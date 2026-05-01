"""Утилиты timezone-проекции для HTTP read API."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException


def to_local_datetime(value: datetime | None, viewer_timezone: str) -> datetime | None:
    """Проецирует datetime в timezone пользователя."""
    if value is None:
        return None
    return value.astimezone(ZoneInfo(viewer_timezone))


def validate_viewer_timezone(viewer_timezone: str | None) -> None:
    """Проверяет, что viewer_timezone является корректной IANA timezone."""
    if viewer_timezone is None:
        return
    try:
        ZoneInfo(viewer_timezone)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(
            status_code=422,
            detail="viewer_timezone должен быть корректным IANA timezone",
        ) from exc
