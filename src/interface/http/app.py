"""Конструктор FastAPI приложения."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.interface.http.health import router as health_router
from src.interface.http.v1.admin.router import router as admin_router
from src.interface.http.v1.internal.router import router as internal_router
from src.interface.http.wiring import get_runtime


@asynccontextmanager
async def _lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Инициализирует runtime и схему БД на старте процесса."""

    get_runtime()
    yield


def create_app() -> FastAPI:
    """Создает и настраивает экземпляр FastAPI."""

    app = FastAPI(title="course_service API", version="0.1.0", lifespan=_lifespan)

    app.include_router(health_router)
    app.include_router(admin_router)
    app.include_router(internal_router)
    return app
