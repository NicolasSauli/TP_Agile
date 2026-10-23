from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Generic, TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import BACKEND_DIRECTORY, Settings
from app.models import AgentRun, Project
from app.schemas import BacklogResult, ProductOwnerResult, ScrumResult, UserStoriesResult


class AgentName(StrEnum):
    PRODUCT_OWNER = "product_owner"
    USER_STORIES = "user_stories"
    BACKLOG = "backlog"
    SCRUM = "scrum"


class AgentUnavailableError(RuntimeError):
    """Raised when generation was requested before the API key was configured."""


class AgentExecutionError(RuntimeError):
    """Raised when an external model call cannot return a valid typed result."""


OutputModel = TypeVar("OutputModel", bound=BaseModel)
PROMPTS_DIRECTORY = BACKEND_DIRECTORY / "prompts"


class StructuredAgent(Generic[OutputModel]):
    """A small, typed agent wrapping Gemini structured outputs.

    The output class is the single contract shared by the model and the rest of
    the backend.
    """

    def __init__(self, name: AgentName, prompt_filename: str, output_type: type[OutputModel], settings: Settings):
        self.name = name
        self.prompt_filename = prompt_filename
        self.output_type = output_type
        self.settings = settings

    @property
    def prompt(self) -> str:
        prompt_path = PROMPTS_DIRECTORY / self.prompt_filename
        try:
            return prompt_path.read_text(encoding="utf-8").strip()
        except FileNotFoundError as exc:
            raise AgentExecutionError(f"Prompt file is missing: {prompt_path.name}") from exc

    def run(self, payload: dict[str, object]) -> OutputModel:
        if not self.settings.gemini_api_key:
            raise AgentUnavailableError(
                "GEMINI_API_KEY is not configured. Add it to backend/.env before using AI generation."
            )

        try:
            client = genai.Client(api_key=self.settings.gemini_api_key)
            response = client.models.generate_content(
                model=self.settings.agent_model,
                contents=f"{self.prompt}\n\nDonnées du projet :\n{payload}",
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=self.output_type,
                ),
            )
        except Exception as exc:  # SDK exceptions are intentionally translated at the service boundary.
            if "quota" in str(exc).lower() or "resource exhausted" in str(exc).lower():
                raise AgentExecutionError(
                    f"{self.name.value} agent indisponible : le quota Gemini est épuisé."
                ) from exc
            raise AgentExecutionError(f"{self.name.value} agent failed: {exc}") from exc

        if response.parsed is not None:
            return response.parsed
        if not response.text:
            raise AgentExecutionError(f"{self.name.value} agent returned no structured result.")
        try:
            return self.output_type.model_validate_json(response.text)
        except ValueError as exc:
            raise AgentExecutionError(f"{self.name.value} agent returned invalid structured data.") from exc


class AgentSuite:
    """Owns the specialized agents and persists an auditable execution trace."""

    def __init__(self, settings: Settings):
        self.product_owner = StructuredAgent(
            AgentName.PRODUCT_OWNER,
            "agent_product_owner_prompt.txt",
            ProductOwnerResult,
            settings,
        )
        self.user_stories = StructuredAgent(
            AgentName.USER_STORIES,
            "agent_user_stories_prompt.txt",
            UserStoriesResult,
            settings,
        )
        self.backlog = StructuredAgent(
            AgentName.BACKLOG,
            "agent_backlog_prompt.txt",
            BacklogResult,
            settings,
        )
        self.scrum = StructuredAgent(
            AgentName.SCRUM,
            "agent_scrum_prompt.txt",
            ScrumResult,
            settings,
        )

    def execute(
        self,
        db: Session,
        project: Project,
        agent: StructuredAgent[OutputModel],
        payload: dict[str, object],
    ) -> OutputModel:
        run = AgentRun(
            project_id=project.id,
            agent_name=agent.name.value,
            status="running",
            input_json=payload,
        )
        db.add(run)
        db.flush()
        try:
            result = agent.run(payload)
        except (AgentUnavailableError, AgentExecutionError) as exc:
            run.status = "failed"
            run.error = str(exc)
            db.commit()
            raise

        run.status = "completed"
        run.output_json = result.model_dump(mode="json")
        db.commit()
        return result
