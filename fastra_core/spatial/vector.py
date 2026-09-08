# fastra_core\spatial\vector.py

from __future__ import annotations

import logging
import math
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from fastra_core.primitives.length import Length

logger = logging.getLogger("fastra_core.spatial.vector")


class Vector(BaseModel):
    """
    Primitive Value Object Spasial untuk merepresentasikan Vektor Bebas 3D (dx, dy, dz).
    Menggunakan Pydantic sebagai validator tunggal dengan mode strict fail-fast.
    Objek diisolasi secara absolut (frozen=True) dalam memori runtime.

    Catatan Arsitektur:
    Atribut diubah dari `dx`, `dy`, `dz` menjadi `x`, `y`, `z` demi menjaga keseragaman
    antarmuka koordinat affin homogen di seluruh pipeline sistem (`Transform`, `Matrix4x4`).
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
            if len(args) > 3:
                raise TypeError("Vector only accepts up to three positional arguments (x, y, z)")
            names = ['x', 'y', 'z']
            for i, val in enumerate(args):
                kwargs.setdefault(names[i], val)
        super().__init__(**kwargs)

    x: float = Field(..., description="Komponen perubahan posisi sumbu X (Delta X)")
    y: float = Field(..., description="Komponen perubahan posisi sumbu Y (Delta Y)")
    z: float = Field(..., description="Komponen perubahan posisi sumbu Z (Delta Z)")

    @field_validator("x", "y", "z", mode="before")
    @classmethod
    def validate_numeric_no_coercion(cls, value: Any) -> float:
        if isinstance(value, bool):
            logger.error("VECTOR_COMPONENT_REJECTED_BOOLEAN: %r", value)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(value, (int, float)):
            logger.error("VECTOR_COMPONENT_REJECTED_NON_NUMERIC: %r", value)
            raise TypeError("VECTOR_COMPONENT_MUST_BE_PURE_NUMERIC_TYPE")
        float_val = float(value)
        if math.isnan(float_val) or math.isinf(float_val):
            logger.error("VECTOR_COMPONENT_REJECTED_NAN_OR_INF: %s", float_val)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_VECTOR_CANNOT_BE_NAN_OR_INFINITE")
        return float_val

    def magnitude(self) -> Length:
        """
        Menghitung panjang/magnitudo murni vektor 3D menggunakan kalkulasi Euclidean Norm.
        Mengembalikan primitif Value Object 'Length' bertipe data terikat.
        """
        squared_sum = self.x * self.x + self.y * self.y + self.z * self.z
        if isinstance(squared_sum, bool):
            logger.error("VECTOR_MAGNITUDE_SQUARED_SUM_BOOLEAN: %r", squared_sum)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")

        calculated_magnitude = math.sqrt(squared_sum)
        if math.isnan(calculated_magnitude) or math.isinf(calculated_magnitude):
            logger.error("VECTOR_MAGNITUDE_NUMERIC_ANOMALY: %s", calculated_magnitude)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_VECTOR_MAGNITUDE_CORRUPTED")

        return Length(value=calculated_magnitude)

    def cross(self, other: Any) -> "Vector":
        """
        Menghitung perkalian silang (Cross Product) untuk menghasilkan vektor ortogonal baru di ruang 3D.
        """
        if not isinstance(other, Vector):
            logger.error("VECTOR_CROSS_REJECTED_NON_VECTOR: %r", other)
            raise TypeError("CROSS_PRODUCT_OPERAND_MUST_BE_AN_INSTANCE_OF_VECTOR_CLASS")

        return Vector(
            x=self.y * other.z - self.z * other.y,
            y=self.z * other.x - self.x * other.z,
            z=self.x * other.y - self.y * other.x,
        )

    def dot(self, other: Any) -> float:
        """
        Menghitung perkalian titik (Dot Product) skalar spasial.
        """
        if not isinstance(other, Vector):
            logger.error("VECTOR_DOT_REJECTED_NON_VECTOR: %r", other)
            raise TypeError("DOT_PRODUCT_OPERAND_MUST_BE_AN_INSTANCE_OF_VECTOR_CLASS")

        result = self.x * other.x + self.y * other.y + self.z * other.z

        if isinstance(result, bool):
            logger.error("VECTOR_DOT_RESULT_BOOLEAN: %r", result)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if math.isnan(result) or math.isinf(result):
            logger.error("VECTOR_DOT_RESULT_NAN_OR_INF: %s", result)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_DOT_PRODUCT_CANNOT_BE_NAN_OR_INFINITE")

        return float(result)

    def normalize(self) -> "Vector":
        """
        Menormalisasikan vektor ke dalam arah komponen unit panjang absolut dasar (Unit Vector).
        Mengantisipasi kegagalan pembagian dengan nol dari vektor hampa secara fail-fast.
        """
        m_decimal = self.magnitude().value
        m = float(m_decimal)
        if abs(m) < 1e-24:
            logger.error("VECTOR_NORMALIZE_ZERO_MAGNITUDE")
            raise ValueError("NUMERICAL_SINGULARITY_CANNOT_NORMALIZE_A_ZERO_VECTOR")

        return Vector(x=self.x / m, y=self.y / m, z=self.z / m)

    def approximately_equal(self, other: Any, epsilon: Any = 1e-6) -> bool:
        if not isinstance(other, Vector):
            return False

        if isinstance(epsilon, bool) or not isinstance(epsilon, (int, float)):
            logger.error("VECTOR_APPROX_EPSILON_REJECTED: %r", epsilon)
            raise TypeError("EPSILON_TOLERANCE_MUST_BE_A_PURE_NUMERIC_TYPE")

        return (
            abs(self.x - other.x) <= epsilon and
            abs(self.y - other.y) <= epsilon and
            abs(self.z - other.z) <= epsilon
        )

    def __add__(self, other: Any) -> "Vector":
        if not isinstance(other, Vector):
            logger.error("VECTOR_ADD_REJECTED_NON_VECTOR: %r", other)
            raise TypeError("ADDITION_OPERAND_MUST_BE_AN_INSTANCE_OF_VECTOR_CLASS")
        return Vector(x=self.x + other.x, y=self.y + other.y, z=self.z + other.z)

    def __sub__(self, other: Any) -> "Vector":
        if not isinstance(other, Vector):
            logger.error("VECTOR_SUB_REJECTED_NON_VECTOR: %r", other)
            raise TypeError("SUBTRACTION_OPERAND_MUST_BE_AN_INSTANCE_OF_VECTOR_CLASS")
        return Vector(x=self.x - other.x, y=self.y - other.y, z=self.z - other.z)

    def __mul__(self, scalar: Any) -> "Vector":
        """
        Operator overloading perkalian skalar eksternal untuk perbesaran magnitudo vektor.
        """
        if isinstance(scalar, bool):
            logger.error("VECTOR_MUL_REJECTED_BOOLEAN: %r", scalar)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(scalar, (int, float)):
            logger.error("VECTOR_MUL_REJECTED_NON_NUMERIC: %r", scalar)
            raise TypeError("SCALAR_MULTIPLIER_MUST_BE_A_PURE_NUMERIC_TYPE")

        float_scalar = float(scalar)
        if math.isnan(float_scalar) or math.isinf(float_scalar):
            logger.error("VECTOR_MUL_REJECTED_NAN_OR_INF: %s", float_scalar)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_SCALAR_MULTIPLIER_CANNOT_BE_NAN_OR_INFINITE")

        return Vector(x=self.x * float_scalar, y=self.y * float_scalar, z=self.z * float_scalar)

    def __rmul__(self, scalar: Any) -> "Vector":
        return self.__mul__(scalar)

    def __truediv__(self, scalar: Any) -> "Vector":
        if isinstance(scalar, bool):
            logger.error("VECTOR_DIV_REJECTED_BOOLEAN: %r", scalar)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(scalar, (int, float)):
            logger.error("VECTOR_DIV_REJECTED_NON_NUMERIC: %r", scalar)
            raise TypeError("SCALAR_DIVISOR_MUST_BE_A_PURE_NUMERIC_TYPE")

        float_scalar = float(scalar)
        if float_scalar == 0.0:
            logger.error("VECTOR_DIV_BY_ZERO")
            raise ZeroDivisionError("DIVISION_BY_ZERO_PROHIBITED")
        if math.isnan(float_scalar) or math.isinf(float_scalar):
            logger.error("VECTOR_DIV_REJECTED_NAN_OR_INF: %s", float_scalar)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_SCALAR_DIVISOR_CANNOT_BE_NAN_OR_INFINITE")

        return Vector(x=self.x / float_scalar, y=self.y / float_scalar, z=self.z / float_scalar)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Vector):
            return False
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __str__(self) -> str:
        return f"[{self.x:.4f}, {self.y:.4f}, {self.z:.4f}]"

    def __repr__(self) -> str:
        return f"Vector(x={self.x}, y={self.y}, z={self.z})"