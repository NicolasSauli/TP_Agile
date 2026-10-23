from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def new_uuid() -> UUID:
    return uuid4()


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=new_uuid)
    owner_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    revision: Mapped[int] = mapped_column(Integer, default=1)
    context_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    answers_json: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    stories: Mapped[list[UserStory]] = relationship(back_populates="project", cascade="all, delete-orphan")
    tasks: Mapped[list[BacklogTask]] = relationship(back_populates="project", cascade="all, delete-orphan")
    sprints: Mapped[list[Sprint]] = relationship(back_populates="project", cascade="all, delete-orphan")
    agent_runs: Mapped[list[AgentRun]] = relationship(back_populates="project", cascade="all, delete-orphan")
    owner: Mapped[User | None] = relationship(back_populates="projects")


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    projects: Mapped[list[Project]] = relationship(back_populates="owner")


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=new_uuid)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserStory(Base):
    __tablename__ = "user_stories"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=new_uuid)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    title: Mapped[str] = mapped_column(String(250))
    role: Mapped[str] = mapped_column(String(250))
    goal: Mapped[str] = mapped_column(Text)
    benefit: Mapped[str] = mapped_column(Text)
    source_need: Mapped[str] = mapped_column(Text)
    acceptance_criteria_json: Mapped[list[dict[str, str]]] = mapped_column(JSON, default=list)
    generation_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    revision: Mapped[int] = mapped_column(Integer)
    is_manual: Mapped[bool] = mapped_column(default=False)

    project: Mapped[Project] = relationship(back_populates="stories")
    tasks: Mapped[list[BacklogTask]] = relationship(back_populates="story")


class BacklogTask(Base):
    __tablename__ = "backlog_tasks"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=new_uuid)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    story_id: Mapped[UUID | None] = mapped_column(ForeignKey("user_stories.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(250))
    description: Mapped[str] = mapped_column(Text)
    task_type: Mapped[str] = mapped_column(String(50))
    generation_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    priority_reason: Mapped[str] = mapped_column(Text, default="Not yet assessed")
    estimate_points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dependency_ids_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), default="backlog")
    sprint_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    revision: Mapped[int] = mapped_column(Integer)
    is_manual: Mapped[bool] = mapped_column(default=False)

    project: Mapped[Project] = relationship(back_populates="tasks")
    story: Mapped[UserStory | None] = relationship(back_populates="tasks")


class Sprint(Base):
    __tablename__ = "sprints"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=new_uuid)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    number: Mapped[int] = mapped_column(Integer)
    goal: Mapped[str] = mapped_column(Text)
    capacity_points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rationale: Mapped[str] = mapped_column(Text)
    assumptions_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    revision: Mapped[int] = mapped_column(Integer)

    project: Mapped[Project] = relationship(back_populates="sprints")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=new_uuid)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    agent_name: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(20), default="running")
    input_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    output_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped[Project] = relationship(back_populates="agent_runs")
