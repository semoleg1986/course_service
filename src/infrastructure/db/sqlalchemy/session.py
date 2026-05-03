"""SQLAlchemy engine/session factory."""

from __future__ import annotations

import os
from contextlib import contextmanager
from contextvars import ContextVar, Token

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

_CURRENT_SESSION: ContextVar[Session | None] = ContextVar(
    "course_service_current_session", default=None
)


def get_database_url() -> str:
    """Возвращает URL БД из окружения."""

    return os.getenv("COURSE_DATABASE_URL", "sqlite:///./course_service.db")


def build_engine(url: str | None = None) -> Engine:
    """Создает SQLAlchemy engine."""

    return create_engine(url or get_database_url(), future=True, pool_pre_ping=True)


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Создает sessionmaker для SQLAlchemy."""

    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_current_session() -> Session | None:
    """Возвращает текущую транзакционную session, если она установлена."""

    return _CURRENT_SESSION.get()


def set_current_session(session: Session) -> Token[Session | None]:
    """Делает session текущей для вложенных репозиториев."""

    return _CURRENT_SESSION.set(session)


def reset_current_session(token: Token[Session | None]) -> None:
    """Сбрасывает текущую транзакционную session."""

    _CURRENT_SESSION.reset(token)


@contextmanager
def managed_session(session_factory: sessionmaker[Session]):
    """Возвращает текущую session или временную read-only session."""

    current = get_current_session()
    if current is not None:
        yield current
        return
    with session_factory() as session:
        yield session


@contextmanager
def managed_transaction(session_factory: sessionmaker[Session]):
    """Возвращает текущую transaction session или временную auto-commit session."""

    current = get_current_session()
    if current is not None:
        yield current
        return
    with session_factory.begin() as session:
        yield session
