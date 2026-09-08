# fastra_core\ai\enums.py

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Set

logger = logging.getLogger("fastra_core.ai.enums")


class AIComponent(str, Enum):
    """Katalog subsistem kecerdasan buatan utama dalam platform orkestrasi kognitif FASTRA."""
    VISION_AI = "VISION_AI"
    DRAWING_AI = "DRAWING_AI"
    LLM_ASSISTANT = "LLM_ASSISTANT"
    PREDICTION_AI = "PREDICTION_AI"


class VerificationStatus(str, Enum):
    """
    Status kepatuhan hasil evaluasi gerbang otomasi verifikasi kognitif (Verification Gate).
    Menentukan kelayakan payload inferensi AI sebelum dialirkan ke physical database layer.
    """
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"
    FLAGGED_HIGH_UNCERTAINTY = "FLAGGED_HIGH_UNCERTAINTY"
    FLAGGED_INCOMPLETE = "FLAGGED_INCOMPLETE"
    FLAGGED_INCONSISTENT = "FLAGGED_INCONSISTENT"


class ConfidenceFlag(str, Enum):
    """Penanda ambang batas tingkat kepastian (Confidence Threshold Boundary Flags) hasil inferensi model."""
    OK = "OK"
    HIGH_UNCERTAINTY = "HIGH_UNCERTAINTY"


class HumanReviewAction(str, Enum):
    """Ketetapan formal dari hasil intervensi penilai manual manusia (Human-In-The-Loop Validation)."""
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MODIFIED = "MODIFIED"


def validate_ai_enum_value(enum_class: Any, value: Any) -> str:
    """
    Fungsi penapis validasi nilai Enum lapisan kognitif AI secara fail-fast dan strict.
    Mengharamkan manipulasi token string kosong atau data zombie terselubung.
    """
    # Validate that enum_class is actually a subclass of Enum
    if not isinstance(enum_class, type) or not issubclass(enum_class, Enum):
        logger.error("VALIDATION_ERROR_TARGET_CLASS_MUST_BE_AN_ENUM: %r", enum_class)
        raise TypeError("VALIDATION_ERROR_TARGET_CLASS_MUST_BE_AN_ENUM")

    if not isinstance(value, str):
        logger.error(
            "VALUE_COERCION_FORBIDDEN_MUST_BE_A_PURE_STRING_GOT_%s: %r",
            type(value).__name__,
            value,
        )
        raise TypeError(f"VALUE_COERCION_FORBIDDEN_MUST_BE_A_PURE_STRING_GOT_{type(value).__name__}")

    clean_val = value.strip()
    if not clean_val:
        logger.error("EMPTY_OR_WHITESPACE_ENUM_VALUE_REJECTED")
        raise ValueError("ENUM_VALUE_CANNOT_BE_EMPTY_OR_WHITESPACE")

    allowed_values: Set[str] = {e.value for e in enum_class}

    if clean_val not in allowed_values:
        logger.error(
            "ILLEGAL_AI_ENUM_VALUE_VIOLATION: '%s' is not a valid member of %s. Allowed: %s",
            clean_val,
            enum_class.__name__,
            sorted(allowed_values),
        )
        raise ValueError(
            f"ILLEGAL_AI_ENUM_VALUE_VIOLATION: '{clean_val}' is not a valid member of "
            f"{enum_class.__name__}. Allowed members: {sorted(allowed_values)}"
        )

    return clean_val