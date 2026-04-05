from enum import StrEnum


class PublishState(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class AccessGrantStatus(StrEnum):
    REQUESTED = "requested"
    PAID = "paid"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVOKED = "revoked"


class EnrollmentStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELED = "canceled"


class SubmissionStatus(StrEnum):
    STARTED = "started"
    SUBMITTED = "submitted"
    GRADED = "graded"


class AttributionChannel(StrEnum):
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    ADS = "ads"
    PARTNER = "partner"
    OTHER = "other"
