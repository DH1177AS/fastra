"""
ACES-600 Digital Twin Enums
Menstandarkan semua nilai status, tipe, dan severity.
"""
from enum import Enum


class SnapshotType(str, Enum):
    BASELINE = "BASELINE"
    CHECKPOINT = "CHECKPOINT"
    EVENT = "EVENT"
    PROGRESS = "PROGRESS"
    AS_BUILT = "AS_BUILT"


class ReportType(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class ProgressStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    DELAYED = "DELAYED"


class IssueSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IssueStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class VOStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ApprovalStatus(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class EventType(str, Enum):
    ENTITY_CREATED = "ENTITY_CREATED"
    ENTITY_MODIFIED = "ENTITY_MODIFIED"
    ENTITY_DELETED = "ENTITY_DELETED"
    VO_CREATED = "VO_CREATED"
    VO_APPROVED = "VO_APPROVED"
    VO_REJECTED = "VO_REJECTED"
    SNAPSHOT_CREATED = "SNAPSHOT_CREATED"
    PROGRESS_REPORTED = "PROGRESS_REPORTED"
    PROJECT_COMPLETED = "PROJECT_COMPLETED"
    ARCHIVE_CREATED = "ARCHIVE_CREATED"
    RESTORE_EXECUTED = "RESTORE_EXECUTED"
