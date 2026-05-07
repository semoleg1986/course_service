"""In-memory rate limiter for course_service HTTP endpoints."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request

from src.infrastructure.config.settings import Settings
from src.interface.http.common.actor import HttpActor, get_http_actor
from src.interface.http.wiring import get_settings


@dataclass(frozen=True, slots=True)
class RateLimitRule:
    """Rule: no more than `max_requests` within `window_seconds`."""

    max_requests: int
    window_seconds: int


class InMemoryRateLimiter:
    """Thread-safe sliding-window limiter."""

    def __init__(self, now: Callable[[], float] | None = None) -> None:
        self._now = now or time.monotonic
        self._events: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, scope: str, key: str, rule: RateLimitRule) -> bool:
        now = self._now()
        boundary = now - float(rule.window_seconds)
        token = (scope, key)

        with self._lock:
            bucket = self._events[token]
            while bucket and bucket[0] <= boundary:
                bucket.popleft()
            if len(bucket) >= rule.max_requests:
                return False
            bucket.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._events.clear()


_limiter = InMemoryRateLimiter()


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _correlation_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None)


def _rate_limit_detail(request: Request) -> dict[str, str | int | None]:
    return {
        "detail": "Слишком много запросов, попробуйте позже.",
        "request_id": _request_id(request),
        "correlation_id": _correlation_id(request),
    }


def _enforce_rate_limit(
    *,
    scope: str,
    key: str,
    rule: RateLimitRule,
    request: Request,
) -> None:
    if _limiter.allow(scope=scope, key=key, rule=rule):
        return
    raise HTTPException(status_code=429, detail=_rate_limit_detail(request))


def enforce_student_complete_rate_limit(
    request: Request,
    actor: HttpActor = Depends(get_http_actor),
    settings: Settings = Depends(get_settings),
) -> None:
    _enforce_rate_limit(
        scope="student_complete",
        key=actor.actor_id,
        rule=RateLimitRule(
            max_requests=settings.student_complete_rate_limit_max,
            window_seconds=settings.student_complete_rate_limit_window_seconds,
        ),
        request=request,
    )


def enforce_student_progress_rate_limit(
    request: Request,
    actor: HttpActor = Depends(get_http_actor),
    settings: Settings = Depends(get_settings),
) -> None:
    _enforce_rate_limit(
        scope="student_progress",
        key=actor.actor_id,
        rule=RateLimitRule(
            max_requests=settings.student_progress_rate_limit_max,
            window_seconds=settings.student_progress_rate_limit_window_seconds,
        ),
        request=request,
    )


def enforce_parent_progress_rate_limit(
    request: Request,
    actor: HttpActor = Depends(get_http_actor),
    settings: Settings = Depends(get_settings),
) -> None:
    _enforce_rate_limit(
        scope="parent_progress",
        key=actor.actor_id,
        rule=RateLimitRule(
            max_requests=settings.parent_progress_rate_limit_max,
            window_seconds=settings.parent_progress_rate_limit_window_seconds,
        ),
        request=request,
    )


def enforce_parent_completed_rate_limit(
    request: Request,
    actor: HttpActor = Depends(get_http_actor),
    settings: Settings = Depends(get_settings),
) -> None:
    _enforce_rate_limit(
        scope="parent_completed",
        key=actor.actor_id,
        rule=RateLimitRule(
            max_requests=settings.parent_completed_rate_limit_max,
            window_seconds=settings.parent_completed_rate_limit_window_seconds,
        ),
        request=request,
    )


def enforce_admin_publish_rate_limit(
    request: Request,
    actor: HttpActor = Depends(get_http_actor),
    settings: Settings = Depends(get_settings),
) -> None:
    _enforce_rate_limit(
        scope="admin_publish",
        key=actor.actor_id,
        rule=RateLimitRule(
            max_requests=settings.admin_publish_rate_limit_max,
            window_seconds=settings.admin_publish_rate_limit_window_seconds,
        ),
        request=request,
    )


def enforce_admin_archive_rate_limit(
    request: Request,
    actor: HttpActor = Depends(get_http_actor),
    settings: Settings = Depends(get_settings),
) -> None:
    _enforce_rate_limit(
        scope="admin_archive",
        key=actor.actor_id,
        rule=RateLimitRule(
            max_requests=settings.admin_archive_rate_limit_max,
            window_seconds=settings.admin_archive_rate_limit_window_seconds,
        ),
        request=request,
    )


def reset_rate_limiter() -> None:
    _limiter.reset()
