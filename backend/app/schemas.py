from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectStatus(StrEnum):
    DRAFT = "draft"
    CLARIFYING = "clarifying"
    READY = "ready"
    GENERATED = "generated"
    STALE = "stale"


class TaskStatus(StrEnum):
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"


class Priority(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class QuestionType(StrEnum):
    TEXT = "text"
    SINGLE_CHOICE = "single_choice"


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    description: str = Field(min_length=10, max_length=10_000)


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=8, max_length=200)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=1, max_length=200)


class AuthUser(BaseModel):
    id: UUID
    name: str
    email: str


class AuthResponse(BaseModel):
    token: str
    user: AuthUser


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = Field(default=None, min_length=10, max_length=10_000)


class ProjectContext(BaseModel):
    """Contract emitted by the Product Owner and consumed by every later agent."""

    product_summary: str = Field(default="")
    business_objectives: list[str] = Field(default_factory=list)
    primary_features: list[str] = Field(default_factory=list)
    target_users: list[str] = Field(default_factory=list)
    technical_constraints: list[str] = Field(default_factory=list)
    organisational_constraints: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    unknown_information: list[str] = Field(default_factory=list)
    developer_count: int | None = Field(default=None, ge=1)
    budget: str | None = Field(default=None)
    delivery_deadline: str | None = Field(default=None)


class ClarifyingQuestion(BaseModel):
    id: str = Field(description="Stable question key, for example developer_count")
    question: str
    field_key: str
    question_type: QuestionType
    choices: list[str] = Field(default_factory=list)
    why_it_matters: str

    @field_validator("choices")
    @classmethod
    def choices_only_for_choice_question(cls, choices: list[str], info: Any) -> list[str]:
        if info.data.get("question_type") == QuestionType.SINGLE_CHOICE and len(choices) < 2:
            raise ValueError("A single-choice question needs at least two choices.")
        return choices


class ProductOwnerResult(BaseModel):
    context: ProjectContext
    next_question: ClarifyingQuestion | None = None
    ready_for_planning: bool
    message: str


class ClarificationAnswer(BaseModel):
    question_id: str = Field(min_length=1, max_length=100)
    answer: str = Field(min_length=1, max_length=2_000)


class ClarificationResponse(BaseModel):
    project: "ProjectRead"
    question: ClarifyingQuestion | None
    message: str


class AcceptanceCriterion(BaseModel):
    description: str


class UserStoryDraft(BaseModel):
    key: str = Field(description="Short unique key within this generation, e.g. user_authentication")
    title: str
    role: str
    goal: str
    benefit: str
    source_need: str
    acceptance_criteria: list[AcceptanceCriterion] = Field(min_length=1)


class UserStoriesResult(BaseModel):
    stories: list[UserStoryDraft] = Field(min_length=1)
    inconsistencies: list[str] = Field(default_factory=list)


class BacklogTaskDraft(BaseModel):
    key: str = Field(description="Unique task key within this generation")
    title: str
    description: str
    story_key: str
    task_type: str = Field(description="functional, technical, quality, or research")
    depends_on_keys: list[str] = Field(default_factory=list)


class BacklogResult(BaseModel):
    tasks: list[BacklogTaskDraft] = Field(min_length=1)
    dependency_notes: list[str] = Field(default_factory=list)


class ScrumTaskAssessment(BaseModel):
    task_key: str
    priority: Priority
    priority_reason: str
    estimate_points: int = Field(ge=1, le=21)
    sprint_number: int | None = Field(default=None, ge=1)


class SprintProposal(BaseModel):
    number: int = Field(ge=1)
    goal: str
    capacity_points: int = Field(ge=1)
    task_keys: list[str] = Field(default_factory=list)
    rationale: str


class ScrumResult(BaseModel):
    assessments: list[ScrumTaskAssessment] = Field(min_length=1)
    sprints: list[SprintProposal] = Field(default_factory=list)
    planning_assumptions: list[str] = Field(default_factory=list)


class UserStoryRead(ORMModel):
    id: UUID
    title: str
    role: str
    goal: str
    benefit: str
    source_need: str
    acceptance_criteria: list[AcceptanceCriterion]
    revision: int
    is_manual: bool


class BacklogTaskRead(ORMModel):
    id: UUID
    title: str
    description: str
    story_id: UUID | None
    task_type: str
    priority: Priority
    priority_reason: str
    estimate_points: int | None
    dependency_ids: list[UUID]
    status: TaskStatus
    sprint_number: int | None
    position: int
    revision: int
    is_manual: bool


class SprintRead(ORMModel):
    id: UUID
    number: int
    goal: str
    capacity_points: int | None
    rationale: str
    assumptions: list[str]
    revision: int


class ProjectRead(ORMModel):
    id: UUID
    name: str
    description: str
    status: ProjectStatus
    revision: int
    context: ProjectContext | None
    created_at: datetime
    updated_at: datetime


class ProjectDetail(ProjectRead):
    user_stories: list[UserStoryRead]
    tasks: list[BacklogTaskRead]
    sprints: list[SprintRead]


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=250)
    description: str | None = Field(default=None, min_length=2, max_length=4_000)
    priority: Priority | None = None
    status: TaskStatus | None = None
    estimate_points: int | None = Field(default=None, ge=1, le=21)
    sprint_number: int | None = Field(default=None, ge=1)
    position: int | None = Field(default=None, ge=0)
    dependency_ids: list[UUID] | None = None


class GenerationResponse(BaseModel):
    project: ProjectDetail
    warnings: list[str] = Field(default_factory=list)


class APIError(BaseModel):
    detail: str


# Resolve the forward reference used by ClarificationResponse during OpenAPI generation.
ClarificationResponse.model_rebuild()
