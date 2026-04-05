"""Конструктор FastAPI приложения."""

from __future__ import annotations

from fastapi import FastAPI

from src.interface.http.health import router as health_router
from src.interface.http.v1.internal.router import router as internal_router


def create_app() -> FastAPI:
    """Создает и настраивает экземпляр FastAPI."""

    app = FastAPI(title="course_service API", version="0.1.0")
    app.include_router(health_router)
    app.include_router(internal_router)
    return app

