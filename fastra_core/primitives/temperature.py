# fastra_core\primitives\temperature.py

from __future__ import annotations

import logging
import math
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra.primitives.temperature")


class TemperatureUnit(str, Enum):
    """
    Strict Enum untuk satuan ukuran temperatur termal dalam standardisasi pengujian beton & material.
    Menghilangkan manipulasi paksa (coercion hack) tipe string bebas.
    """
    KELVIN = "K"
    CELSIUS = "C"
    FAHRENHEIT = "F"


class Temperature(BaseModel):
    """
    Primitive Value Object untuk merepresentasikan besaran Temperatur (Temperature).
    Menggunakan Pydantic sebagai validator tunggal dengan mode strict fail-fast.
    Seluruh nilai internal disimpan secara absolut dalam satuan Kelvin (K) dengan batas Nol Mutlak.
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    value: float = Field(..., description="Besaran temperatur dalam satuan Kelvin (K)")
    unit: TemperatureUnit = Field(default=TemperatureUnit.KELVIN, description="Satuan awal input data")

    @field_validator("value", mode="before")
    @classmethod
    def validate_numeric_no_coercion(cls, value: Any) -> float:
        if isinstance(value, bool):
            logger.error("TEMPERATURE_VALUE_REJECTED_BOOLEAN: %r", value)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(value, (int, float)):
            logger.error("TEMPERATURE_VALUE_REJECTED_NON_NUMERIC: %r", value)
            raise TypeError("TEMPERATURE_VALUE_MUST_BE_PURE_NUMERIC_TYPE")
        float_val = float(value)
        if math.isnan(float_val) or math.isinf(float_val):
            logger.error("TEMPERATURE_VALUE_REJECTED_NAN_OR_INF: %s", float_val)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        if float_val < 0.0:
            logger.error("TEMPERATURE_VALUE_REJECTED_BELOW_ABSOLUTE_ZERO: %s K", float_val)
            raise ValueError(
                f"THERMODYNAMIC_CONSTRAINT_VIOLATION_TEMPERATURE_CANNOT_BE_BELOW_ABSOLUTE_ZERO: {float_val} K"
            )
        return float_val

    @classmethod
    def from_celsius(cls, c: Any) -> "Temperature":
        """Named constructor untuk instansiasi Temperatur murni dari Celsius (°C)."""
        if isinstance(c, bool):
            logger.error("TEMPERATURE_FROM_CELSIUS_REJECTED_BOOLEAN: %r", c)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(c, (int, float)):
            logger.error("TEMPERATURE_FROM_CELSIUS_REJECTED_NON_NUMERIC: %r", c)
            raise TypeError("TEMPERATURE_VALUE_MUST_BE_PURE_NUMERIC_TYPE")
        float_val = float(c)
        if math.isnan(float_val) or math.isinf(float_val):
            logger.error("TEMPERATURE_FROM_CELSIUS_REJECTED_NAN_OR_INF: %s", float_val)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        kelvin_val = float_val + 273.15
        if kelvin_val < 0.0:
            logger.error("TEMPERATURE_FROM_CELSIUS_REJECTED_BELOW_ABSOLUTE_ZERO: %s K", kelvin_val)
            raise ValueError(
                f"THERMODYNAMIC_CONSTRAINT_VIOLATION_TEMPERATURE_CANNOT_BE_BELOW_ABSOLUTE_ZERO: {kelvin_val} K"
            )
        return cls(value=kelvin_val, unit=TemperatureUnit.CELSIUS)

    @classmethod
    def from_fahrenheit(cls, f: Any) -> "Temperature":
        """Named constructor untuk instansiasi Temperatur murni dari Fahrenheit (°F)."""
        if isinstance(f, bool):
            logger.error("TEMPERATURE_FROM_FAHRENHEIT_REJECTED_BOOLEAN: %r", f)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(f, (int, float)):
            logger.error("TEMPERATURE_FROM_FAHRENHEIT_REJECTED_NON_NUMERIC: %r", f)
            raise TypeError("TEMPERATURE_VALUE_MUST_BE_PURE_NUMERIC_TYPE")
        float_val = float(f)
        if math.isnan(float_val) or math.isinf(float_val):
            logger.error("TEMPERATURE_FROM_FAHRENHEIT_REJECTED_NAN_OR_INF: %s", float_val)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        kelvin_val = (float_val - 32.0) * 5.0 / 9.0 + 273.15
        if kelvin_val < 0.0:
            logger.error("TEMPERATURE_FROM_FAHRENHEIT_REJECTED_BELOW_ABSOLUTE_ZERO: %s K", kelvin_val)
            raise ValueError(
                f"THERMODYNAMIC_CONSTRAINT_VIOLATION_TEMPERATURE_CANNOT_BE_BELOW_ABSOLUTE_ZERO: {kelvin_val} K"
            )
        return cls(value=kelvin_val, unit=TemperatureUnit.FAHRENHEIT)

    def to_celsius(self) -> float:
        return self.value - 273.15

    def to_fahrenheit(self) -> float:
        return (self.value - 273.15) * 9.0 / 5.0 + 32.0

    def approximately_equal(self, other: Any, epsilon: float = 1e-6) -> bool:
        if not isinstance(other, Temperature):
            return False
        return abs(self.value - other.value) <= epsilon

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Temperature):
            return False
        return self.value == other.value

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Temperature):
            logger.error("TEMPERATURE_COMPARE_REJECTED_NON_TEMPERATURE: %r", other)
            raise TypeError("COMPARISON_OPERAND_MUST_BE_AN_INSTANCE_OF_TEMPERATURE_CLASS")
        return self.value < other.value

    def __le__(self, other: Any) -> bool:
        if not isinstance(other, Temperature):
            logger.error("TEMPERATURE_COMPARE_REJECTED_NON_TEMPERATURE: %r", other)
            raise TypeError("COMPARISON_OPERAND_MUST_BE_AN_INSTANCE_OF_TEMPERATURE_CLASS")
        return self.value <= other.value

    def __gt__(self, other: Any) -> bool:
        if not isinstance(other, Temperature):
            logger.error("TEMPERATURE_COMPARE_REJECTED_NON_TEMPERATURE: %r", other)
            raise TypeError("COMPARISON_OPERAND_MUST_BE_AN_INSTANCE_OF_TEMPERATURE_CLASS")
        return self.value > other.value

    def __ge__(self, other: Any) -> bool:
        if not isinstance(other, Temperature):
            logger.error("TEMPERATURE_COMPARE_REJECTED_NON_TEMPERATURE: %r", other)
            raise TypeError("COMPARISON_OPERAND_MUST_BE_AN_INSTANCE_OF_TEMPERATURE_CLASS")
        return self.value >= other.value

    def __str__(self) -> str:
        return f"{self.to_celsius():.1f} °C"

    def __repr__(self) -> str:
        return f"Temperature({self.value} K)"