# fastra_core\digital_twin\enums.py

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Set

logger = logging.getLogger("fastra_core.digital_twin.enums")


class SnapshotType(str, Enum):
    """Katalog klasifikasi jenis penanda checkpoint keadaan (Snapshot) Digital Twin."""
    BASELINE = "BASELINE"
    CHECKPOINT = "CHECKPOINT"
    EVENT = "EVENT"
    PROGRESS = "PROGRESS"
    AS_BUILT = "AS_BUILT"


class ReportType(str, Enum):
    """Siklus periodik penerbitan lembar laporan progres konstruksi lapangan."""
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class ProgressStatus(str, Enum):
    """Status tahapan realisasi fisik dari item elemen pekerjaan / objek konstruksi."""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    DELAYED = "DELAYED"


class IssueSeverity(str, Enum):
    """Tingkat kritis dampak kegagalan/kendala penemuan masalah (Field Issues) di lapangan."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IssueStatus(str, Enum):
    """Status penanganan penyelesaian kendala konstruksi lapangan."""
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class VOStatus(str, Enum):
    """Alur tata kelola siklus dokumen Perintah Perubahan Kerja / Variation Order (VO)."""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ApprovalStatus(str, Enum):
    """Status ketetapan formal dari simpul mata rantai otorisasi (Approval Chain Node)."""
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class EventType(str, Enum):
    """Katalog identitas peristiwa perubahan state transaksional penapis Audit Trail Ledger."""
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


def validate_enum_value(enum_class: Any, value: Any) -> str:
    """
    Fungsi penapis validasi nilai Enum secara fail-fast dan strict.
    Mengharamkan manipulasi token string kosong atau data zombie terselubung.
    """
    if not isinstance(enum_class, type) or not issubclass(enum_class, Enum):
        logger.error("VALIDATION_ERROR_TARGET_CLASS_MUST_BE_AN_ENUM: %r", enum_class)
        raise TypeError("VALIDATION_ERROR_TARGET_CLASS_MUST_BE_AN_ENUM")

    if not isinstance(value, str):
        logger.error("VALUE_COERCION_FORBIDDEN_MUST_BE_A_PURE_STRING_GOT_%s: %r", type(value).__name__, value)
        raise TypeError(f"VALUE_COERCION_FORBIDDEN_MUST_BE_A_PURE_STRING_GOT_{type(value).__name__}")

    clean_val = value.strip()
    allowed_values: Set[str] = {e.value for e in enum_class}

    if clean_val not in allowed_values:
        logger.error(
            "ILLEGAL_ENUM_VALUE_VIOLATION: '%s' not in %s",
            clean_val,
            sorted(allowed_values),
        )
        raise ValueError(
            f"ILLEGAL_ENUM_VALUE_VIOLATION: '{clean_val}' is not a valid member of "
            f"{enum_class.__name__}. Allowed members: {sorted(allowed_values)}"
        )

    return clean_val