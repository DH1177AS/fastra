# fastra_core\primitives\length.py

from __future__ import annotations

import logging
import math
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Union

from pydantic.dataclasses import dataclass

logger = logging.getLogger("fastra.primitives.length")


class LengthUnit(str, Enum):
    METERS = "m"
    MILLIMETERS = "mm"
    CENTIMETERS = "cm"
    KILOMETERS = "km"
    INCHES = "in"
    FEET = "ft"
    YARDS = "yd"


@dataclass(frozen=True)
class Length:
    value: Decimal
    unit: LengthUnit = LengthUnit.METERS

    def __post_init__(self) -> None:
        value = self.value
        if isinstance(value, bool):
            logger.error("LENGTH_VALUE_REJECTED_BOOLEAN: %r", value)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(value, (int, float, Decimal)):
            logger.error("LENGTH_VALUE_REJECTED_NON_NUMERIC: %r", value)
            raise TypeError("LENGTH_VALUE_MUST_BE_PURE_NUMERIC_TYPE")
        try:
            decimal_val = Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            logger.error("LENGTH_VALUE_INVALID_DECIMAL: %r", value)
            raise ValueError(f"INVALID_LENGTH_DECIMAL_REPRESENTATION: {value}") from exc
        if decimal_val.is_nan() or decimal_val.is_infinite():
            logger.error("LENGTH_VALUE_REJECTED_NAN_OR_INF: %s", decimal_val)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        if decimal_val < 0:
            logger.error("LENGTH_VALUE_REJECTED_NEGATIVE: %s", decimal_val)
            raise ValueError("LENGTH_VALUE_MUST_BE_NON_NEGATIVE")
        object.__setattr__(self, "value", decimal_val)
        object.__setattr__(self, "unit", self.unit)

    @classmethod
    def from_meters(cls, value: Union[int, float, Decimal]) -> "Length":
        return cls(value=value, unit=LengthUnit.METERS)

    @classmethod
    def from_millimeters(cls, mm: Any) -> "Length":
        if isinstance(mm, bool):
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(mm, (int, float, Decimal)):
            raise TypeError("LENGTH_VALUE_MUST_BE_PURE_NUMERIC_TYPE")
        decimal_val = Decimal(str(mm))
        if decimal_val.is_nan() or decimal_val.is_infinite():
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        if decimal_val < 0:
            raise ValueError("LENGTH_VALUE_MUST_BE_NON_NEGATIVE")
        return cls(value=decimal_val / Decimal("1000"), unit=LengthUnit.MILLIMETERS)

    @classmethod
    def from_centimeters(cls, cm: Any) -> "Length":
        if isinstance(cm, bool):
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(cm, (int, float, Decimal)):
            raise TypeError("LENGTH_VALUE_MUST_BE_PURE_NUMERIC_TYPE")
        decimal_val = Decimal(str(cm))
        if decimal_val.is_nan() or decimal_val.is_infinite():
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        if decimal_val < 0:
            raise ValueError("LENGTH_VALUE_MUST_BE_NON_NEGATIVE")
        return cls(value=decimal_val / Decimal("100"), unit=LengthUnit.CENTIMETERS)

    @classmethod
    def from_kilometers(cls, km: Any) -> "Length":
        if isinstance(km, bool):
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(km, (int, float, Decimal)):
            raise TypeError("LENGTH_VALUE_MUST_BE_PURE_NUMERIC_TYPE")
        decimal_val = Decimal(str(km))
        if decimal_val.is_nan() or decimal_val.is_infinite():
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        if decimal_val < 0:
            raise ValueError("LENGTH_VALUE_MUST_BE_NON_NEGATIVE")
        return cls(value=decimal_val * Decimal("1000"), unit=LengthUnit.KILOMETERS)

    @classmethod
    def from_inches(cls, inches: Any) -> "Length":
        if isinstance(inches, bool):
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(inches, (int, float, Decimal)):
            raise TypeError("LENGTH_VALUE_MUST_BE_PURE_NUMERIC_TYPE")
        decimal_val = Decimal(str(inches))
        if decimal_val.is_nan() or decimal_val.is_infinite():
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        if decimal_val < 0:
            raise ValueError("LENGTH_VALUE_MUST_BE_NON_NEGATIVE")
        return cls(value=decimal_val * Decimal("0.0254"), unit=LengthUnit.INCHES)

    @classmethod
    def from_feet(cls, feet: Any) -> "Length":
        if isinstance(feet, bool):
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(feet, (int, float, Decimal)):
            raise TypeError("LENGTH_VALUE_MUST_BE_PURE_NUMERIC_TYPE")
        decimal_val = Decimal(str(feet))
        if decimal_val.is_nan() or decimal_val.is_infinite():
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        if decimal_val < 0:
            raise ValueError("LENGTH_VALUE_MUST_BE_NON_NEGATIVE")
        return cls(value=decimal_val * Decimal("0.3048"), unit=LengthUnit.FEET)

    @classmethod
    def from_yards(cls, yards: Any) -> "Length":
        if isinstance(yards, bool):
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(yards, (int, float, Decimal)):
            raise TypeError("LENGTH_VALUE_MUST_BE_PURE_NUMERIC_TYPE")
        decimal_val = Decimal(str(yards))
        if decimal_val.is_nan() or decimal_val.is_infinite():
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        if decimal_val < 0:
            raise ValueError("LENGTH_VALUE_MUST_BE_NON_NEGATIVE")
        return cls(value=decimal_val * Decimal("0.9144"), unit=LengthUnit.YARDS)

    def to_meters(self) -> float:
        return float(self.value)

    def to_millimeters(self) -> float:
        return float(self.value * Decimal("1000"))

    def to_centimeters(self) -> float:
        return float(self.value * Decimal("100"))

    def to_kilometers(self) -> float:
        return float(self.value / Decimal("1000"))

    def to_inches(self) -> float:
        return float(self.value / Decimal("0.0254"))

    def to_feet(self) -> float:
        return float(self.value / Decimal("0.3048"))

    def to_yards(self) -> float:
        return float(self.value / Decimal("0.9144"))

    def approximately_equal(self, other: Any, epsilon: float = 1e-6) -> bool:
        if not isinstance(other, Length):
            return False
        try:
            eps = Decimal(str(epsilon))
        except (InvalidOperation, ValueError):
            return False
        return abs(self.value - other.value) <= eps

    def _coerce_other(self, other: Any) -> Decimal:
        if isinstance(other, Length):
            return other.value
        if isinstance(other, (int, float, Decimal)) and not isinstance(other, bool):
            return Decimal(str(other))
        raise TypeError("COMPARISON_OPERAND_MUST_BE_LENGTH_OR_NUMERIC")

    def __add__(self, other: Any) -> "Length":
        if not isinstance(other, Length):
            raise TypeError("OPERAND_MUST_BE_AN_INSTANCE_OF_LENGTH_CLASS")
        if self.unit != other.unit:
            raise ValueError("LENGTH_UNIT_MISMATCH_CANNOT_PERFORM_ARITHMETIC_OPERATIONS")
        return Length(value=self.value + other.value, unit=self.unit)

    def __sub__(self, other: Any) -> "Length":
        if not isinstance(other, Length):
            raise TypeError("OPERAND_MUST_BE_AN_INSTANCE_OF_LENGTH_CLASS")
        if self.unit != other.unit:
            raise ValueError("LENGTH_UNIT_MISMATCH_CANNOT_PERFORM_ARITHMETIC_OPERATIONS")
        result = self.value - other.value
        if result < 0:
            raise ValueError("LENGTH_SUBTRACTION_RESULT_CANNOT_BE_NEGATIVE")
        return Length(value=result, unit=self.unit)

    def __mul__(self, scalar: Any) -> "Length":
        if isinstance(scalar, bool):
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(scalar, (int, float, Decimal)):
            raise TypeError("SCALAR_MUST_BE_A_PURE_NUMERIC_TYPE")
        decimal_scalar = Decimal(str(scalar))
        if decimal_scalar.is_nan() or decimal_scalar.is_infinite():
            raise ValueError("NUMERIC_ANOMALY_DETECTED_SCALAR_CANNOT_BE_NAN_OR_INFINITE")
        result = self.value * decimal_scalar
        if result < 0:
            raise ValueError("LENGTH_MULTIPLICATION_RESULT_CANNOT_BE_NEGATIVE")
        return Length(value=result, unit=self.unit)

    def __rmul__(self, scalar: Any) -> "Length":
        return self.__mul__(scalar)

    def __truediv__(self, scalar: Any) -> "Length":
        if isinstance(scalar, bool):
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(scalar, (int, float, Decimal)):
            raise TypeError("SCALAR_MUST_BE_A_PURE_NUMERIC_TYPE")
        decimal_scalar = Decimal(str(scalar))
        if decimal_scalar == 0:
            raise ZeroDivisionError("DIVISION_BY_ZERO_PROHIBITED")
        if decimal_scalar.is_nan() or decimal_scalar.is_infinite():
            raise ValueError("NUMERIC_ANOMALY_DETECTED_SCALAR_CANNOT_BE_NAN_OR_INFINITE")
        result = self.value / decimal_scalar
        if result < 0:
            raise ValueError("LENGTH_DIVISION_RESULT_CANNOT_BE_NEGATIVE")
        return Length(value=result, unit=self.unit)

    def __eq__(self, other: Any) -> bool:
        try:
            other_val = self._coerce_other(other)
        except TypeError:
            return False
        return self.value == other_val

    def __lt__(self, other: Any) -> bool:
        other_val = self._coerce_other(other)
        return self.value < other_val

    def __le__(self, other: Any) -> bool:
        other_val = self._coerce_other(other)
        return self.value <= other_val

    def __gt__(self, other: Any) -> bool:
        other_val = self._coerce_other(other)
        return self.value > other_val

    def __ge__(self, other: Any) -> bool:
        other_val = self._coerce_other(other)
        return self.value >= other_val

    def __str__(self) -> str:
        return f"{self.value} {self.unit.value}"

    def __repr__(self) -> str:
        return f"Length({self.value} {self.unit.value})"