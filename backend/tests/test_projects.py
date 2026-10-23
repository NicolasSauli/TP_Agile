from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
from app.main import app


def test_project_crud_lifecycle(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
    )
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            registered = client.post(
                "/api/v1/auth/register",
                json={"name": "Test User", "email": "test@example.com", "password": "password123"},
            )
            assert registered.status_code == 201
            headers = {"Authorization": f"Bearer {registered.json()['token']}"}
            created = client.post(
                "/api/v1/projects",
                json={
                    "name": "Plateforme de réservation",
                    "description": "Une plateforme qui permet aux indépendants de gérer leurs réservations.",
                },
                headers=headers,
            )
            assert created.status_code == 201
            project = created.json()
            assert project["status"] == "draft"
            assert project["tasks"] == []

            listing = client.get("/api/v1/projects", headers=headers)
            assert listing.status_code == 200
            assert len(listing.json()) == 1

            changed = client.patch(
                f"/api/v1/projects/{project['id']}",
                json={"description": "Une plateforme de réservation avec agenda et notifications pour indépendants."},
                headers=headers,
            )
            assert changed.status_code == 200
            assert changed.json()["status"] == "stale"
            assert changed.json()["revision"] == 2
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
