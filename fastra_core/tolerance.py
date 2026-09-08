# fastra_core\tolerance.py

from __future__ import annotations

import logging
import math
from typing import Any

from pydantic import BaseModel, ConfigDict

logger = logging.getLogger("fastra_core.tolerance")

# Immutable Global Configuration Constants Matrix
EPSILON_LENGTH: float = 1e-6
EPSILON_AREA: float = 1e-6
EPSILON_VOLUME: float = 1e-9
EPSILON_ANGLE: float = 1e-9
EPSILON_CURRENCY: float = 0.5
EPSILON_DEFAULT: float = 1e-6


class ToleranceGuard(BaseModel):
    """
    Engine Pengaman Batas Toleransi Spasial dan Finansial (Tolerance Guard Engine).
    Menjamin stabilitas komparasi aljabar dari manipulasi data mengambang rusak.
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    @classmethod
    def _validate_numeric_no_coercion(cls, val: Any, name: str) -> float:
        """Validasi numerik murni dengan penolakan coercion dan anomali float."""
        if isinstance(val, bool):
            logger.error("TOLERANCE_%s_BOOLEAN_REJECTED: %r", name.upper(), val)
            raise TypeError(f"DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED_AT_{name.upper()}")
        if not isinstance(val, (int, float)):
            logger.error("TOLERANCE_%s_NON_NUMERIC_REJECTED: %r", name.upper(), val)
            raise TypeError(f"VALUE_FOR_{name.upper()}_MUST_BE_PURE_NUMERIC_TYPE")
        float_val = float(val)
        if math.isnan(float_val) or math.isinf(float_val):
            logger.error("TOLERANCE_%s_NAN_OR_INF_REJECTED: %s", name.upper(), float_val)
            raise ValueError(
                f"NUMERIC_ANOMALY_DETECTED_VALUE_FOR_{name.upper()}_CANNOT_BE_NAN_OR_INFINITE"
            )
        return float_val

    @classmethod
    def approximately_equal(cls, a: Any, b: Any, epsilon: Any = EPSILON_DEFAULT) -> bool:
        """
        Memverifikasi kesamaan nilai keuangan atau spasial berdasarkan batas toleransi epsilon.
        """
        clean_a = cls._validate_numeric_no_coercion(a, "a")
        clean_b = cls._validate_numeric_no_coercion(b, "b")
        clean_epsilon = cls._validate_numeric_no_coercion(epsilon, "epsilon")

        if clean_epsilon < 0.0:
            logger.error("TOLERANCE_EPSILON_NEGATIVE_REJECTED: %s", clean_epsilon)
            raise ValueError("TOLERANCE_CONSTRAINT_VIOLATION_EPSILON_CANNOT_BE_NEGATIVE")

        result = abs(clean_a - clean_b) <= clean_epsilon
        logger.debug("approximately_equal(a=%s, b=%s, eps=%s) -> %s", clean_a, clean_b, clean_epsilon, result)
        return result

    @classmethod
    def approximately_greater(cls, a: Any, b: Any, epsilon: Any = EPSILON_DEFAULT) -> bool:
        """
        Memverifikasi apakah nilai A secara hampiran lebih besar dari nilai B (A >= B - Epsilon).
        """
        clean_a = cls._validate_numeric_no_coercion(a, "a")
        clean_b = cls._validate_numeric_no_coercion(b, "b")
        clean_epsilon = cls._validate_numeric_no_coercion(epsilon, "epsilon")

        if clean_epsilon < 0.0:
            logger.error("TOLERANCE_EPSILON_NEGATIVE_REJECTED: %s", clean_epsilon)
            raise ValueError("TOLERANCE_CONSTRAINT_VIOLATION_EPSILON_CANNOT_BE_NEGATIVE")

        result = clean_a > (clean_b - clean_epsilon)
        logger.debug("approximately_greater(a=%s, b=%s, eps=%s) -> %s", clean_a, clean_b, clean_epsilon, result)
        return result

    @classmethod
    def approximately_less(cls, a: Any, b: Any, epsilon: Any = EPSILON_DEFAULT) -> bool:
        """
        Memverifikasi apakah nilai A secara hampiran lebih kecil dari nilai B (A <= B + Epsilon).
        """
        clean_a = cls._validate_numeric_no_coercion(a, "a")
        clean_b = cls._validate_numeric_no_coercion(b, "b")
        clean_epsilon = cls._validate_numeric_no_coercion(epsilon, "epsilon")

        if clean_epsilon < 0.0:
            logger.error("TOLERANCE_EPSILON_NEGATIVE_REJECTED: %s", clean_epsilon)
            raise ValueError("TOLERANCE_CONSTRAINT_VIOLATION_EPSILON_CANNOT_BE_NEGATIVE")

        result = clean_a < (clean_b + clean_epsilon)
        logger.debug("approximately_less(a=%s, b=%s, eps=%s) -> %s", clean_a, clean_b, clean_epsilon, result)
        return result


# Expose fungsionalitas fungsional tingkat modul demi kompatibilitas hulu
def approximately_equal(a: Any, b: Any, epsilon: Any = EPSILON_DEFAULT) -> bool:
    """Wrapper fungsional untuk komparasi hampiran sama."""
    return ToleranceGuard.approximately_equal(a, b, epsilon)


def approximately_greater(a: Any, b: Any, epsilon: Any = EPSILON_DEFAULT) -> bool:
    """Wrapper fungsional untuk komparasi hampiran lebih besar."""
    return ToleranceGuard.approximately_greater(a, b, epsilon)


def approximately_less(a: Any, b: Any, epsilon: Any = EPSILON_DEFAULT) -> bool:
    """Wrapper fungsional untuk komparasi hampiran lebih kecil."""
    return ToleranceGuard.approximately_less(a, b, epsilon)