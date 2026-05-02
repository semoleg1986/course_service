from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.db.inmemory.access_read_model import InMemoryAccessReadModel
from src.infrastructure.db.sqlalchemy import models as _models  # noqa: F401
from src.infrastructure.db.sqlalchemy.access_read_model_sqlalchemy import (
    SqlalchemyAccessReadModel,
)
from src.infrastructure.db.sqlalchemy.base import Base


def _now() -> datetime:
    return datetime(2026, 5, 2, 12, 0, tzinfo=UTC)


def test_inmemory_progress_read_model_stores_lesson_and_course_progress() -> None:
    read_model = InMemoryAccessReadModel()
    now = _now()

    read_model.upsert_lesson_progress(
        course_id="course-1",
        module_id="module-1",
        lesson_id="lesson-1",
        student_id="student-1",
        progress_id="lp-1",
        status="completed",
        created_at=now,
        created_by="student-1",
        updated_at=now,
        updated_by="student-1",
        version=2,
        started_at=now,
        completed_at=now,
        last_activity_at=now,
    )
    read_model.upsert_lesson_progress(
        course_id="course-1",
        module_id="module-1",
        lesson_id="lesson-2",
        student_id="student-1",
        progress_id="lp-2",
        status="in_progress",
        created_at=now,
        created_by="student-1",
        updated_at=now,
        updated_by="student-1",
        version=2,
        started_at=now,
        completed_at=None,
        last_activity_at=now,
    )

    assert read_model.list_completed_lesson_ids(
        course_id="course-1",
        student_id="student-1",
    ) == ["lesson-1"]

    read_model.store_course_progress_summary(
        course_id="course-1",
        student_id="student-1",
        status="in_progress",
        progress_percent=50.0,
        completed_lessons=1,
        total_lessons=2,
        completed_at=None,
    )
    assert read_model.get_course_progress_summary(
        course_id="course-1",
        student_id="student-1",
    ) == ("in_progress", 50.0, 1, 2, None)


def test_sqlalchemy_progress_read_model_stores_lesson_and_course_progress() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        future=True,
    )
    read_model = SqlalchemyAccessReadModel(session_factory)
    now = _now()

    read_model.upsert_lesson_progress(
        course_id="course-1",
        module_id="module-1",
        lesson_id="lesson-1",
        student_id="student-1",
        progress_id="lp-1",
        status="completed",
        created_at=now,
        created_by="student-1",
        updated_at=now,
        updated_by="student-1",
        version=2,
        started_at=now,
        completed_at=now,
        last_activity_at=now,
    )
    read_model.upsert_lesson_progress(
        course_id="course-1",
        module_id="module-1",
        lesson_id="lesson-1",
        student_id="student-1",
        progress_id="lp-1",
        status="completed",
        created_at=now,
        created_by="student-1",
        updated_at=now,
        updated_by="student-1",
        version=2,
        started_at=now,
        completed_at=now,
        last_activity_at=now,
    )
    read_model.upsert_lesson_progress(
        course_id="course-1",
        module_id="module-1",
        lesson_id="lesson-2",
        student_id="student-1",
        progress_id="lp-2",
        status="in_progress",
        created_at=now,
        created_by="student-1",
        updated_at=now,
        updated_by="student-1",
        version=2,
        started_at=now,
        completed_at=None,
        last_activity_at=now,
    )

    assert read_model.list_completed_lesson_ids(
        course_id="course-1",
        student_id="student-1",
    ) == ["lesson-1"]

    read_model.store_course_progress_summary(
        course_id="course-1",
        student_id="student-1",
        status="in_progress",
        progress_percent=50.0,
        completed_lessons=1,
        total_lessons=2,
        completed_at=None,
    )
    read_model.store_course_progress_summary(
        course_id="course-1",
        student_id="student-1",
        status="completed",
        progress_percent=100.0,
        completed_lessons=2,
        total_lessons=2,
        completed_at=now,
    )

    assert read_model.get_course_progress_summary(
        course_id="course-1",
        student_id="student-1",
    ) == ("completed", 100.0, 2, 2, now)
