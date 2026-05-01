"""HTTP роуты public v1 для опубликованных курсов."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, Query

from src.application.common.dto import PublicCourseResult
from src.application.courses.queries.dto import GetPublishedCourseBySlugQuery
from src.domain.errors import NotFoundError
from src.interface.http.common.timezone import (
    to_local_datetime,
    validate_viewer_timezone,
)
from src.interface.http.v1.schemas.course import (
    PublicCourseModuleResponse,
    PublicCourseResponse,
    SeoResponse,
)
from src.interface.http.wiring import get_facade

router = APIRouter(prefix="/v1/public", tags=["public"])


def _to_public_course_response(
    result: PublicCourseResult,
    viewer_timezone: str | None = None,
) -> PublicCourseResponse:
    payload = asdict(result)
    seo_payload = {
        "meta_title": result.seo_meta_title,
        "meta_description": result.seo_meta_description,
        "canonical_url": result.seo_canonical_url,
        "robots": result.seo_robots,
        "og_image_url": result.seo_og_image_url,
    }
    modules = [
        PublicCourseModuleResponse(**item) for item in payload.pop("modules", [])
    ]
    for key in [
        "seo_meta_title",
        "seo_meta_description",
        "seo_canonical_url",
        "seo_robots",
        "seo_og_image_url",
    ]:
        payload.pop(key, None)
    payload["seo"] = SeoResponse(**seo_payload)
    payload["modules"] = modules
    payload["viewer_timezone"] = viewer_timezone
    payload["starts_at_local"] = (
        to_local_datetime(result.starts_at, viewer_timezone)
        if viewer_timezone
        else None
    )
    payload["enrollment_opens_at_local"] = (
        to_local_datetime(result.enrollment_opens_at, viewer_timezone)
        if viewer_timezone
        else None
    )
    payload["enrollment_closes_at_local"] = (
        to_local_datetime(result.enrollment_closes_at, viewer_timezone)
        if viewer_timezone
        else None
    )
    return PublicCourseResponse(**payload)


@router.get("/courses/{slug}", response_model=PublicCourseResponse)
def get_public_course(
    slug: str,
    viewer_timezone: str | None = Query(default=None),
    facade=Depends(get_facade),
) -> PublicCourseResponse:
    """Возвращает опубликованный курс по slug."""

    validate_viewer_timezone(viewer_timezone)
    try:
        result = facade.query(GetPublishedCourseBySlugQuery(slug=slug))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_public_course_response(result, viewer_timezone=viewer_timezone)
