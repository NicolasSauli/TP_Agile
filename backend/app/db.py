from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_database() -> None:
    # Import here to register the SQLAlchemy mappings before table creation.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    if "projects" in inspect(engine).get_table_names():
        columns = {column["name"] for column in inspect(engine).get_columns("projects")}
        if "owner_id" not in columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE projects ADD COLUMN owner_id VARCHAR(36)"))
