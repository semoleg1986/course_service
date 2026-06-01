from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from src.application.learning.commands.dto import CompleteLessonCommand
from src.application.learning.queries.dto import (
    GetStudentCourseLearningQuery,
    GetStudentCourseProgressQuery,
)
from src.domain.errors import AccessDeniedError, InvariantViolationError, NotFoundError
from src.interface.http.common.actor import HttpActor, get_http_actor
from src.interface.http.common.rate_limit import (
    enforce_student_complete_rate_limit,
    enforce_student_progress_rate_limit,
)
from src.interface.http.observability import increment_counter
from src.interface.http.v1.schemas.course import (
    StudentCourseLearningLessonResponse,
    StudentCourseLearningModuleResponse,
    StudentCourseLearningProgressResponse,
    StudentCourseLearningResponse,
    StudentCourseProgressResponse,
    StudentLessonCompletionResponse,
)
from src.interface.http.wiring import get_facade

router = APIRouter(prefix="/v1/student", tags=["student"])


def _increment_student_course_learning_requests(
    *, result: str, status: str = "none"
) -> None:
    increment_counter(
        "student_course_learning_requests_total",
        "Total student course learning read requests.",
        result=result,
        status=status,
    )


@router.post(
    "/courses/{course_id}/lessons/{lesson_id}/complete",
    response_model=StudentLessonCompletionResponse,
)
def complete_lesson(
    course_id: str,
    lesson_id: str,
    _: None = Depends(enforce_student_complete_rate_limit),
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
        increment_counter(
            "student_lesson_completion_requests_total",
            "Total student lesson completion requests.",
            result="not_found",
            course_status="unknown",
        )
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AccessDeniedError as exc:
        increment_counter(
            "student_lesson_completion_requests_total",
            "Total student lesson completion requests.",
            result="denied",
            course_status="unknown",
        )
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        increment_counter(
            "student_lesson_completion_requests_total",
            "Total student lesson completion requests.",
            result="conflict",
            course_status="unknown",
        )
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    increment_counter(
        "student_lesson_completion_requests_total",
        "Total student lesson completion requests.",
        result="success",
        course_status=result.course_status,
    )
    if result.course_status == "completed":
        increment_counter(
            "course_completions_total",
            "Total completed courses via student learning flow.",
            source="student_complete",
        )

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
    _: None = Depends(enforce_student_progress_rate_limit),
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
        increment_counter(
            "student_course_progress_requests_total",
            "Total student course progress read requests.",
            result="not_found",
        )
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AccessDeniedError as exc:
        increment_counter(
            "student_course_progress_requests_total",
            "Total student course progress read requests.",
            result="denied",
        )
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        increment_counter(
            "student_course_progress_requests_total",
            "Total student course progress read requests.",
            result="conflict",
        )
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    increment_counter(
        "student_course_progress_requests_total",
        "Total student course progress read requests.",
        result="success",
        status=result.status,
    )

    return StudentCourseProgressResponse(
        course_id=result.course_id,
        title=result.title,
        progress_percent=result.progress_percent,
        completed_lessons=result.completed_lessons,
        total_lessons=result.total_lessons,
        status=result.status,
        completed_at=result.completed_at,
    )


@router.get(
    "/courses/{course_id}/learning",
    response_model=StudentCourseLearningResponse,
)
def get_course_learning(
    course_id: str,
    _: None = Depends(enforce_student_progress_rate_limit),
    actor: HttpActor = Depends(get_http_actor),
    facade=Depends(get_facade),
) -> StudentCourseLearningResponse:
    """Возвращает student-facing курс: прогресс, модули, уроки и next lesson."""
    try:
        result = facade.query(
            GetStudentCourseLearningQuery(
                course_id=course_id,
                actor_id=actor.actor_id,
                actor_roles=actor.roles,
            )
        )
    except NotFoundError as exc:
        _increment_student_course_learning_requests(result="not_found")
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AccessDeniedError as exc:
        _increment_student_course_learning_requests(result="denied")
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        _increment_student_course_learning_requests(result="conflict")
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    _increment_student_course_learning_requests(
        result="success", status=result.progress.status
    )

    return StudentCourseLearningResponse(
        course_id=result.course_id,
        title=result.title,
        description=result.description,
        level=result.level,
        progress=StudentCourseLearningProgressResponse(
            progress_percent=result.progress.progress_percent,
            completed_lessons=result.progress.completed_lessons,
            total_lessons=result.progress.total_lessons,
            status=result.progress.status,
            completed_at=result.progress.completed_at,
        ),
        next_lesson_id=result.next_lesson_id,
        modules=[
            StudentCourseLearningModuleResponse(
                module_id=module.module_id,
                title=module.title,
                description=module.description,
                is_required=module.is_required,
                lessons_count=module.lessons_count,
                lessons=[
                    StudentCourseLearningLessonResponse(
                        lesson_id=lesson.lesson_id,
                        title=lesson.title,
                        description=lesson.description,
                        content_type=lesson.content_type,
                        content_ref=lesson.content_ref,
                        duration_minutes=lesson.duration_minutes,
                        is_preview=lesson.is_preview,
                        progress_status=lesson.progress_status,
                        is_completed=lesson.is_completed,
                    )
                    for lesson in module.lessons
                ],
            )
            for module in result.modules
        ],
    )
