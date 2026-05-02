"""HTTP роуты parent v1 для чтения прогресса ученика."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, Query

from src.application.access.queries.dto import (
    ListParentStudentCompletedCoursesQuery,
    ListParentStudentCourseProgressQuery,
)
from src.domain.errors import AccessDeniedError
from src.interface.http.common.actor import HttpActor, get_http_actor
from src.interface.http.common.timezone import (
    to_local_datetime,
    validate_viewer_timezone,
)
from src.interface.http.observability import increment_counter
from src.interface.http.v1.schemas.course import (
    CompletedCourseItemResponse,
    CompletedCourseListResponse,
    CourseProgressItemResponse,
    CourseProgressListResponse,
)
from src.interface.http.wiring import get_facade

router = APIRouter(prefix="/v1/parent", tags=["parent"])


@router.get(
    "/students/{student_id}/courses/progress",
    response_model=CourseProgressListResponse,
)
def list_student_course_progress(
    student_id: str,
    status: str | None = Query(default=None),
    viewer_timezone: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    actor: HttpActor = Depends(get_http_actor),
    facade=Depends(get_facade),
) -> CourseProgressListResponse:
    """Возвращает агрегированный прогресс ученика по курсам."""

    validate_viewer_timezone(viewer_timezone)

    try:
        results = facade.query(
            ListParentStudentCourseProgressQuery(
                actor_id=actor.actor_id,
                actor_roles=actor.roles,
                student_id=student_id,
                status=status,
                limit=limit,
                offset=offset,
            )
        )
    except AccessDeniedError as exc:
        increment_counter(
            "parent_acl_denied_total",
            "Total denied parent ACL checks.",
            endpoint="progress",
        )
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    increment_counter(
        "parent_progress_requests_total",
        "Total parent student progress read requests.",
        result="success",
        status_filter=status or "all",
    )
    return CourseProgressListResponse(
        items=[CourseProgressItemResponse(**asdict(item)) for item in results],
        limit=limit,
        offset=offset,
        status=status,
        viewer_timezone=viewer_timezone,
    )


@router.get(
    "/students/{student_id}/courses/completed",
    response_model=CompletedCourseListResponse,
)
def list_student_completed_courses(
    student_id: str,
    viewer_timezone: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    actor: HttpActor = Depends(get_http_actor),
    facade=Depends(get_facade),
) -> CompletedCourseListResponse:
    """Возвращает завершенные курсы ученика."""

    validate_viewer_timezone(viewer_timezone)

    try:
        results = facade.query(
            ListParentStudentCompletedCoursesQuery(
                actor_id=actor.actor_id,
                actor_roles=actor.roles,
                student_id=student_id,
                limit=limit,
                offset=offset,
            )
        )
    except AccessDeniedError as exc:
        increment_counter(
            "parent_acl_denied_total",
            "Total denied parent ACL checks.",
            endpoint="completed",
        )
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    increment_counter(
        "parent_completed_requests_total",
        "Total parent student completed-courses read requests.",
        result="success",
    )
    return CompletedCourseListResponse(
        items=[
            CompletedCourseItemResponse(
                **asdict(item),
                completed_at_local=(
                    to_local_datetime(item.completed_at, viewer_timezone)
                    if viewer_timezone
                    else None
                ),
            )
            for item in results
        ],
        limit=limit,
        offset=offset,
        viewer_timezone=viewer_timezone,
    )
