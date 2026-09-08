# fastra_core\primitives\density.py

from __future__ import annotations

import logging
import math
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra.primitives.density")


class DensityUnit(str, Enum):
    """
    Strict Enum untuk satuan ukuran massa jenis (density) material konstruksi.
    Mencegah coercion hack dan variasi penulisan string ilegal.
    """
    KG_PER_CUBIC_METER = "kg/m³"
    G_PER_CUBIC_CENTIMETER = "g/cm³"


class Density(BaseModel):
    """
    Primitive Value Object untuk merepresentasikan Massa Jenis Material (Density).
    Menggunakan Pydantic sebagai validator tunggal dengan mode strict fail-fast.
    Seluruh nilai internal disimpan secara absolut dalam satuan Kilogram per Meter Kubik (kg/m³).
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    value: float = Field(..., description="Besaran massa jenis dalam satuan Kilogram per Meter Kubik (kg/m³)")
    unit: DensityUnit = Field(default=DensityUnit.KG_PER_CUBIC_METER, description="Satuan awal input data")

    def __init__(self, *args, **kwargs):
        if args:
            if len(args) > 1:
                raise TypeError("Density only accepts a single positional argument for value")
            kwargs.setdefault("value", args[0])
        super().__init__(**kwargs)

    @field_validator("value", mode="before")
    @classmethod
    def validate_numeric_no_coercion(cls, value: Any) -> float:
        if isinstance(value, bool):
            logger.error("DENSITY_VALUE_REJECTED_BOOLEAN: %r", value)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(value, (int, float)):
            logger.error("DENSITY_VALUE_REJECTED_NON_NUMERIC: %r", value)
            raise TypeError("DENSITY_VALUE_MUST_BE_PURE_NUMERIC_TYPE")
        float_val = float(value)
        if math.isnan(float_val) or math.isinf(float_val):
            logger.error("DENSITY_VALUE_REJECTED_NAN_OR_INF: %s", float_val)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        if float_val <= 0.0:
            logger.error("DENSITY_VALUE_REJECTED_NON_POSITIVE: %s", float_val)
            raise ValueError(f"QUANTITY_CONSTRAINT_VIOLATION_DENSITY_MUST_BE_GREATER_THAN_ZERO: {float_val}")
        return float_val

    @classmethod
    def from_g_per_cubic_cm(cls, val: Any) -> "Density":
        """
        Named constructor untuk instansiasi Massa Jenis murni dari satuan Gram per Sentimeter Kubik (g/cm³).
        """
        if isinstance(val, bool):
            logger.error("DENSITY_FROM_G_CM3_REJECTED_BOOLEAN: %r", val)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(val, (int, float)):
            logger.error("DENSITY_FROM_G_CM3_REJECTED_NON_NUMERIC: %r", val)
            raise TypeError("DENSITY_VALUE_MUST_BE_PURE_NUMERIC_TYPE")
        float_val = float(val)
        if math.isnan(float_val) or math.isinf(float_val):
            logger.error("DENSITY_FROM_G_CM3_REJECTED_NAN_OR_INF: %s", float_val)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        if float_val <= 0.0:
            logger.error("DENSITY_FROM_G_CM3_REJECTED_NON_POSITIVE: %s", float_val)
            raise ValueError(f"QUANTITY_CONSTRAINT_VIOLATION_DENSITY_MUST_BE_GREATER_THAN_ZERO: {float_val}")
        return cls(value=float_val * 1000.0, unit=DensityUnit.G_PER_CUBIC_CENTIMETER)

    def to_g_per_cubic_cm(self) -> float:
        """
        Mengonversi nilai massa jenis internal ke Gram per Sentimeter Kubik (g/cm³).
        """
        return self.value / 1000.0

    def approximately_equal(self, other: Any, epsilon: float = 1e-6) -> bool:
        """
        Memverifikasi kesamaan nilai massa jenis berdasarkan batas toleransi floating point (epsilon).
        """
        if not isinstance(other, Density):
            return False
        return abs(self.value - other.value) <= epsilon

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Density):
            return False
        return self.value == other.value

    def __str__(self) -> str:
        return f"{self.value} kg/m³"

    def __repr__(self) -> str:
        return f"Density({self.value})"