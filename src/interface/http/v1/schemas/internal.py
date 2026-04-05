"""Схемы internal API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CourseAccessCheckRequest(BaseModel):
    """Request проверки доступа к курсу."""

    course_id: str = Field(..., description="UUID курса")
    actor_account_id: str = Field(..., description="UUID account актора")
    actor_roles: list[str] = Field(..., description="Роли актора")
    student_id: str | None = Field(default=None, description="UUID ученика")
    require_active_grant: bool = True
    require_enrollment: bool = False


class CourseAccessByTokenRequest(BaseModel):
    """Request проверки доступа по Bearer токену актора."""

    course_id: str = Field(..., description="UUID курса")
    student_id: str | None = Field(default=None, description="UUID ученика")
    require_active_grant: bool = True
    require_enrollment: bool = False


class CourseAccessDecisionResponse(BaseModel):
    """Response решения по доступу к курсу."""

    decision: str
    reason_code: str
    course_id: str
    actor_account_id: str
    student_id: str | None = None
    grant_status: str | None = None
    enrollment_status: str | None = None
    checked_at: datetime
