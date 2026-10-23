from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import BacklogTask, Project, Sprint, UserStory
from app.schemas import (
    BacklogResult,
    ClarificationAnswer,
    ClarifyingQuestion,
    GenerationResponse,
    ProductOwnerResult,
    ProjectContext,
    ProjectStatus,
    ScrumResult,
    UserStoriesResult,
)
from app.services.agents import AgentSuite
from app.services.repository import delete_non_manual_plan, project_detail


class ClarificationRequiredError(RuntimeError):
    def __init__(self, question: ClarifyingQuestion | None, message: str):
        super().__init__(message)
        self.question = question


@dataclass
class PlanningArtifacts:
    product_owner: ProductOwnerResult
    stories: UserStoriesResult
    backlog: BacklogResult
    scrum: ScrumResult


class ProjectOrchestrator:
    """Coordinates specialized agents; database rules remain outside the LLM."""

    def __init__(self, agents: AgentSuite):
        self.agents = agents

    @staticmethod
    def _base_payload(project: Project) -> dict[str, object]:
        return {
            "project": {"id": str(project.id), "name": project.name, "description": project.description},
            "current_context": project.context_json or {},
            "answers": project.answers_json or {},
        }

    def answer_clarification(
        self,
        db: Session,
        project: Project,
        answer: ClarificationAnswer,
    ) -> ProductOwnerResult:
        answers = dict(project.answers_json or {})
        answers[answer.question_id] = answer.answer
        project.answers_json = answers
        payload = self._base_payload(project) | {
            "mode": "clarification",
            "latest_answer": answer.model_dump(),
            "minimum_information": [
                "primary_features",
                "target_users",
                "technical_constraints",
                "developer_count",
                "budget",
                "delivery_deadline",
            ],
        }
        result = self.agents.execute(db, project, self.agents.product_owner, payload)
        project.context_json = result.context.model_dump(mode="json")
        project.status = ProjectStatus.READY.value if result.ready_for_planning else ProjectStatus.CLARIFYING.value
        db.commit()
        db.refresh(project)
        return result

    def start_clarification(self, db: Session, project: Project) -> ProductOwnerResult:
        """Ask the first adaptive question after a project description is saved."""

        payload = self._base_payload(project) | {
            "mode": "clarification",
            "latest_answer": None,
            "minimum_information": [
                "primary_features",
                "target_users",
                "technical_constraints",
                "developer_count",
                "budget",
                "delivery_deadline",
            ],
        }
        result = self.agents.execute(db, project, self.agents.product_owner, payload)
        project.context_json = result.context.model_dump(mode="json")
        project.status = ProjectStatus.READY.value if result.ready_for_planning else ProjectStatus.CLARIFYING.value
        db.commit()
        db.refresh(project)
        return result

    def generate(self, db: Session, project: Project) -> GenerationResponse:
        po_payload = self._base_payload(project) | {
            "mode": "planning_synthesis",
            "minimum_information": [
                "primary_features",
                "target_users",
                "technical_constraints",
                "developer_count",
                "budget",
                "delivery_deadline",
            ],
        }
        product_owner = self.agents.execute(db, project, self.agents.product_owner, po_payload)
        project.context_json = product_owner.context.model_dump(mode="json")
        if not product_owner.ready_for_planning:
            project.status = ProjectStatus.CLARIFYING.value
            db.commit()
            raise ClarificationRequiredError(product_owner.next_question, product_owner.message)

        stories = self.agents.execute(
            db,
            project,
            self.agents.user_stories,
            {
                "project_context": product_owner.context.model_dump(mode="json"),
                "project_description": project.description,
            },
        )
        backlog = self.agents.execute(
            db,
            project,
            self.agents.backlog,
            {
                "project_context": product_owner.context.model_dump(mode="json"),
                "user_stories": stories.model_dump(mode="json"),
                "preservation_rule": "Do not recreate user-managed tasks; they are protected by the backend.",
            },
        )
        scrum = self.agents.execute(
            db,
            project,
            self.agents.scrum,
            {
                "project_context": product_owner.context.model_dump(mode="json"),
                "backlog": backlog.model_dump(mode="json"),
                "planning_rule": "Dependencies are strict ordering constraints. State planning assumptions explicitly.",
            },
        )
        self._persist_plan(db, project, stories, backlog, scrum)
        warnings = list(stories.inconsistencies) + list(backlog.dependency_notes) + list(scrum.planning_assumptions)
        return GenerationResponse(project=project_detail(db, project), warnings=warnings)

    def _persist_plan(
        self,
        db: Session,
        project: Project,
        stories_result: UserStoriesResult,
        backlog_result: BacklogResult,
        scrum_result: ScrumResult,
    ) -> None:
        assessments = {item.task_key: item for item in scrum_result.assessments}
        generated_keys = {task.key for task in backlog_result.tasks}
        missing_assessments = generated_keys - assessments.keys()
        unknown_assessments = assessments.keys() - generated_keys
        if missing_assessments or unknown_assessments:
            raise ValueError(
                "Scrum assessment keys must exactly match backlog task keys "
                f"(missing={sorted(missing_assessments)}, unknown={sorted(unknown_assessments)})."
            )

        story_keys = {story.key for story in stories_result.stories}
        invalid_story_keys = {task.story_key for task in backlog_result.tasks} - story_keys
        if invalid_story_keys:
            raise ValueError(f"Backlog references unknown User Story keys: {sorted(invalid_story_keys)}")
        for task in backlog_result.tasks:
            unknown_dependencies = set(task.depends_on_keys) - generated_keys
            if task.key in task.depends_on_keys or unknown_dependencies:
                raise ValueError(f"Invalid dependencies for task '{task.key}'.")

        delete_non_manual_plan(db, project)
        story_by_key: dict[str, UserStory] = {}
        for draft in stories_result.stories:
            story = UserStory(
                project_id=project.id,
                title=draft.title,
                role=draft.role,
                goal=draft.goal,
                benefit=draft.benefit,
                source_need=draft.source_need,
                acceptance_criteria_json=[criterion.model_dump() for criterion in draft.acceptance_criteria],
                generation_key=draft.key,
                revision=project.revision,
            )
            db.add(story)
            story_by_key[draft.key] = story
        db.flush()

        priority_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        drafts_in_priority_order = sorted(
            backlog_result.tasks,
            key=lambda task: (priority_rank[assessments[task.key].priority.value], task.title.lower()),
        )
        task_by_key: dict[str, BacklogTask] = {}
        for position, draft in enumerate(drafts_in_priority_order):
            assessment = assessments[draft.key]
            task = BacklogTask(
                project_id=project.id,
                story_id=story_by_key[draft.story_key].id,
                title=draft.title,
                description=draft.description,
                task_type=draft.task_type,
                generation_key=draft.key,
                priority=assessment.priority.value,
                priority_reason=assessment.priority_reason,
                estimate_points=assessment.estimate_points,
                status="backlog",
                sprint_number=assessment.sprint_number,
                position=position,
                revision=project.revision,
            )
            db.add(task)
            task_by_key[draft.key] = task
        db.flush()
        for draft in backlog_result.tasks:
            task_by_key[draft.key].dependency_ids_json = [
                str(task_by_key[dependency_key].id) for dependency_key in draft.depends_on_keys
            ]

        for proposal in scrum_result.sprints:
            unknown_sprint_tasks = set(proposal.task_keys) - generated_keys
            if unknown_sprint_tasks:
                raise ValueError(f"Sprint {proposal.number} references unknown task keys.")
            db.add(
                Sprint(
                    project_id=project.id,
                    number=proposal.number,
                    goal=proposal.goal,
                    capacity_points=proposal.capacity_points,
                    rationale=proposal.rationale,
                    assumptions_json=scrum_result.planning_assumptions,
                    revision=project.revision,
                )
            )

        project.status = ProjectStatus.GENERATED.value
        db.commit()
        db.refresh(project)
