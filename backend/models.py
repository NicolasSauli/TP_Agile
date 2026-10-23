from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProjectContext(StrictModel):
    title: str = Field(description="Project title provided by the user.")
    description: str = Field(description="Short description of the project.")
    confirmed_information: list[str] = Field(
        description="Facts explicitly provided by the user, including the project title."
    )
    goals: list[str] = Field(description="Project goals supported by the given context.")
    key_features: list[str] = Field(description="Main features supported by the given context.")
    target_users: list[str] = Field(description="Known or explicitly hypothesized target users.")
    technical_constraints: list[str] = Field(description="Technical constraints stated by the user.")
    team_size: int | None = Field(
        ge=1, description="Number of developers, or null if unknown."
    )
    budget: str | None = Field(description="Budget, or null if unknown.")
    deadline: str | None = Field(description="Delivery deadline, or null if unknown.")
    assumptions: list[str] = Field(description="Explicit hypotheses, never presented as confirmed facts.")
    unknowns: list[str] = Field(description="Important information not provided by the user.")


class UserStory(StrictModel):
    id: str = Field(description="Stable unique identifier, for example US-1.")
    title: str
    description: str = Field(description="User story in the 'As a... I want... so that...' format.")
    acceptance_criteria: list[str]
    source_requirements: list[str] = Field(description="Requirements from the project context.")


class UserStoryCollection(StrictModel):
    user_stories: list[UserStory]


class BacklogTask(StrictModel):
    id: str = Field(description="Stable unique identifier, for example TASK-1.")
    story_id: str = Field(description="ID of the related user story.")
    title: str
    description: str
    task_type: Literal["functional", "technical"]
    dependencies: list[str] = Field(description="IDs of prerequisite backlog tasks.")


class Backlog(StrictModel):
    tasks: list[BacklogTask]


class Priority(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ClassifiedTask(StrictModel):
    task_id: str
    priority: Priority
    priority_reason: str
    estimate_story_points: int = Field(ge=1)
    dependencies: list[str]
    sprint_number: int | None = Field(description="Proposed sprint number, or null if not schedulable.")


class Sprint(StrictModel):
    number: int = Field(ge=1)
    goal: str
    task_ids: list[str]
    total_story_points: int = Field(ge=0)


class ScrumPlan(StrictModel):
    project_title: str
    team_size: int | None
    capacity_assumptions: list[str] = Field(
        description="Explicit assumptions; do not claim exact team capacity from headcount alone."
    )
    tasks: list[ClassifiedTask] = Field(description="Tasks ordered by priority and dependencies.")
    sprints: list[Sprint]
