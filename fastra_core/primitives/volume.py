# fastra_core\primitives\volume.py

from __future__ import annotations

import logging
import math
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator
from decimal import Decimal, InvalidOperation

logger = logging.getLogger("fastra.primitives.volume")


class VolumeUnit(str, Enum):
   
    CUBIC_METERS = "m³"
    LITERS = "L"


class Volume(BaseModel):
   
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
                raise TypeError("Volume only accepts a single positional argument for value")
            kwargs.setdefault("value", args[0])
        super().__init__(**kwargs)

    value: float = Field(..., description="Besaran volume dalam satuan Meter Kubik (m³)")
    unit: VolumeUnit = Field(default=VolumeUnit.CUBIC_METERS, description="Satuan awal input data")

    @field_validator("value", mode="before")
    @classmethod
    def validate_numeric_no_coercion(cls, value: Any) -> float:
        if isinstance(value, bool):
            logger.error("VOLUME_VALUE_REJECTED_BOOLEAN: %r", value)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if isinstance(value, Decimal):
            value = float(value)
        if not isinstance(value, (int, float)):
            logger.error("VOLUME_VALUE_REJECTED_NON_NUMERIC: %r", value)
            raise TypeError("VOLUME_VALUE_MUST_BE_PURE_NUMERIC_TYPE")
        float_val = float(value)
        if math.isnan(float_val) or math.isinf(float_val):
            logger.error("VOLUME_VALUE_REJECTED_NAN_OR_INF: %s", float_val)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        if float_val < 0.0:
            logger.error("VOLUME_VALUE_REJECTED_NEGATIVE: %s", float_val)
            raise ValueError("VOLUME_VALUE_MUST_BE_NON_NEGATIVE")
        return float_val

    @classmethod
    def from_liters(cls, l: Any) -> "Volume":
        """Named constructor untuk instansiasi Volume murni dari satuan Liter (L)."""
        if isinstance(l, bool):
            logger.error("VOLUME_FROM_LITERS_REJECTED_BOOLEAN: %r", l)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(l, (int, float)):
            logger.error("VOLUME_FROM_LITERS_REJECTED_NON_NUMERIC: %r", l)
            raise TypeError("VOLUME_VALUE_MUST_BE_PURE_NUMERIC_TYPE")
        float_val = float(l)
        if math.isnan(float_val) or math.isinf(float_val):
            logger.error("VOLUME_FROM_LITERS_REJECTED_NAN_OR_INF: %s", float_val)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        if float_val < 0.0:
            logger.error("VOLUME_FROM_LITERS_REJECTED_NEGATIVE: %s", float_val)
            raise ValueError(f"QUANTITY_CONSTRAINT_VIOLATION_VOLUME_CANNOT_BE_NEGATIVE: {float_val}")
        return cls(value=float_val * 0.001, unit=VolumeUnit.LITERS)

    def to_liters(self) -> float:
        return self.value * 1000.0

    def approximately_equal(self, other: Any, epsilon: float = 1e-9) -> bool:
        if not isinstance(other, Volume):
            return False
        return abs(self.value - other.value) <= epsilon

    def __add__(self, other: Any) -> "Volume":
        if not isinstance(other, Volume):
            logger.error("VOLUME_ADD_REJECTED_NON_VOLUME: %r", other)
            raise TypeError("OPERAND_MUST_BE_AN_INSTANCE_OF_VOLUME_CLASS")
        return Volume(value=self.value + other.value, unit=VolumeUnit.CUBIC_METERS)

    def __sub__(self, other: Any) -> "Volume":
        if not isinstance(other, Volume):
            logger.error("VOLUME_SUB_REJECTED_NON_VOLUME: %r", other)
            raise TypeError("OPERAND_MUST_BE_AN_INSTANCE_OF_VOLUME_CLASS")
        result = self.value - other.value
        if result < 0.0:
            logger.error("VOLUME_SUB_RESULT_NEGATIVE: %s", result)
            raise ValueError(f"QUANTITY_CONSTRAINT_VIOLATION_SUBTRACTION_RESULT_CANNOT_BE_NEGATIVE: {result}")
        return Volume(value=result, unit=VolumeUnit.CUBIC_METERS)

    def __mul__(self, scalar: Any) -> "Volume":
        if isinstance(scalar, bool):
            logger.error("VOLUME_MUL_REJECTED_BOOLEAN: %r", scalar)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(scalar, (int, float)):
            logger.error("VOLUME_MUL_REJECTED_NON_NUMERIC: %r", scalar)
            raise TypeError("SCALAR_MUST_BE_A_PURE_NUMERIC_TYPE")
        float_scalar = float(scalar)
        if math.isnan(float_scalar) or math.isinf(float_scalar):
            logger.error("VOLUME_MUL_REJECTED_NAN_OR_INF: %s", float_scalar)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        result = self.value * float_scalar
        if result < 0.0:
            logger.error("VOLUME_MUL_RESULT_NEGATIVE: %s", result)
            raise ValueError(f"QUANTITY_CONSTRAINT_VIOLATION_MULTIPLICATION_RESULT_CANNOT_BE_NEGATIVE: {result}")
        return Volume(value=result, unit=VolumeUnit.CUBIC_METERS)

    def __rmul__(self, scalar: Any) -> "Volume":
        return self.__mul__(scalar)

    def __truediv__(self, scalar: Any) -> "Volume":
        if isinstance(scalar, bool):
            logger.error("VOLUME_DIV_REJECTED_BOOLEAN: %r", scalar)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(scalar, (int, float)):
            logger.error("VOLUME_DIV_REJECTED_NON_NUMERIC: %r", scalar)
            raise TypeError("SCALAR_MUST_BE_A_PURE_NUMERIC_TYPE")
        float_scalar = float(scalar)
        if float_scalar == 0.0:
            logger.error("VOLUME_DIV_BY_ZERO")
            raise ZeroDivisionError("DIVISION_BY_ZERO_PROHIBITED")
        if math.isnan(float_scalar) or math.isinf(float_scalar):
            logger.error("VOLUME_DIV_REJECTED_NAN_OR_INF: %s", float_scalar)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        result = self.value / float_scalar
        if result < 0.0:
            logger.error("VOLUME_DIV_RESULT_NEGATIVE: %s", result)
            raise ValueError(f"QUANTITY_CONSTRAINT_VIOLATION_DIVISION_RESULT_CANNOT_BE_NEGATIVE: {result}")
        return Volume(value=result, unit=VolumeUnit.CUBIC_METERS)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Volume):
            return False
        return self.value == other.value

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Volume):
            logger.error("VOLUME_COMPARE_REJECTED_NON_VOLUME: %r", other)
            raise TypeError("COMPARISON_OPERAND_MUST_BE_AN_INSTANCE_OF_VOLUME_CLASS")
        return self.value < other.value

    def __le__(self, other: Any) -> bool:
        if not isinstance(other, Volume):
            logger.error("VOLUME_COMPARE_REJECTED_NON_VOLUME: %r", other)
            raise TypeError("COMPARISON_OPERAND_MUST_BE_AN_INSTANCE_OF_VOLUME_CLASS")
        return self.value <= other.value

    def __gt__(self, other: Any) -> bool:
        if not isinstance(other, Volume):
            logger.error("VOLUME_COMPARE_REJECTED_NON_VOLUME: %r", other)
            raise TypeError("COMPARISON_OPERAND_MUST_BE_AN_INSTANCE_OF_VOLUME_CLASS")
        return self.value > other.value

    def __ge__(self, other: Any) -> bool:
        if not isinstance(other, Volume):
            logger.error("VOLUME_COMPARE_REJECTED_NON_VOLUME: %r", other)
            raise TypeError("COMPARISON_OPERAND_MUST_BE_AN_INSTANCE_OF_VOLUME_CLASS")
        return self.value >= other.value

    def __str__(self) -> str:
        return f"{self.value} m³"

    def __repr__(self) -> str:
        return f"Volume({self.value})"