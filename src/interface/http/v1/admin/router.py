"""HTTP роуты admin v1 для курсов."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException

from src.application.common.dto import CourseResult
from src.application.courses.commands.dto import (
    AddLessonCommand,
    AddModuleCommand,
    ArchiveCourseCommand,
    CreateCourseCommand,
    PublishCourseCommand,
    UpdateCourseCommand,
)
from src.application.courses.queries.dto import GetCourseByIdQuery
from src.domain.errors import AccessDeniedError, InvariantViolationError, NotFoundError
from src.interface.http.common.actor import HttpActor, get_http_actor
from src.interface.http.v1.schemas.course import (
    AddLessonRequest,
    AddModuleRequest,
    CourseResponse,
    CreateCourseRequest,
    SeoResponse,
    UpdateCourseRequest,
)
from src.interface.http.wiring import get_facade

router = APIRouter(prefix="/v1/admin", tags=["admin"])


def _to_course_response(result: CourseResult) -> CourseResponse:
    payload = asdict(result)
    seo_payload = {
        "meta_title": result.seo_meta_title,
        "meta_description": result.seo_meta_description,
        "canonical_url": result.seo_canonical_url,
        "robots": result.seo_robots,
        "og_image_url": result.seo_og_image_url,
    }
    for key in [
        "seo_meta_title",
        "seo_meta_description",
        "seo_canonical_url",
        "seo_robots",
        "seo_og_image_url",
    ]:
        payload.pop(key, None)
    payload["seo"] = SeoResponse(**seo_payload)
    return CourseResponse(**payload)


@router.post("/courses", response_model=CourseResponse, status_code=201)
def create_course(
    payload: CreateCourseRequest,
    actor: HttpActor = Depends(get_http_actor),
    facade=Depends(get_facade),
) -> CourseResponse:
    """Создает курс."""

    try:
        result = facade.execute(
            CreateCourseCommand(
                title=payload.title,
                description=payload.description,
                teacher_id=payload.teacher_id,
                teacher_display_name=payload.teacher_display_name,
                starts_at=payload.starts_at,
                duration_days=payload.duration_days,
                access_ttl_days=payload.access_ttl_days,
                enrollment_opens_at=payload.enrollment_opens_at,
                enrollment_closes_at=payload.enrollment_closes_at,
                price=payload.price,
                currency=payload.currency.upper(),
                language=payload.language,
                age_min=payload.age_min,
                age_max=payload.age_max,
                level=payload.level,
                tags=payload.tags,
                cover_image_url=payload.cover_image_url,
                is_live_enabled=payload.is_live_enabled,
                live_room_template_id=payload.live_room_template_id,
                timezone=payload.timezone,
                max_students=payload.max_students,
                slug=payload.slug,
                seo_meta_title=payload.seo.meta_title if payload.seo else None,
                seo_meta_description=(
                    payload.seo.meta_description if payload.seo else None
                ),
                seo_canonical_url=payload.seo.canonical_url if payload.seo else None,
                seo_robots=payload.seo.robots if payload.seo else "index",
                seo_og_image_url=payload.seo.og_image_url if payload.seo else None,
                actor_id=actor.actor_id,
                actor_roles=actor.roles,
            )
        )
    except AccessDeniedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_course_response(result)


@router.patch("/courses/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: str,
    payload: UpdateCourseRequest,
    actor: HttpActor = Depends(get_http_actor),
    facade=Depends(get_facade),
) -> CourseResponse:
    """Обновляет курс."""

    try:
        result = facade.execute(
            UpdateCourseCommand(
                course_id=course_id,
                actor_id=actor.actor_id,
                actor_roles=actor.roles,
                title=payload.title,
                description=payload.description,
                teacher_id=payload.teacher_id,
                teacher_display_name=payload.teacher_display_name,
                starts_at=payload.starts_at,
                duration_days=payload.duration_days,
                access_ttl_days=payload.access_ttl_days,
                enrollment_opens_at=payload.enrollment_opens_at,
                enrollment_closes_at=payload.enrollment_closes_at,
                price=payload.price,
                currency=payload.currency.upper() if payload.currency else None,
                language=payload.language,
                age_min=payload.age_min,
                age_max=payload.age_max,
                level=payload.level,
                tags=payload.tags,
                cover_image_url=payload.cover_image_url,
                is_live_enabled=payload.is_live_enabled,
                live_room_template_id=payload.live_room_template_id,
                timezone=payload.timezone,
                max_students=payload.max_students,
                slug=payload.slug,
                seo_meta_title=payload.seo.meta_title if payload.seo else None,
                seo_meta_description=(
                    payload.seo.meta_description if payload.seo else None
                ),
                seo_canonical_url=payload.seo.canonical_url if payload.seo else None,
                seo_robots=payload.seo.robots if payload.seo else None,
                seo_og_image_url=payload.seo.og_image_url if payload.seo else None,
            )
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AccessDeniedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_course_response(result)


@router.get("/courses/{course_id}", response_model=CourseResponse)
def get_course(
    course_id: str,
    actor: HttpActor = Depends(get_http_actor),
    facade=Depends(get_facade),
) -> CourseResponse:
    """Возвращает курс по ID."""

    try:
        result = facade.query(
            GetCourseByIdQuery(
                course_id=course_id, actor_id=actor.actor_id, actor_roles=actor.roles
            )
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AccessDeniedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return _to_course_response(result)


@router.post("/courses/{course_id}/modules", response_model=CourseResponse)
def add_module(
    course_id: str,
    payload: AddModuleRequest,
    actor: HttpActor = Depends(get_http_actor),
    facade=Depends(get_facade),
) -> CourseResponse:
    """Добавляет модуль в курс."""

    try:
        result = facade.execute(
            AddModuleCommand(
                course_id=course_id,
                module_id=payload.module_id,
                title=payload.title,
                actor_id=actor.actor_id,
                actor_roles=actor.roles,
            )
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AccessDeniedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_course_response(result)


@router.post(
    "/courses/{course_id}/modules/{module_id}/lessons", response_model=CourseResponse
)
def add_lesson(
    course_id: str,
    module_id: str,
    payload: AddLessonRequest,
    actor: HttpActor = Depends(get_http_actor),
    facade=Depends(get_facade),
) -> CourseResponse:
    """Добавляет урок в модуль курса."""

    try:
        result = facade.execute(
            AddLessonCommand(
                course_id=course_id,
                module_id=module_id,
                lesson_id=payload.lesson_id,
                title=payload.title,
                actor_id=actor.actor_id,
                actor_roles=actor.roles,
            )
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AccessDeniedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_course_response(result)


@router.post("/courses/{course_id}/publish", response_model=CourseResponse)
def publish_course(
    course_id: str,
    actor: HttpActor = Depends(get_http_actor),
    facade=Depends(get_facade),
) -> CourseResponse:
    """Публикует курс."""

    try:
        result = facade.execute(
            PublishCourseCommand(
                course_id=course_id,
                actor_id=actor.actor_id,
                actor_roles=actor.roles,
            )
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AccessDeniedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_course_response(result)


@router.post("/courses/{course_id}/archive", response_model=CourseResponse)
def archive_course(
    course_id: str,
    actor: HttpActor = Depends(get_http_actor),
    facade=Depends(get_facade),
) -> CourseResponse:
    """Архивирует курс."""

    try:
        result = facade.execute(
            ArchiveCourseCommand(
                course_id=course_id,
                actor_id=actor.actor_id,
                actor_roles=actor.roles,
            )
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AccessDeniedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_course_response(result)
