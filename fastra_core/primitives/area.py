# fastra_core\primitives\area.py

from __future__ import annotations

import enum
import logging
import math
from decimal import Decimal, InvalidOperation
from typing import Any, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra.primitives.area")


class AreaUnit(str, enum.Enum):
    SQUARE_METER = "m²"
    SQUARE_CENTIMETER = "cm²"
    SQUARE_KILOMETER = "km²"
    HECTARE = "ha"
    ARE = "are"


class Area(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    value: float = Field(..., ge=0.0)
    unit: AreaUnit = Field(default=AreaUnit.SQUARE_METER)

    def __init__(self, value: Any, unit: AreaUnit = AreaUnit.SQUARE_METER):
        super().__init__(value=value, unit=unit)

    @field_validator("value", mode="before")
    @classmethod
    def validate_value(cls, v: Any) -> float:
        if isinstance(v, bool):
            logger.error("AREA_VALUE_REJECTED_BOOLEAN: %r", v)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if isinstance(v, Decimal):
            v = float(v)
        if not isinstance(v, (int, float)):
            logger.error("AREA_VALUE_REJECTED_NON_NUMERIC: %r", v)
            raise TypeError("AREA_VALUE_MUST_BE_PURE_NUMERIC_TYPE")
        float_v = float(v)
        if math.isnan(float_v) or math.isinf(float_v):
            logger.error("AREA_VALUE_REJECTED_NAN_OR_INF: %s", float_v)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        if float_v < 0:
            logger.error("AREA_VALUE_REJECTED_NEGATIVE: %s", float_v)
            raise ValueError("AREA_VALUE_MUST_BE_NON_NEGATIVE")
        return float_v

    @classmethod
    def from_square_centimeters(cls, value: Union[int, float, Decimal]) -> "Area":
        if isinstance(value, bool):
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(value, (int, float, Decimal)):
            raise TypeError("AREA_VALUE_MUST_BE_PURE_NUMERIC_TYPE")
        decimal_val = Decimal(str(value))
        if decimal_val.is_nan() or decimal_val.is_infinite():
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        if decimal_val < 0:
            raise ValueError("AREA_VALUE_MUST_BE_NON_NEGATIVE")
        m2 = float(decimal_val / Decimal("10000"))
        return cls(value=m2, unit=AreaUnit.SQUARE_METER)

    def to_square_meters(self) -> float:
        return self.value

    def to_square_centimeters(self) -> float:
        if self.unit == AreaUnit.SQUARE_CENTIMETER:
            return self.value
        return self.value * 10000.0

    def __add__(self, other: Any) -> "Area":
        if not isinstance(other, Area):
            logger.error("AREA_ADD_REJECTED_NON_AREA: %r", other)
            raise TypeError("OPERAND_MUST_BE_AN_INSTANCE_OF_AREA_CLASS")
        if self.unit != other.unit:
            logger.error("AREA_ADD_UNIT_MISMATCH: %s vs %s", self.unit.value, other.unit.value)
            raise ValueError("AREA_UNIT_MISMATCH_CANNOT_PERFORM_ARITHMETIC_OPERATIONS")
        return Area(value=self.value + other.value, unit=self.unit)

    def __mul__(self, scalar: Any) -> "Area":
        if isinstance(scalar, bool):
            logger.error("AREA_MUL_REJECTED_BOOLEAN: %r", scalar)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(scalar, (int, float, Decimal)):
            logger.error("AREA_MUL_REJECTED_INVALID_TYPE: %r", scalar)
            raise TypeError("SCALAR_MULTIPLIER_MUST_BE_INT_FLOAT_OR_DECIMAL")
        decimal_scalar = Decimal(str(scalar))
        if decimal_scalar.is_nan() or decimal_scalar.is_infinite():
            logger.error("AREA_MUL_SCALAR_NAN_OR_INF: %s", decimal_scalar)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_SCALAR_CANNOT_BE_NAN_OR_INFINITE")
        result = self.value * float(decimal_scalar)
        return Area(value=result, unit=self.unit)

    def __rmul__(self, scalar: Any) -> "Area":
        return self.__mul__(scalar)

    def approximately_equal(self, other: Any, epsilon: float = 1e-6) -> bool:
        if not isinstance(other, Area):
            return False
        return abs(self.value - other.value) <= epsilon

    def __str__(self) -> str:
        return f"{self.value} {self.unit.value}"

    def __repr__(self) -> str:
        return f"Area({self.value} {self.unit.value})"