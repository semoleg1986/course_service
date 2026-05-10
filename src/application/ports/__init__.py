"""Порты application-слоя."""

"""Порты application слоя course_service."""

from src.application.ports.access_read_model import AccessReadModel
from src.application.ports.access_token_verifier import AccessTokenVerifier
from src.application.ports.audit_evidence import (
    AuditEvidenceRecord,
    AuditEvidenceRepository,
)
from src.application.ports.bonus_wallet import BonusWalletPort
from src.application.ports.clock import Clock
from src.application.ports.parent_student_relation_checker import (
    ParentStudentRelationChecker,
)
from src.application.ports.student_parent_directory import StudentParentDirectory
from src.application.ports.teacher_directory import TeacherDirectory, TeacherInfo

__all__ = [
    "AccessReadModel",
    "AuditEvidenceRecord",
    "AuditEvidenceRepository",
    "AccessTokenVerifier",
    "BonusWalletPort",
    "Clock",
    "ParentStudentRelationChecker",
    "StudentParentDirectory",
    "TeacherDirectory",
    "TeacherInfo",
]
