from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AgentRun, AuthSession, BacklogTask, Project, User
from app.schemas import (
    APIError,
    AuthResponse,
    AuthUser,
    ClarificationAnswer,
    ClarificationResponse,
    GenerationResponse,
    ProjectCreate,
    ProjectDetail,
    ProjectRead,
    ProjectStatus,
    ProjectUpdate,
    LoginRequest,
    RegisterRequest,
    TaskUpdate,
)
from app.services.agents import AgentExecutionError, AgentSuite, AgentUnavailableError
from app.services.orchestrator import ClarificationRequiredError, ProjectOrchestrator
from app.services.repository import (
    NotFoundError,
    get_project_or_404,
    project_detail,
    project_read,
    task_read,
    validate_dependencies,
)

router = APIRouter(tags=["projects"])
Database = Annotated[Session, Depends(get_db)]
TOKEN_TTL = timedelta(days=7)


def password_digest(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 240_000)
    return f"{salt.hex()}${digest.hex()}"


def password_matches(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$", 1)
        expected = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 240_000).hex()
        return hmac.compare_digest(expected, digest_hex)
    except ValueError:
        return False


def create_session(db: Session, user: User) -> AuthResponse:
    token = secrets.token_urlsafe(32)
    db.add(AuthSession(
        user_id=user.id,
        token_hash=hashlib.sha256(token.encode()).hexdigest(),
        expires_at=datetime.now(timezone.utc) + TOKEN_TTL,
    ))
    db.commit()
    return AuthResponse(token=token, user=AuthUser.model_validate(user, from_attributes=True))


def current_user(
    db: Database,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentification requise.")
    token = authorization[7:].strip()
    session = db.scalar(select(AuthSession).where(AuthSession.token_hash == hashlib.sha256(token.encode()).hexdigest()))
    now = datetime.now(timezone.utc)
    expires_at = session.expires_at.replace(tzinfo=timezone.utc) if session and session.expires_at.tzinfo is None else session.expires_at if session else None
    if session is None or expires_at < now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session invalide ou expirée.")
    user = db.get(User, session.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable.")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


@router.post("/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED, tags=["auth"])
def register(payload: RegisterRequest, db: Database) -> AuthResponse:
    email = payload.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cette adresse e-mail est déjà utilisée.")
    user = User(name=payload.name.strip(), email=email, password_hash=password_digest(payload.password))
    db.add(user)
    db.flush()
    response = create_session(db, user)
    return response


@router.post("/auth/login", response_model=AuthResponse, tags=["auth"])
def login(payload: LoginRequest, db: Database) -> AuthResponse:
    user = db.scalar(select(User).where(User.email == payload.email.strip().lower()))
    if user is None or not password_matches(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou mot de passe incorrect.")
    return create_session(db, user)


@router.get("/auth/me", response_model=AuthUser, tags=["auth"])
def me(user: CurrentUser) -> AuthUser:
    return AuthUser.model_validate(user, from_attributes=True)


def get_orchestrator() -> ProjectOrchestrator:
    from app.core.config import get_settings

    return ProjectOrchestrator(AgentSuite(get_settings()))


Orchestrator = Annotated[ProjectOrchestrator, Depends(get_orchestrator)]


def project_or_error(db: Session, project_id: UUID) -> Project:
    try:
        return get_project_or_404(db, project_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


def owned_project_or_error(db: Session, project_id: UUID, user: User) -> Project:
    project = project_or_error(db, project_id)
    if project.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projet introuvable.")
    return project


@router.post("/projects", response_model=ProjectDetail, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Database, user: CurrentUser) -> ProjectDetail:
    project = Project(owner_id=user.id, name=payload.name, description=payload.description, status=ProjectStatus.DRAFT.value)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project_detail(db, project)


@router.get("/projects", response_model=list[ProjectRead])
def list_projects(db: Database, user: CurrentUser) -> list[ProjectRead]:
    projects = db.scalars(select(Project).where(Project.owner_id == user.id).order_by(Project.updated_at.desc())).all()
    return [project_read(project) for project in projects]


@router.get("/projects/{project_id}", response_model=ProjectDetail, responses={404: {"model": APIError}})
def get_project(project_id: UUID, db: Database, user: CurrentUser) -> ProjectDetail:
    return project_detail(db, owned_project_or_error(db, project_id, user))


@router.patch("/projects/{project_id}", response_model=ProjectDetail, responses={404: {"model": APIError}})
def update_project(project_id: UUID, payload: ProjectUpdate, db: Database, user: CurrentUser) -> ProjectDetail:
    project = owned_project_or_error(db, project_id, user)
    changes = payload.model_dump(exclude_unset=True)
    if "name" in changes:
        project.name = changes["name"]
    if "description" in changes and changes["description"] != project.description:
        project.description = changes["description"]
        project.revision += 1
        project.status = ProjectStatus.STALE.value
    db.commit()
    db.refresh(project)
    return project_detail(db, project)


@router.post(
    "/projects/{project_id}/clarifications/start",
    response_model=ClarificationResponse,
    responses={404: {"model": APIError}, 503: {"model": APIError}, 502: {"model": APIError}},
)
def start_clarification(
    project_id: UUID,
    db: Database,
    orchestrator: Orchestrator,
    user: CurrentUser,
) -> ClarificationResponse:
    project = owned_project_or_error(db, project_id, user)
    try:
        result = orchestrator.start_clarification(db, project)
    except AgentUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except AgentExecutionError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return ClarificationResponse(project=project_read(project), question=result.next_question, message=result.message)


@router.post(
    "/projects/{project_id}/clarifications",
    response_model=ClarificationResponse,
    responses={404: {"model": APIError}, 503: {"model": APIError}, 502: {"model": APIError}},
)
def answer_clarification(
    project_id: UUID,
    payload: ClarificationAnswer,
    db: Database,
    orchestrator: Orchestrator,
    user: CurrentUser,
) -> ClarificationResponse:
    project = owned_project_or_error(db, project_id, user)
    try:
        result = orchestrator.answer_clarification(db, project, payload)
    except AgentUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except AgentExecutionError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return ClarificationResponse(project=project_read(project), question=result.next_question, message=result.message)


@router.post(
    "/projects/{project_id}/generate",
    response_model=GenerationResponse,
    responses={404: {"model": APIError}, 409: {"model": APIError}, 503: {"model": APIError}, 502: {"model": APIError}},
)
def generate_project(project_id: UUID, db: Database, orchestrator: Orchestrator, user: CurrentUser) -> GenerationResponse:
    project = owned_project_or_error(db, project_id, user)
    try:
        return orchestrator.generate(db, project)
    except ClarificationRequiredError as exc:
        detail = {"message": str(exc), "next_question": exc.question.model_dump() if exc.question else None}
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail) from exc
    except AgentUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except (AgentExecutionError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.patch(
    "/projects/{project_id}/tasks/{task_id}",
    response_model=dict,
    responses={404: {"model": APIError}, 422: {"model": APIError}},
)
def update_task(project_id: UUID, task_id: UUID, payload: TaskUpdate, db: Database, user: CurrentUser) -> dict:
    owned_project_or_error(db, project_id, user)
    task = db.get(BacklogTask, task_id)
    if task is None or task.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} was not found.")
    updates = payload.model_dump(exclude_unset=True)
    if "dependency_ids" in updates:
        try:
            validate_dependencies(project_id, updates["dependency_ids"], task_id, db)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
        updates["dependency_ids_json"] = [str(dependency_id) for dependency_id in updates.pop("dependency_ids")]
    for field, value in updates.items():
        setattr(task, field, value.value if hasattr(value, "value") else value)
    task.is_manual = True
    db.commit()
    db.refresh(task)
    return {"task": task_read(task).model_dump(mode="json")}


@router.get("/projects/{project_id}/agent-runs", response_model=list[dict], responses={404: {"model": APIError}})
def list_agent_runs(project_id: UUID, db: Database, user: CurrentUser) -> list[dict]:
    owned_project_or_error(db, project_id, user)
    runs = db.scalars(
        select(AgentRun).where(AgentRun.project_id == project_id).order_by(AgentRun.created_at.desc())
    ).all()
    return [
        {
            "id": str(run.id),
            "agent_name": run.agent_name,
            "status": run.status,
            "error": run.error,
            "created_at": run.created_at,
        }
        for run in runs
    ]
