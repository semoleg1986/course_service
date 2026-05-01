"""Конструктор FastAPI приложения."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.interface.http.errors import register_exception_handlers
from src.interface.http.health import router as health_router
from src.interface.http.observability import (
    configure_http_logging,
    install_observability,
)
from src.interface.http.v1.admin.router import router as admin_router
from src.interface.http.v1.internal.router import router as internal_router
from src.interface.http.v1.parent.router import router as parent_router
from src.interface.http.wiring import get_runtime


@asynccontextmanager
async def _lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Инициализирует runtime и схему БД на старте процесса."""

    get_runtime()
    yield


def create_app() -> FastAPI:
    """Создает и настраивает экземпляр FastAPI."""

    configure_http_logging()
    app = FastAPI(title="course_service API", version="0.1.0", lifespan=_lifespan)

    install_observability(app)
    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(admin_router)
    app.include_router(parent_router)
    app.include_router(internal_router)
    return app
