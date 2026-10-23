import json
import unittest
from types import SimpleNamespace

from google.genai import types
from pydantic import BaseModel, ValidationError

from backend.agents import MODEL, _gemini_schema, format_json
from backend.models import (
    Backlog,
    BacklogTask,
    ClassifiedTask,
    Priority,
    ProjectContext,
    ScrumPlan,
    Sprint,
    StrictModel,
    UserStory,
    UserStoryCollection,
)
from backend.orchestrator import ProjectOrchestrator


class _FakeModels:
    def __init__(self, outputs: list[object]) -> None:
        self.outputs = iter(outputs)
        self.models: list[str] = []
        self.schemas: list[dict[str, object]] = []

    def generate_content(
        self, *, model: str, contents: str, config: types.GenerateContentConfig
    ) -> object:
        self.models.append(model)
        result = next(self.outputs)
        schema = config.response_schema
        if not isinstance(schema, dict) or not isinstance(result, BaseModel):
            raise AssertionError(f"Unexpected output for {schema}")
        self.schemas.append(schema)
        return SimpleNamespace(text=result.model_dump_json())


class _FakeAgent:
    def __init__(self, result: object) -> None:
        self.result = result
        self.received_contexts: list[ProjectContext] = []

    def run(self, client: object, context: ProjectContext, *args: object) -> object:
        self.received_contexts.append(context)
        return self.result


class AgentWorkflowTests(unittest.TestCase):
    def test_agents_exchange_structured_data_and_emit_json(self) -> None:
        context = ProjectContext(
            title="Application de gestion",
            description="Application de gestion de projets.",
            confirmed_information=["Application de gestion"],
            goals=["Organiser un projet"],
            key_features=["Créer un projet"],
            target_users=["Chef de projet"],
            technical_constraints=[],
            team_size=3,
            budget=None,
            deadline=None,
            assumptions=[],
            unknowns=["Budget", "Échéance"],
        )
        stories = UserStoryCollection(
            user_stories=[
                UserStory(
                    id="US-1",
                    title="Créer un projet",
                    description="En tant que chef de projet, je souhaite créer un projet.",
                    acceptance_criteria=["Le projet est enregistré."],
                    source_requirements=["Créer un projet"],
                )
            ]
        )
        backlog = Backlog(
            tasks=[
                BacklogTask(
                    id="TASK-1",
                    story_id="US-1",
                    title="Créer un projet",
                    description="Enregistrer le projet.",
                    task_type="functional",
                    dependencies=[],
                )
            ]
        )
        plan = ScrumPlan(
            project_title=context.title,
            team_size=3,
            capacity_assumptions=["Capacité à confirmer avec l'équipe."],
            tasks=[
                ClassifiedTask(
                    task_id="TASK-1",
                    priority=Priority.HIGH,
                    priority_reason="Permet de commencer le projet.",
                    estimate_story_points=2,
                    dependencies=[],
                    sprint_number=1,
                )
            ],
            sprints=[
                Sprint(
                    number=1,
                    goal="Créer un projet.",
                    task_ids=["TASK-1"],
                    total_story_points=2,
                )
            ],
        )
        models = _FakeModels([context, stories, backlog, plan])
        client = SimpleNamespace(models=models)

        result = ProjectOrchestrator().run(client, context.title)
        output = json.loads(format_json(result))

        self.assertEqual(models.models, [MODEL] * 4)
        self.assertEqual(len(models.schemas), 4)
        for schema in models.schemas:
            self.assertNotIn("additionalProperties", json.dumps(schema))
        self.assertEqual(output["project_title"], context.title)
        self.assertEqual(output["tasks"][0]["task_id"], "TASK-1")
        self.assertEqual(output["sprints"][0]["task_ids"], ["TASK-1"])

    def test_gemini_schema_removes_unsupported_additional_properties(self) -> None:
        schema = _gemini_schema(ProjectContext)

        self.assertNotIn("additionalProperties", json.dumps(schema))

    def test_pydantic_still_rejects_extra_fields(self) -> None:
        with self.assertRaises(ValidationError):
            ProjectContext.model_validate(
                {
                    "title": "Projet",
                    "description": "Description",
                    "confirmed_information": [],
                    "goals": [],
                    "key_features": [],
                    "target_users": [],
                    "technical_constraints": [],
                    "team_size": None,
                    "budget": None,
                    "deadline": None,
                    "assumptions": [],
                    "unknowns": [],
                    "unexpected": "value",
                }
            )

    def test_user_title_is_preserved_when_product_owner_rephrases_it(self) -> None:
        entered_title = "je veux faire un jeu de dame en ligne de commande"
        context = ProjectContext(
            title="Jeu de dames en ligne de commande",
            description="Un jeu de dames jouable en ligne de commande.",
            confirmed_information=["Le projet concerne un jeu de dames."],
            goals=["Jouer aux dames dans un terminal."],
            key_features=["Partie de dames en ligne de commande."],
            target_users=["Joueur"],
            technical_constraints=["Interface en ligne de commande."],
            team_size=None,
            budget=None,
            deadline=None,
            assumptions=[],
            unknowns=[],
        )
        stories = UserStoryCollection(
            user_stories=[
                UserStory(
                    id="US-1",
                    title="Jouer une partie",
                    description="En tant que joueur, je veux jouer aux dames.",
                    acceptance_criteria=["Une partie peut être commencée."],
                    source_requirements=["Jouer aux dames dans un terminal."],
                )
            ]
        )
        backlog = Backlog(
            tasks=[
                BacklogTask(
                    id="TASK-1",
                    story_id="US-1",
                    title="Démarrer une partie",
                    description="Initialiser une partie de dames.",
                    task_type="functional",
                    dependencies=[],
                )
            ]
        )
        plan = ScrumPlan(
            project_title=entered_title,
            team_size=None,
            capacity_assumptions=[],
            tasks=[
                ClassifiedTask(
                    task_id="TASK-1",
                    priority=Priority.HIGH,
                    priority_reason="Fonctionnalité centrale.",
                    estimate_story_points=2,
                    dependencies=[],
                    sprint_number=None,
                )
            ],
            sprints=[],
        )
        story_agent = _FakeAgent(stories)
        backlog_agent = _FakeAgent(backlog)
        scrum_agent = _FakeAgent(plan)
        orchestrator = ProjectOrchestrator(
            product_owner=SimpleNamespace(run=lambda client, title: context),
            story_agent=story_agent,
            backlog_agent=backlog_agent,
            scrum_agent=scrum_agent,
        )

        result = orchestrator.run(SimpleNamespace(), entered_title)

        self.assertEqual(result.project_title, entered_title)
        self.assertEqual(story_agent.received_contexts[0].title, entered_title)
        self.assertIn(
            entered_title,
            story_agent.received_contexts[0].confirmed_information,
        )


if __name__ == "__main__":
    unittest.main()
