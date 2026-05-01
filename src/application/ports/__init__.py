"""Порты application-слоя."""

"""Порты application слоя course_service."""

from src.application.ports.access_read_model import AccessReadModel
from src.application.ports.access_token_verifier import AccessTokenVerifier
from src.application.ports.clock import Clock
from src.application.ports.parent_student_relation_checker import (
    ParentStudentRelationChecker,
)
from src.application.ports.teacher_directory import TeacherDirectory, TeacherInfo

__all__ = [
    "AccessReadModel",
    "AccessTokenVerifier",
    "Clock",
    "ParentStudentRelationChecker",
    "TeacherDirectory",
    "TeacherInfo",
]
