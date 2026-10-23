import unittest

from backend.models import (
    Backlog,
    BacklogTask,
    ClassifiedTask,
    Priority,
    ProjectContext,
    ScrumPlan,
    Sprint,
    UserStory,
    UserStoryCollection,
)
from backend.orchestrator import validate_backlog, validate_scrum_plan


class OrchestratorValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.context = ProjectContext(
            title="Application de gestion",
            description="Application à définir.",
            confirmed_information=["Application de gestion"],
            goals=[],
            key_features=[],
            target_users=[],
            technical_constraints=[],
            team_size=None,
            budget=None,
            deadline=None,
            assumptions=[],
            unknowns=[],
        )
        self.stories = UserStoryCollection(
            user_stories=[
                UserStory(
                    id="US-1",
                    title="Créer un projet",
                    description="En tant qu'utilisateur, je souhaite créer un projet.",
                    acceptance_criteria=["Le projet est créé."],
                    source_requirements=["Créer un projet"],
                )
            ]
        )
        self.backlog = Backlog(
            tasks=[
                BacklogTask(
                    id="TASK-1",
                    story_id="US-1",
                    title="Créer le projet",
                    description="Implémenter la création.",
                    task_type="functional",
                    dependencies=[],
                ),
                BacklogTask(
                    id="TASK-2",
                    story_id="US-1",
                    title="Tester la création",
                    description="Ajouter les tests.",
                    task_type="technical",
                    dependencies=["TASK-1"],
                ),
            ]
        )

    def test_validates_inter_agent_references(self) -> None:
        validate_backlog(self.context, self.stories, self.backlog)

    def test_rejects_unknown_task_dependency(self) -> None:
        self.backlog.tasks[1].dependencies = ["TASK-UNKNOWN"]
        with self.assertRaisesRegex(ValueError, "dépendances inconnues"):
            validate_backlog(self.context, self.stories, self.backlog)

    def test_rejects_sprint_before_dependency(self) -> None:
        plan = ScrumPlan(
            project_title=self.context.title,
            team_size=None,
            capacity_assumptions=[],
            tasks=[
                ClassifiedTask(
                    task_id="TASK-1",
                    priority=Priority.HIGH,
                    priority_reason="Prérequis.",
                    estimate_story_points=2,
                    dependencies=[],
                    sprint_number=2,
                ),
                ClassifiedTask(
                    task_id="TASK-2",
                    priority=Priority.MEDIUM,
                    priority_reason="Dépend du développement.",
                    estimate_story_points=1,
                    dependencies=["TASK-1"],
                    sprint_number=1,
                ),
            ],
            sprints=[
                Sprint(number=1, goal="Tests", task_ids=["TASK-2"], total_story_points=1),
                Sprint(number=2, goal="Développement", task_ids=["TASK-1"], total_story_points=2),
            ],
        )
        with self.assertRaisesRegex(ValueError, "avant sa dépendance"):
            validate_scrum_plan(self.backlog, plan)

    def test_rejects_missing_scrum_classification(self) -> None:
        plan = ScrumPlan(
            project_title=self.context.title,
            team_size=None,
            capacity_assumptions=[],
            tasks=[
                ClassifiedTask(
                    task_id="TASK-1",
                    priority=Priority.HIGH,
                    priority_reason="Prioritaire.",
                    estimate_story_points=2,
                    dependencies=[],
                    sprint_number=1,
                )
            ],
            sprints=[Sprint(number=1, goal="Développement", task_ids=["TASK-1"], total_story_points=2)],
        )
        with self.assertRaisesRegex(ValueError, "ne correspond pas au backlog"):
            validate_scrum_plan(self.backlog, plan)


if __name__ == "__main__":
    unittest.main()
