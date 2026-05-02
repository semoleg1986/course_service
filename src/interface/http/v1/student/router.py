from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from src.application.learning.commands.dto import CompleteLessonCommand
from src.application.learning.queries.dto import GetStudentCourseProgressQuery
from src.domain.errors import AccessDeniedError, InvariantViolationError, NotFoundError
from src.interface.http.common.actor import HttpActor, get_http_actor
from src.interface.http.v1.schemas.course import (
    StudentCourseProgressResponse,
    StudentLessonCompletionResponse,
)
from src.interface.http.wiring import get_facade

router = APIRouter(prefix="/v1/student", tags=["student"])


@router.post(
    "/courses/{course_id}/lessons/{lesson_id}/complete",
    response_model=StudentLessonCompletionResponse,
)
def complete_lesson(
    course_id: str,
    lesson_id: str,
    actor: HttpActor = Depends(get_http_actor),
    facade=Depends(get_facade),
) -> StudentLessonCompletionResponse:
    """Отмечает урок завершенным для текущего ученика."""
    try:
        result = facade.execute(
            CompleteLessonCommand(
                course_id=course_id,
                lesson_id=lesson_id,
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

    return StudentLessonCompletionResponse(
        course_id=result.course_id,
        module_id=result.module_id,
        lesson_id=result.lesson_id,
        student_id=result.student_id,
        lesson_status=result.lesson_status,
        course_status=result.course_status,
        progress_percent=result.progress_percent,
        completed_lessons=result.completed_lessons,
        total_lessons=result.total_lessons,
        completed_at=result.completed_at,
    )


@router.get(
    "/courses/{course_id}/progress",
    response_model=StudentCourseProgressResponse,
)
def get_course_progress(
    course_id: str,
    actor: HttpActor = Depends(get_http_actor),
    facade=Depends(get_facade),
) -> StudentCourseProgressResponse:
    """Возвращает прогресс текущего студента по курсу."""
    try:
        result = facade.query(
            GetStudentCourseProgressQuery(
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

    return StudentCourseProgressResponse(
        course_id=result.course_id,
        title=result.title,
        progress_percent=result.progress_percent,
        completed_lessons=result.completed_lessons,
        total_lessons=result.total_lessons,
        status=result.status,
        completed_at=result.completed_at,
    )
