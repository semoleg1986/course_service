"""Обработчики ошибок HTTP-слоя."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.interface.http import problem_types


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _correlation_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None)


def _headers(request: Request, extra: dict[str, str] | None = None) -> dict[str, str]:
    headers = dict(extra or {})
    request_id = _request_id(request)
    correlation_id = _correlation_id(request)
    if request_id is not None:
        headers["X-Request-ID"] = request_id
    if correlation_id is not None:
        headers["X-Correlation-ID"] = correlation_id
    return headers


def _problem(
    request: Request,
    *,
    status: int,
    title: str,
    problem_type: str,
    detail: object,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "type": problem_type,
            "title": title,
            "status": status,
            "detail": detail,
            "instance": str(request.url.path),
            "request_id": _request_id(request),
            "correlation_id": _correlation_id(request),
        },
        headers=_headers(request, headers),
        media_type="application/problem+json",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Регистрирует единый RFC7807 формат ошибок с trace ids."""

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return _problem(
            request,
            status=422,
            title="Ошибка валидации",
            problem_type=problem_types.VALIDATION,
            detail=str(exc),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        mapping = {
            401: ("Не авторизован", problem_types.UNAUTHORIZED),
            403: ("Доступ запрещен", problem_types.ACCESS_DENIED),
            404: ("Не найдено", problem_types.NOT_FOUND),
            409: ("Конфликт", problem_types.CONFLICT),
            422: ("Ошибка валидации", problem_types.VALIDATION),
        }
        title, problem_type = mapping.get(
            exc.status_code, (str(exc.detail), "about:blank")
        )
        return _problem(
            request,
            status=exc.status_code,
            title=title,
            problem_type=problem_type,
            detail=exc.detail,
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        return _problem(
            request,
            status=500,
            title="Внутренняя ошибка",
            problem_type=problem_types.INTERNAL_ERROR,
            detail="Unhandled server error.",
        )
