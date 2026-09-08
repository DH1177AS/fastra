# fastra_core\primitives\mass.py

from __future__ import annotations

import logging
import math
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra.primitives.mass")


class MassUnit(str, Enum):
    """
    Strict Enum untuk satuan ukuran massa/berat material konstruksi (baja, agregat, semen).
    Menghilangkan manipulasi paksa (coercion hack) tipe string bebas.
    """
    KILOGRAMS = "kg"
    GRAMS = "g"
    METRIC_TONS = "t"


class Mass(BaseModel):
    """
    Primitive Value Object untuk merepresentasikan besaran Massa/Berat (Mass).
    Menggunakan Pydantic sebagai validator tunggal dengan mode strict fail-fast.
    Seluruh nilai internal disimpan secara absolut dalam satuan Kilogram (kg).
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
                raise TypeError("Mass only accepts a single positional argument for value")
            kwargs.setdefault("value", args[0])
        super().__init__(**kwargs)
    value: float = Field(..., description="Besaran massa dalam satuan Kilogram (kg)")
    unit: MassUnit = Field(default=MassUnit.KILOGRAMS, description="Satuan awal input data")

    @field_validator("value", mode="before")
    @classmethod
    def validate_numeric_no_coercion(cls, value: Any) -> float:
        if isinstance(value, bool):
            logger.error("MASS_VALUE_REJECTED_BOOLEAN: %r", value)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(value, (int, float)):
            logger.error("MASS_VALUE_REJECTED_NON_NUMERIC: %r", value)
            raise TypeError("MASS_VALUE_MUST_BE_PURE_NUMERIC_TYPE")
        float_val = float(value)
        if math.isnan(float_val) or math.isinf(float_val):
            logger.error("MASS_VALUE_REJECTED_NAN_OR_INF: %s", float_val)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        if float_val < 0.0:
            logger.error("MASS_VALUE_REJECTED_NEGATIVE: %s", float_val)
            raise ValueError(f"QUANTITY_CONSTRAINT_VIOLATION_MASS_CANNOT_BE_NEGATIVE: {float_val}")
        return float_val

    @classmethod
    def from_grams(cls, g: Any) -> "Mass":
        """Named constructor untuk instansiasi Massa murni dari gram (g)."""
        if isinstance(g, bool):
            logger.error("MASS_FROM_GRAMS_REJECTED_BOOLEAN: %r", g)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(g, (int, float)):
            logger.error("MASS_FROM_GRAMS_REJECTED_NON_NUMERIC: %r", g)
            raise TypeError("MASS_VALUE_MUST_BE_PURE_NUMERIC_TYPE")
        float_val = float(g)
        if math.isnan(float_val) or math.isinf(float_val):
            logger.error("MASS_FROM_GRAMS_REJECTED_NAN_OR_INF: %s", float_val)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        if float_val < 0.0:
            logger.error("MASS_FROM_GRAMS_REJECTED_NEGATIVE: %s", float_val)
            raise ValueError(f"QUANTITY_CONSTRAINT_VIOLATION_MASS_CANNOT_BE_NEGATIVE: {float_val}")
        return cls(value=float_val * 0.001, unit=MassUnit.GRAMS)

    @classmethod
    def from_metric_tons(cls, t: Any) -> "Mass":
        """Named constructor untuk instansiasi Massa murni dari ton metrik (t)."""
        if isinstance(t, bool):
            logger.error("MASS_FROM_TONS_REJECTED_BOOLEAN: %r", t)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(t, (int, float)):
            logger.error("MASS_FROM_TONS_REJECTED_NON_NUMERIC: %r", t)
            raise TypeError("MASS_VALUE_MUST_BE_PURE_NUMERIC_TYPE")
        float_val = float(t)
        if math.isnan(float_val) or math.isinf(float_val):
            logger.error("MASS_FROM_TONS_REJECTED_NAN_OR_INF: %s", float_val)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        if float_val < 0.0:
            logger.error("MASS_FROM_TONS_REJECTED_NEGATIVE: %s", float_val)
            raise ValueError(f"QUANTITY_CONSTRAINT_VIOLATION_MASS_CANNOT_BE_NEGATIVE: {float_val}")
        return cls(value=float_val * 1000.0, unit=MassUnit.METRIC_TONS)

    def to_grams(self) -> float:
        return self.value * 1000.0

    def to_metric_tons(self) -> float:
        return self.value * 0.001

    def approximately_equal(self, other: Any, epsilon: float = 1e-6) -> bool:
        if not isinstance(other, Mass):
            return False
        return abs(self.value - other.value) <= epsilon

    def __add__(self, other: Any) -> "Mass":
        if not isinstance(other, Mass):
            logger.error("MASS_ADD_REJECTED_NON_MASS: %r", other)
            raise TypeError("OPERAND_MUST_BE_AN_INSTANCE_OF_MASS_CLASS")
        return Mass(value=self.value + other.value, unit=MassUnit.KILOGRAMS)

    def __sub__(self, other: Any) -> "Mass":
        if not isinstance(other, Mass):
            logger.error("MASS_SUB_REJECTED_NON_MASS: %r", other)
            raise TypeError("OPERAND_MUST_BE_AN_INSTANCE_OF_MASS_CLASS")
        result = self.value - other.value
        if result < 0.0:
            logger.error("MASS_SUB_RESULT_NEGATIVE: %s", result)
            raise ValueError(f"QUANTITY_CONSTRAINT_VIOLATION_SUBTRACTION_RESULT_CANNOT_BE_NEGATIVE: {result}")
        return Mass(value=result, unit=MassUnit.KILOGRAMS)

    def __mul__(self, scalar: Any) -> "Mass":
        if isinstance(scalar, bool):
            logger.error("MASS_MUL_REJECTED_BOOLEAN: %r", scalar)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(scalar, (int, float)):
            logger.error("MASS_MUL_REJECTED_NON_NUMERIC: %r", scalar)
            raise TypeError("SCALAR_MUST_BE_A_PURE_NUMERIC_TYPE")
        float_scalar = float(scalar)
        if math.isnan(float_scalar) or math.isinf(float_scalar):
            logger.error("MASS_MUL_REJECTED_NAN_OR_INF: %s", float_scalar)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        result = self.value * float_scalar
        if result < 0.0:
            logger.error("MASS_MUL_RESULT_NEGATIVE: %s", result)
            raise ValueError(f"QUANTITY_CONSTRAINT_VIOLATION_MULTIPLICATION_RESULT_CANNOT_BE_NEGATIVE: {result}")
        return Mass(value=result, unit=MassUnit.KILOGRAMS)

    def __rmul__(self, scalar: Any) -> "Mass":
        return self.__mul__(scalar)

    def __truediv__(self, scalar: Any) -> "Mass":
        if isinstance(scalar, bool):
            logger.error("MASS_DIV_REJECTED_BOOLEAN: %r", scalar)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(scalar, (int, float)):
            logger.error("MASS_DIV_REJECTED_NON_NUMERIC: %r", scalar)
            raise TypeError("SCALAR_MUST_BE_A_PURE_NUMERIC_TYPE")
        float_scalar = float(scalar)
        if float_scalar == 0.0:
            logger.error("MASS_DIV_BY_ZERO")
            raise ZeroDivisionError("DIVISION_BY_ZERO_PROHIBITED")
        if math.isnan(float_scalar) or math.isinf(float_scalar):
            logger.error("MASS_DIV_REJECTED_NAN_OR_INF: %s", float_scalar)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        result = self.value / float_scalar
        if result < 0.0:
            logger.error("MASS_DIV_RESULT_NEGATIVE: %s", result)
            raise ValueError(f"QUANTITY_CONSTRAINT_VIOLATION_DIVISION_RESULT_CANNOT_BE_NEGATIVE: {result}")
        return Mass(value=result, unit=MassUnit.KILOGRAMS)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Mass):
            return False
        return self.value == other.value

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Mass):
            logger.error("MASS_COMPARE_REJECTED_NON_MASS: %r", other)
            raise TypeError("COMPARISON_OPERAND_MUST_BE_AN_INSTANCE_OF_MASS_CLASS")
        return self.value < other.value

    def __le__(self, other: Any) -> bool:
        if not isinstance(other, Mass):
            logger.error("MASS_COMPARE_REJECTED_NON_MASS: %r", other)
            raise TypeError("COMPARISON_OPERAND_MUST_BE_AN_INSTANCE_OF_MASS_CLASS")
        return self.value <= other.value

    def __gt__(self, other: Any) -> bool:
        if not isinstance(other, Mass):
            logger.error("MASS_COMPARE_REJECTED_NON_MASS: %r", other)
            raise TypeError("COMPARISON_OPERAND_MUST_BE_AN_INSTANCE_OF_MASS_CLASS")
        return self.value > other.value

    def __ge__(self, other: Any) -> bool:
        if not isinstance(other, Mass):
            logger.error("MASS_COMPARE_REJECTED_NON_MASS: %r", other)
            raise TypeError("COMPARISON_OPERAND_MUST_BE_AN_INSTANCE_OF_MASS_CLASS")
        return self.value >= other.value

    def __str__(self) -> str:
        return f"{self.value} kg"

    def __repr__(self) -> str:
        return f"Mass({self.value})"