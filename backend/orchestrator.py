from google import genai

from backend.agents import (
    BacklogAgent,
    ProductOwnerAgent,
    ScrumClassificationAgent,
    UserStoryAgent,
)
from backend.models import Backlog, ProjectContext, ScrumPlan, UserStoryCollection


def validate_backlog(
    context: ProjectContext, stories: UserStoryCollection, backlog: Backlog
) -> None:
    story_ids = [story.id for story in stories.user_stories]
    if not story_ids:
        raise ValueError("L'agent User Stories n'a généré aucune User Story.")
    if len(story_ids) != len(set(story_ids)):
        raise ValueError("L'agent User Stories a produit des identifiants en double.")

    task_ids = [task.id for task in backlog.tasks]
    if not task_ids:
        raise ValueError("L'agent backlog n'a généré aucune tâche.")
    if len(task_ids) != len(set(task_ids)):
        raise ValueError("L'agent backlog a produit des identifiants de tâches en double.")

    known_stories = set(story_ids)
    known_tasks = set(task_ids)
    for task in backlog.tasks:
        if task.story_id not in known_stories:
            raise ValueError(
                f"La tâche {task.id} référence une User Story inconnue : {task.story_id}."
            )
        if task.id in task.dependencies:
            raise ValueError(f"La tâche {task.id} dépend d'elle-même.")
        missing_dependencies = set(task.dependencies) - known_tasks
        if missing_dependencies:
            raise ValueError(
                f"La tâche {task.id} référence des dépendances inconnues : "
                f"{', '.join(sorted(missing_dependencies))}."
            )


def validate_scrum_plan(backlog: Backlog, plan: ScrumPlan) -> None:
    backlog_ids = {task.id for task in backlog.tasks}
    plan_ids = [task.task_id for task in plan.tasks]
    if len(plan_ids) != len(set(plan_ids)):
        raise ValueError("L'agent Scrum a classé une tâche plusieurs fois.")
    if set(plan_ids) != backlog_ids:
        missing = sorted(backlog_ids - set(plan_ids))
        extra = sorted(set(plan_ids) - backlog_ids)
        raise ValueError(
            f"Le plan Scrum ne correspond pas au backlog (manquantes : {missing}; "
            f"inconnues : {extra})."
        )

    task_by_id = {task.id: task for task in backlog.tasks}
    classified_by_id = {task.task_id: task for task in plan.tasks}
    task_positions = {task.task_id: index for index, task in enumerate(plan.tasks)}
    for task_id, classification in classified_by_id.items():
        expected = set(task_by_id[task_id].dependencies)
        if set(classification.dependencies) != expected:
            raise ValueError(
                f"Les dépendances de la tâche {task_id} ont été modifiées par l'agent Scrum."
            )
        for dependency_id in expected:
            if task_positions[dependency_id] > task_positions[task_id]:
                raise ValueError(
                    f"La tâche {task_id} apparaît avant sa dépendance {dependency_id}."
                )
            dependency_sprint = classified_by_id[dependency_id].sprint_number
            task_sprint = classification.sprint_number
            if task_sprint is not None and (
                dependency_sprint is None or dependency_sprint > task_sprint
            ):
                raise ValueError(
                    f"La tâche {task_id} est planifiée avant sa dépendance {dependency_id}."
                )

    sprint_task_ids = [task_id for sprint in plan.sprints for task_id in sprint.task_ids]
    if len(sprint_task_ids) != len(set(sprint_task_ids)):
        raise ValueError("Une tâche apparaît plusieurs fois dans les sprints.")
    scheduled_task_ids = {
        task.task_id for task in plan.tasks if task.sprint_number is not None
    }
    if set(sprint_task_ids) != scheduled_task_ids:
        raise ValueError("Les sprints ne correspondent pas aux tâches planifiées.")
    sprint_numbers = [sprint.number for sprint in plan.sprints]
    if len(sprint_numbers) != len(set(sprint_numbers)):
        raise ValueError("L'agent Scrum a produit des numéros de sprint en double.")
    for sprint in plan.sprints:
        if any(task_id not in backlog_ids for task_id in sprint.task_ids):
            raise ValueError(f"Le sprint {sprint.number} référence une tâche inconnue.")
        if any(
            classified_by_id[task_id].sprint_number != sprint.number
            for task_id in sprint.task_ids
        ):
            raise ValueError(
                f"Les tâches du sprint {sprint.number} ne correspondent pas aux classifications."
            )
        expected_points = sum(
            classified_by_id[task_id].estimate_story_points for task_id in sprint.task_ids
        )
        if sprint.total_story_points != expected_points:
            raise ValueError(
                f"La charge totale du sprint {sprint.number} ne correspond pas aux estimations."
            )


class ProjectOrchestrator:
    def __init__(
        self,
        product_owner: ProductOwnerAgent | None = None,
        story_agent: UserStoryAgent | None = None,
        backlog_agent: BacklogAgent | None = None,
        scrum_agent: ScrumClassificationAgent | None = None,
    ) -> None:
        self.product_owner = product_owner or ProductOwnerAgent()
        self.story_agent = story_agent or UserStoryAgent()
        self.backlog_agent = backlog_agent or BacklogAgent()
        self.scrum_agent = scrum_agent or ScrumClassificationAgent()

    def run(self, client: genai.Client, title: str) -> ScrumPlan:
        context = self.product_owner.run(client, title)
        if context.title != title:
            confirmed_information = list(context.confirmed_information)
            if title not in confirmed_information:
                confirmed_information.append(title)
            context = context.model_copy(
                update={
                    "title": title,
                    "confirmed_information": confirmed_information,
                }
            )

        stories = self.story_agent.run(client, context)
        backlog = self.backlog_agent.run(client, context, stories)
        validate_backlog(context, stories, backlog)

        plan = self.scrum_agent.run(client, context, backlog)
        if plan.project_title != context.title:
            plan = plan.model_copy(update={"project_title": context.title})
        if plan.team_size != context.team_size:
            raise ValueError("L'agent Scrum a modifié le nombre de développeurs.")
        validate_scrum_plan(backlog, plan)
        return plan
