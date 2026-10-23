from __future__ import annotations

from typing import Iterable
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models import BacklogTask, Project, Sprint, UserStory
from app.schemas import (
    AcceptanceCriterion,
    BacklogTaskRead,
    Priority,
    ProjectContext,
    ProjectDetail,
    ProjectRead,
    ProjectStatus,
    SprintRead,
    TaskStatus,
    UserStoryRead,
)


class NotFoundError(LookupError):
    pass


def get_project_or_404(db: Session, project_id: UUID) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise NotFoundError(f"Project {project_id} was not found.")
    return project


def project_read(project: Project) -> ProjectRead:
    return ProjectRead(
        id=project.id,
        name=project.name,
        description=project.description,
        status=ProjectStatus(project.status),
        revision=project.revision,
        context=ProjectContext.model_validate(project.context_json) if project.context_json else None,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def story_read(story: UserStory) -> UserStoryRead:
    return UserStoryRead(
        id=story.id,
        title=story.title,
        role=story.role,
        goal=story.goal,
        benefit=story.benefit,
        source_need=story.source_need,
        acceptance_criteria=[AcceptanceCriterion.model_validate(item) for item in story.acceptance_criteria_json],
        revision=story.revision,
        is_manual=story.is_manual,
    )


def task_read(task: BacklogTask) -> BacklogTaskRead:
    return BacklogTaskRead(
        id=task.id,
        title=task.title,
        description=task.description,
        story_id=task.story_id,
        task_type=task.task_type,
        priority=Priority(task.priority),
        priority_reason=task.priority_reason,
        estimate_points=task.estimate_points,
        dependency_ids=[UUID(dependency_id) for dependency_id in task.dependency_ids_json],
        status=TaskStatus(task.status),
        sprint_number=task.sprint_number,
        position=task.position,
        revision=task.revision,
        is_manual=task.is_manual,
    )


def sprint_read(sprint: Sprint) -> SprintRead:
    return SprintRead(
        id=sprint.id,
        number=sprint.number,
        goal=sprint.goal,
        capacity_points=sprint.capacity_points,
        rationale=sprint.rationale,
        assumptions=sprint.assumptions_json,
        revision=sprint.revision,
    )


def project_detail(db: Session, project: Project) -> ProjectDetail:
    stories = list(
        db.scalars(select(UserStory).where(UserStory.project_id == project.id).order_by(UserStory.title)).all()
    )
    tasks = list(db.scalars(select(BacklogTask).where(BacklogTask.project_id == project.id)).all())
    priority_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    tasks.sort(key=lambda task: (task.position, priority_rank.get(task.priority, 9), task.title.lower()))
    sprints = list(
        db.scalars(select(Sprint).where(Sprint.project_id == project.id).order_by(Sprint.number)).all()
    )
    return ProjectDetail(
        **project_read(project).model_dump(),
        user_stories=[story_read(story) for story in stories],
        tasks=[task_read(task) for task in tasks],
        sprints=[sprint_read(sprint) for sprint in sprints],
    )


def delete_non_manual_plan(db: Session, project: Project) -> None:
    """Clear only AI-owned plan data; manually modified tasks always survive reruns."""

    protected_story_ids = set(
        db.scalars(
            select(BacklogTask.story_id).where(
                BacklogTask.project_id == project.id,
                BacklogTask.is_manual.is_(True),
                BacklogTask.story_id.is_not(None),
            )
        ).all()
    )
    db.execute(
        delete(BacklogTask).where(
            BacklogTask.project_id == project.id,
            BacklogTask.is_manual.is_(False),
        )
    )
    stories_to_remove = db.scalars(
        select(UserStory).where(
            UserStory.project_id == project.id,
            UserStory.is_manual.is_(False),
        )
    ).all()
    for story in stories_to_remove:
        if story.id not in protected_story_ids:
            db.delete(story)
    db.execute(delete(Sprint).where(Sprint.project_id == project.id))
    db.flush()


def validate_dependencies(project_id: UUID, dependency_ids: Iterable[UUID], task_id: UUID | None, db: Session) -> None:
    dependency_ids = list(dependency_ids)
    if task_id and task_id in dependency_ids:
        raise ValueError("A task cannot depend on itself.")
    if not dependency_ids:
        return
    count = db.scalar(
        select(func.count())
        .select_from(BacklogTask)
        .where(
            BacklogTask.project_id == project_id,
            BacklogTask.id.in_(dependency_ids),
        )
    )
    if count != len(set(dependency_ids)):
        raise ValueError("Every dependency must belong to the same project.")
