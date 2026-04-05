"""SQLAlchemy engine/session factory."""

from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def get_database_url() -> str:
    """Возвращает URL БД из окружения."""

    return os.getenv("COURSE_DATABASE_URL", "sqlite:///./course_service.db")


def build_engine(url: str | None = None) -> Engine:
    """Создает SQLAlchemy engine."""

    return create_engine(url or get_database_url(), future=True, pool_pre_ping=True)


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Создает sessionmaker для SQLAlchemy."""

    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
