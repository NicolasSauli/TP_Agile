import json
from typing import Any, TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel

from backend.models import Backlog, ProjectContext, ScrumPlan, UserStoryCollection

MODEL = "gemini-3.5-flash-lite"
ResponseModel = TypeVar("ResponseModel", bound=BaseModel)


def _gemini_schema(response_model: type[BaseModel]) -> dict[str, Any]:
    schema = response_model.model_json_schema()

    def remove_unsupported_properties(value: Any) -> None:
        if isinstance(value, dict):
            value.pop("additionalProperties", None)
            for nested_value in value.values():
                remove_unsupported_properties(nested_value)
        elif isinstance(value, list):
            for nested_value in value:
                remove_unsupported_properties(nested_value)

    remove_unsupported_properties(schema)
    return schema


def _ask_agent(
    client: genai.Client,
    *,
    name: str,
    instructions: str,
    payload: BaseModel,
    response_model: type[ResponseModel],
) -> ResponseModel:
    response = client.models.generate_content(
        model=MODEL,
        contents=(
            f"{instructions}\n\nDonnées d'entrée (JSON) :\n{payload.model_dump_json()}"
        ),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=_gemini_schema(response_model),
        ),
    )
    if response.text is None:
        raise RuntimeError(f"L'agent {name} n'a pas produit de réponse structurée.")
    return response_model.model_validate_json(response.text)


class ProductOwnerAgent:
    def run(self, client: genai.Client, title: str) -> ProjectContext:
        return _ask_agent(
            client,
            name="Product Owner",
            instructions=(
                "Tu es Product Owner. À partir du seul intitulé fourni, produis une synthèse "
                "prudente en français. Ne présente aucune déduction comme un fait confirmé. "
                "Quand une information n'est pas connue, utilise null pour les champs optionnels "
                "et ajoute-la à unknowns. Les objectifs, fonctionnalités et utilisateurs non "
                "explicites doivent être présentés comme hypothèses, jamais inventés. "
                "Renseigne confirmed_information avec uniquement les faits explicitement fournis."
            ),
            payload=_TitleInput(title=title),
            response_model=ProjectContext,
        )


class UserStoryAgent:
    def run(self, client: genai.Client, context: ProjectContext) -> UserStoryCollection:
        return _ask_agent(
            client,
            name="User Stories",
            instructions=(
                "Tu es un agent de génération de User Stories. Réponds en français. "
                "Ne transforme pas les hypothèses en faits, reste dans le périmètre du contexte "
                "et génère des critères d'acceptation vérifiables."
            ),
            payload=context,
            response_model=UserStoryCollection,
        )


class BacklogAgent:
    def run(
        self, client: genai.Client, context: ProjectContext, stories: UserStoryCollection
    ) -> Backlog:
        return _ask_agent(
            client,
            name="Backlog",
            instructions=(
                "Tu es un agent de génération du backlog. Décompose chaque User Story en tâches "
                "fonctionnelles ou techniques utiles, sans micro-tâches artificielles. Réponds en "
                "français, conserve les identifiants de User Stories et indique uniquement des "
                "dépendances entre tâches du backlog."
            ),
            payload=_AgentInput(project=context, user_stories=stories),
            response_model=Backlog,
        )


class ScrumClassificationAgent:
    def run(
        self, client: genai.Client, context: ProjectContext, backlog: Backlog
    ) -> ScrumPlan:
        return _ask_agent(
            client,
            name="Scrum",
            instructions=(
                "Tu es l'agent Scrum chargé de classer et planifier le backlog. Réponds en "
                "français. Priorise selon la valeur métier, l'importance, les dépendances et "
                "l'échéance. Estime en points de complexité, justifie chaque priorité, respecte "
                "l'ordre des dépendances et répartis les tâches en sprints si c'est défendable. "
                "Le nombre de développeurs seul ne donne pas une capacité précise : indique "
                "clairement toute hypothèse de capacité. Ne planifie pas une tâche dont les "
                "prérequis ne sont pas résolus; laisse son sprint à null si nécessaire. Reprends "
                "exactement les identifiants et dépendances du backlog. Le résultat doit inclure "
                "chaque tâche une seule fois."
            ),
            payload=_AgentInput(project=context, backlog=backlog),
            response_model=ScrumPlan,
        )


class _TitleInput(BaseModel):
    title: str


class _AgentInput(BaseModel):
    project: ProjectContext
    user_stories: UserStoryCollection | None = None
    backlog: Backlog | None = None


def format_json(plan: ScrumPlan) -> str:
    return json.dumps(plan.model_dump(mode="json"), ensure_ascii=False, indent=2)
