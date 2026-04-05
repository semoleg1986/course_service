from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


def _database_url() -> str:
    return os.getenv(
        "COURSE_DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/course_service_test",
    )


@pytest.fixture(scope="session", autouse=True)
def prepare_postgres_schema() -> None:
    os.environ["COURSE_USE_INMEMORY"] = "0"
    os.environ["COURSE_AUTO_CREATE_SCHEMA"] = "0"
    database_url = _database_url()
    os.environ["COURSE_DATABASE_URL"] = database_url

    try:
        engine = create_engine(database_url, future=True, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(f"Postgres недоступен для integration tests: {exc}")

    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


@pytest.fixture(autouse=True)
def clean_tables() -> None:
    engine = create_engine(_database_url(), future=True, pool_pre_ping=True)
    with engine.begin() as conn:
        try:
            conn.execute(text("TRUNCATE TABLE enrollment_projections RESTART IDENTITY CASCADE"))
            conn.execute(text("TRUNCATE TABLE access_grant_projections RESTART IDENTITY CASCADE"))
            conn.execute(text("TRUNCATE TABLE course_owner_projections RESTART IDENTITY CASCADE"))
        except SQLAlchemyError:
            conn.execute(text("DELETE FROM enrollment_projections"))
            conn.execute(text("DELETE FROM access_grant_projections"))
            conn.execute(text("DELETE FROM course_owner_projections"))
