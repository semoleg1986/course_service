"""Базовый declarative-класс SQLAlchemy."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """База для ORM-моделей course_service."""
