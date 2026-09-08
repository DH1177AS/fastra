# fastra_core\primitives\angle.py

from __future__ import annotations

import logging
import math
from enum import Enum
from typing import Any

from pydantic.dataclasses import dataclass

logger = logging.getLogger("fastra.primitives.angle")


class AngleUnit(str, Enum):
    """
    Strict Enum untuk satuan ukuran sudut.
    Mencegah coercion hack dan variasi penulisan string ilegal.
    """
    RADIANS = "rad"
    DEGREES = "deg"


@dataclass(frozen=True)
class Angle:
    """
    Primitive Value Object untuk merepresentasikan besaran Sudut (Angle).
    Menggunakan dataclass Pydantic untuk mendukung inisialisasi posisional
    dan mempertahankan validasi ketat dengan mode strict fail-fast.
    Seluruh nilai internal disimpan secara absolut dalam satuan Radian (rad).
    """
    value: float
    unit: AngleUnit = AngleUnit.RADIANS

    def __post_init__(self) -> None:
        """
        Validasi ketat dilakukan pada tahap inisialisasi dataclass.
        Menolak boolean, non-numerik, NaN, dan infinity.
        """
        value = self.value
        if isinstance(value, bool):
            logger.error("ANGLE_VALUE_REJECTED_BOOLEAN: %r", value)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(value, (int, float)):
            logger.error("ANGLE_VALUE_REJECTED_NON_NUMERIC: %r", value)
            raise TypeError("ANGLE_VALUE_MUST_BE_PURE_NUMERIC_TYPE")
        float_val = float(value)
        if math.isnan(float_val) or math.isinf(float_val):
            logger.error("ANGLE_VALUE_REJECTED_NAN_OR_INF: %s", float_val)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        object.__setattr__(self, "value", float_val)
        object.__setattr__(self, "unit", self.unit)

    @classmethod
    def from_degrees(cls, deg: Any) -> "Angle":
        """
        Named constructor untuk instansiasi Sudut murni dari satuan Derajat.
        """
        if isinstance(deg, bool):
            logger.error("ANGLE_FROM_DEGREES_REJECTED_BOOLEAN: %r", deg)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(deg, (int, float)):
            logger.error("ANGLE_FROM_DEGREES_REJECTED_NON_NUMERIC: %r", deg)
            raise TypeError("ANGLE_VALUE_MUST_BE_PURE_NUMERIC_TYPE")
        float_deg = float(deg)
        if math.isnan(float_deg) or math.isinf(float_deg):
            logger.error("ANGLE_FROM_DEGREES_REJECTED_NAN_OR_INF: %s", float_deg)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_BE_NAN_OR_INFINITE")
        return cls(value=math.radians(float_deg), unit=AngleUnit.DEGREES)

    def to_degrees(self) -> float:
        """
        Mengonversi nilai sudut internal dari Radian ke Derajat secara presisi.
        """
        return math.degrees(self.value)

    def normalized(self) -> "Angle":
        """
        Mengembalikan instansiasi objek Sudut baru yang telah dinormalisasi
        ke dalam rentang periodik lingkaran murni: [0, 2π) Radian.
        """
        two_pi = 2 * math.pi
        normalized_value = self.value % two_pi
        # Menangani nilai modulus negatif bawaan Python agar tetap berada dalam rentang positif
        if normalized_value < 0:
            normalized_value += two_pi
        return Angle(value=normalized_value, unit=AngleUnit.RADIANS)

    def approximately_equal(self, other: Any, epsilon: float = 1e-9) -> bool:
        """
        Memverifikasi kesamaan nilai sudut berdasarkan batas toleransi kesalahan floating point (epsilon).
        """
        if not isinstance(other, Angle):
            return False
        # Normalisasi kedua sudut sebelum melakukan komparasi jarak spasial murni
        self_norm = self.normalized().value
        other_norm = other.normalized().value
        diff = abs(self_norm - other_norm)
        # Menangani pembungkus batas periodik lingkaran jika mendekati nilai 2π
        return diff <= epsilon or abs(2 * math.pi - diff) <= epsilon

    def __add__(self, other: Any) -> "Angle":
        if not isinstance(other, Angle):
            logger.error("ANGLE_ADD_REJECTED_NON_ANGLE: %r", other)
            raise TypeError("OPERAND_MUST_BE_AN_INSTANCE_OF_ANGLE_CLASS")
        return Angle(value=self.value + other.value, unit=AngleUnit.RADIANS)

    def __sub__(self, other: Any) -> "Angle":
        if not isinstance(other, Angle):
            logger.error("ANGLE_SUB_REJECTED_NON_ANGLE: %r", other)
            raise TypeError("OPERAND_MUST_BE_AN_INSTANCE_OF_ANGLE_CLASS")
        return Angle(value=self.value - other.value, unit=AngleUnit.RADIANS)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Angle):
            return False
        return self.value == other.value

    def __str__(self) -> str:
        return f"{self.to_degrees():.2f}°"