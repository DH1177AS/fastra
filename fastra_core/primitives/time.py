# fastra_core\primitives\time.py

from __future__ import annotations

import logging
import math
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra.primitives.time")


class TimeUnit(str, Enum):
    """
    Strict Enum untuk satuan durasi waktu operasional scheduling / scheduling QS.
    Menghilangkan manipulasi paksa (coercion hack) tipe string bebas.
    """
    SECONDS = "s"
    MINUTES = "m"
    HOURS = "h"
    DAYS = "d"


class Time(BaseModel):
    """
    Primitive Value Object untuk merepresentasikan besaran Durasi Waktu (Time).
    Menggunakan Pydantic sebagai validator tunggal dengan mode strict fail-fast.
    Seluruh nilai internal disimpan secara absolut dalam satuan Detik (s).
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    def __init__(self, *args, **kwargs):
        if args:
            if len(args) > 1:
                raise TypeError("Time only accepts a single positional argument for value")
            kwargs.setdefault("value", args[0])
        super().__init__(**kwargs)

    value: float = Field(..., description="Besaran durasi waktu dalam satuan Detik (s)")
    unit: TimeUnit = Field(default=TimeUnit.SECONDS, description="Satuan awal input data")

    @field_validator("value", mode="before")
    @classmethod
    def validate_numeric_no_coercion(cls, value: Any) -> float:
        if isinstance(value, bool):
            logger.error("TIME_VALUE_REJECTED_BOOLEAN: %r", value)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(value, (int, float)):
            logger.error("TIME_VALUE_REJECTED_NON_NUMERIC: %r", value)
            raise TypeError("TIME_VALUE_MUST_BE_PURE_NUMERIC_TYPE")
        float_val = float(value)
        if math.isnan(float_val) or math.isinf(float_val):
            logger.error("TIME_VALUE_REJECTED_NAN_OR_INF: %s", float_val)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        if float_val < 0.0:
            logger.error("TIME_VALUE_REJECTED_NEGATIVE: %s", float_val)
            raise ValueError(f"QUANTITY_CONSTRAINT_VIOLATION_TIME_DURATION_CANNOT_BE_NEGATIVE: {float_val}")
        return float_val

    @classmethod
    def from_minutes(cls, m: Any) -> "Time":
        """Named constructor untuk instansiasi Waktu murni dari menit (m)."""
        if isinstance(m, bool):
            logger.error("TIME_FROM_MINUTES_REJECTED_BOOLEAN: %r", m)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(m, (int, float)):
            logger.error("TIME_FROM_MINUTES_REJECTED_NON_NUMERIC: %r", m)
            raise TypeError("TIME_VALUE_MUST_BE_PURE_NUMERIC_TYPE")
        float_val = float(m)
        if math.isnan(float_val) or math.isinf(float_val):
            logger.error("TIME_FROM_MINUTES_REJECTED_NAN_OR_INF: %s", float_val)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        if float_val < 0.0:
            logger.error("TIME_FROM_MINUTES_REJECTED_NEGATIVE: %s", float_val)
            raise ValueError(f"QUANTITY_CONSTRAINT_VIOLATION_TIME_DURATION_CANNOT_BE_NEGATIVE: {float_val}")
        return cls(value=float_val * 60.0, unit=TimeUnit.MINUTES)

    @classmethod
    def from_hours(cls, h: Any) -> "Time":
        """Named constructor untuk instansiasi Waktu murni dari jam (h)."""
        if isinstance(h, bool):
            logger.error("TIME_FROM_HOURS_REJECTED_BOOLEAN: %r", h)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(h, (int, float)):
            logger.error("TIME_FROM_HOURS_REJECTED_NON_NUMERIC: %r", h)
            raise TypeError("TIME_VALUE_MUST_BE_PURE_NUMERIC_TYPE")
        float_val = float(h)
        if math.isnan(float_val) or math.isinf(float_val):
            logger.error("TIME_FROM_HOURS_REJECTED_NAN_OR_INF: %s", float_val)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        if float_val < 0.0:
            logger.error("TIME_FROM_HOURS_REJECTED_NEGATIVE: %s", float_val)
            raise ValueError(f"QUANTITY_CONSTRAINT_VIOLATION_TIME_DURATION_CANNOT_BE_NEGATIVE: {float_val}")
        return cls(value=float_val * 3600.0, unit=TimeUnit.HOURS)

    @classmethod
    def from_days(cls, d: Any) -> "Time":
        """Named constructor untuk instansiasi Waktu murni dari hari (d)."""
        if isinstance(d, bool):
            logger.error("TIME_FROM_DAYS_REJECTED_BOOLEAN: %r", d)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(d, (int, float)):
            logger.error("TIME_FROM_DAYS_REJECTED_NON_NUMERIC: %r", d)
            raise TypeError("TIME_VALUE_MUST_BE_PURE_NUMERIC_TYPE")
        float_val = float(d)
        if math.isnan(float_val) or math.isinf(float_val):
            logger.error("TIME_FROM_DAYS_REJECTED_NAN_OR_INF: %s", float_val)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        if float_val < 0.0:
            logger.error("TIME_FROM_DAYS_REJECTED_NEGATIVE: %s", float_val)
            raise ValueError(f"QUANTITY_CONSTRAINT_VIOLATION_TIME_DURATION_CANNOT_BE_NEGATIVE: {float_val}")
        return cls(value=float_val * 86400.0, unit=TimeUnit.DAYS)

    def to_minutes(self) -> float:
        return self.value / 60.0

    def to_hours(self) -> float:
        return self.value / 3600.0

    def to_days(self) -> float:
        return self.value / 86400.0

    def approximately_equal(self, other: Any, epsilon: float = 1e-6) -> bool:
        if not isinstance(other, Time):
            return False
        return abs(self.value - other.value) <= epsilon

    def __add__(self, other: Any) -> "Time":
        if not isinstance(other, Time):
            logger.error("TIME_ADD_REJECTED_NON_TIME: %r", other)
            raise TypeError("OPERAND_MUST_BE_AN_INSTANCE_OF_TIME_CLASS")
        return Time(value=self.value + other.value, unit=TimeUnit.SECONDS)

    def __sub__(self, other: Any) -> "Time":
        if not isinstance(other, Time):
            logger.error("TIME_SUB_REJECTED_NON_TIME: %r", other)
            raise TypeError("OPERAND_MUST_BE_AN_INSTANCE_OF_TIME_CLASS")
        result = self.value - other.value
        if result < 0.0:
            logger.error("TIME_SUB_RESULT_NEGATIVE: %s", result)
            raise ValueError(f"QUANTITY_CONSTRAINT_VIOLATION_SUBTRACTION_RESULT_CANNOT_BE_NEGATIVE: {result}")
        return Time(value=result, unit=TimeUnit.SECONDS)

    def __mul__(self, scalar: Any) -> "Time":
        if isinstance(scalar, bool):
            logger.error("TIME_MUL_REJECTED_BOOLEAN: %r", scalar)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(scalar, (int, float)):
            logger.error("TIME_MUL_REJECTED_NON_NUMERIC: %r", scalar)
            raise TypeError("SCALAR_MUST_BE_A_PURE_NUMERIC_TYPE")
        float_scalar = float(scalar)
        if math.isnan(float_scalar) or math.isinf(float_scalar):
            logger.error("TIME_MUL_REJECTED_NAN_OR_INF: %s", float_scalar)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        result = self.value * float_scalar
        if result < 0.0:
            logger.error("TIME_MUL_RESULT_NEGATIVE: %s", result)
            raise ValueError(f"QUANTITY_CONSTRAINT_VIOLATION_MULTIPLICATION_RESULT_CANNOT_BE_NEGATIVE: {result}")
        return Time(value=result, unit=TimeUnit.SECONDS)

    def __rmul__(self, scalar: Any) -> "Time":
        return self.__mul__(scalar)

    def __truediv__(self, scalar: Any) -> "Time":
        if isinstance(scalar, bool):
            logger.error("TIME_DIV_REJECTED_BOOLEAN: %r", scalar)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(scalar, (int, float)):
            logger.error("TIME_DIV_REJECTED_NON_NUMERIC: %r", scalar)
            raise TypeError("SCALAR_MUST_BE_A_PURE_NUMERIC_TYPE")
        float_scalar = float(scalar)
        if float_scalar == 0.0:
            logger.error("TIME_DIV_BY_ZERO")
            raise ZeroDivisionError("DIVISION_BY_ZERO_PROHIBITED")
        if math.isnan(float_scalar) or math.isinf(float_scalar):
            logger.error("TIME_DIV_REJECTED_NAN_OR_INF: %s", float_scalar)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        result = self.value / float_scalar
        if result < 0.0:
            logger.error("TIME_DIV_RESULT_NEGATIVE: %s", result)
            raise ValueError(f"QUANTITY_CONSTRAINT_VIOLATION_DIVISION_RESULT_CANNOT_BE_NEGATIVE: {result}")
        return Time(value=result, unit=TimeUnit.SECONDS)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Time):
            return False
        return self.value == other.value

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Time):
            logger.error("TIME_COMPARE_REJECTED_NON_TIME: %r", other)
            raise TypeError("COMPARISON_OPERAND_MUST_BE_AN_INSTANCE_OF_TIME_CLASS")
        return self.value < other.value

    def __le__(self, other: Any) -> bool:
        if not isinstance(other, Time):
            logger.error("TIME_COMPARE_REJECTED_NON_TIME: %r", other)
            raise TypeError("COMPARISON_OPERAND_MUST_BE_AN_INSTANCE_OF_TIME_CLASS")
        return self.value <= other.value

    def __gt__(self, other: Any) -> bool:
        if not isinstance(other, Time):
            logger.error("TIME_COMPARE_REJECTED_NON_TIME: %r", other)
            raise TypeError("COMPARISON_OPERAND_MUST_BE_AN_INSTANCE_OF_TIME_CLASS")
        return self.value > other.value

    def __ge__(self, other: Any) -> bool:
        if not isinstance(other, Time):
            logger.error("TIME_COMPARE_REJECTED_NON_TIME: %r", other)
            raise TypeError("COMPARISON_OPERAND_MUST_BE_AN_INSTANCE_OF_TIME_CLASS")
        return self.value >= other.value

    def __str__(self) -> str:
        return f"{self.to_hours():.2f} jam"

    def __repr__(self) -> str:
        return f"Time({self.value})"