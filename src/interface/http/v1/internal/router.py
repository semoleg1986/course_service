"""Internal v1 router."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, Header, HTTPException

from src.application.access.commands.dto import ApplyAccessGrantedEventCommand
from src.application.access.queries.dto import CheckCourseAccessQuery
from src.application.courses.queries.dto import GetCourseByIdQuery
from src.domain.errors import NotFoundError
from src.interface.http.common.actor import HttpActor, get_http_actor
from src.interface.http.observability import increment_counter
from src.interface.http.v1.schemas.internal import (
    AccessGrantedEventRequest,
    AccessGrantedEventResponse,
    CourseAccessByTokenRequest,
    CourseAccessCheckRequest,
    CourseAccessDecisionResponse,
    CoursePaymentSnapshotResponse,
)
from src.interface.http.wiring import get_facade, get_service_token

router = APIRouter(prefix="/internal/v1/access", tags=["internal"])


@router.post("/check", response_model=CourseAccessDecisionResponse)
def check_course_access(
    payload: CourseAccessCheckRequest,
    service_token: str | None = Header(default=None, alias="X-Service-Token"),
    expected_token: str = Depends(get_service_token),
    facade=Depends(get_facade),
) -> CourseAccessDecisionResponse:
    """Проверяет доступ актора к курсу для межсервисного взаимодействия."""

    if not service_token:
        raise HTTPException(status_code=401, detail="Требуется X-Service-Token.")
    if service_token != expected_token:
        raise HTTPException(status_code=401, detail="Некорректный X-Service-Token.")

    result = facade.query(
        CheckCourseAccessQuery(
            course_id=payload.course_id,
            actor_account_id=payload.actor_account_id,
            actor_roles=payload.actor_roles,
            student_id=payload.student_id,
            require_active_grant=payload.require_active_grant,
            require_enrollment=payload.require_enrollment,
        )
    )
    return CourseAccessDecisionResponse(**asdict(result))


@router.post("/check-by-token", response_model=CourseAccessDecisionResponse)
def check_course_access_by_token(
    payload: CourseAccessByTokenRequest,
    actor: HttpActor = Depends(get_http_actor),
    facade=Depends(get_facade),
) -> CourseAccessDecisionResponse:
    """Проверяет доступ к курсу по ролям из Bearer access token."""

    result = facade.query(
        CheckCourseAccessQuery(
            course_id=payload.course_id,
            actor_account_id=actor.actor_id,
            actor_roles=actor.roles,
            student_id=payload.student_id,
            require_active_grant=payload.require_active_grant,
            require_enrollment=payload.require_enrollment,
        )
    )
    return CourseAccessDecisionResponse(**asdict(result))


@router.get(
    "/courses/{course_id}/payment-snapshot",
    response_model=CoursePaymentSnapshotResponse,
)
def get_course_payment_snapshot(
    course_id: str,
    service_token: str | None = Header(default=None, alias="X-Service-Token"),
    expected_token: str = Depends(get_service_token),
    facade=Depends(get_facade),
) -> CoursePaymentSnapshotResponse:
    """Возвращает минимальный платежный снапшот курса для payments_service."""

    if not service_token:
        raise HTTPException(status_code=401, detail="Требуется X-Service-Token.")
    if service_token != expected_token:
        raise HTTPException(status_code=401, detail="Некорректный X-Service-Token.")

    try:
        result = facade.query(
            GetCourseByIdQuery(
                course_id=course_id,
                actor_id="internal-course-service",
                actor_roles=["admin"],
            )
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail="Курс не найден.") from exc

    return CoursePaymentSnapshotResponse(
        course_id=result.course_id,
        price=result.price,
        currency=result.currency,
        access_ttl_days=result.access_ttl_days,
    )


@router.post(
    "/events/course-access-granted",
    response_model=AccessGrantedEventResponse,
)
def apply_access_granted_event(
    payload: AccessGrantedEventRequest,
    service_token: str | None = Header(default=None, alias="X-Service-Token"),
    expected_token: str = Depends(get_service_token),
    facade=Depends(get_facade),
) -> AccessGrantedEventResponse:
    """Применяет course.access.granted event к access projection с dedup."""

    if not service_token:
        raise HTTPException(status_code=401, detail="Требуется X-Service-Token.")
    if service_token != expected_token:
        raise HTTPException(status_code=401, detail="Некорректный X-Service-Token.")

    applied = facade.execute(
        ApplyAccessGrantedEventCommand(
            event_id=payload.event_id,
            course_id=payload.course_id,
            student_id=payload.student_id,
            granted_status=payload.granted_status,
        )
    )
    increment_counter(
        "course_access_granted_events_total",
        "Total course.access.granted events received by course_service.",
        result="applied" if applied else "replay",
        granted_status=payload.granted_status,
    )
    increment_counter(
        (
            "course_access_granted_applied_total"
            if applied
            else "course_access_granted_replays_total"
        ),
        (
            "Total applied course.access.granted events."
            if applied
            else "Total replayed course.access.granted events."
        ),
        granted_status=payload.granted_status,
    )
    return AccessGrantedEventResponse(
        event_id=payload.event_id,
        applied=applied,
        course_id=payload.course_id,
        student_id=payload.student_id,
        granted_status=payload.granted_status,
    )
