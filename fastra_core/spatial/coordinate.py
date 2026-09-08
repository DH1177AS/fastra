# fastra_core/spatial/coordinate.py

from __future__ import annotations

import logging
import math
from typing import Any

from fastra_core.primitives.length import Length

logger = logging.getLogger("fastra_core.spatial.coordinate")


class Coordinate:
    """
    Primitive Value Object Spasial untuk merepresentasikan titik Koordinat 3D (X, Y, Z).
    Menggunakan class Python biasa dengan validasi manual yang ketat.
    Objek dijamin tidak dapat diubah (immutable) dengan menyimpan nilai sebagai float.
    """

    __slots__ = ("_x", "_y", "_z")

    def __init__(self, x: Any, y: Any, z: Any = 0.0) -> None:
        self._x = self._validate_component(x, "x")
        self._y = self._validate_component(y, "y")
        self._z = self._validate_component(z, "z")

    @staticmethod
    def _validate_component(value: Any, name: str) -> float:
        """Validasi komponen koordinat: tolak bool, non‑numerik, dan NaN/Inf."""
        if isinstance(value, bool):
            logger.error("COORDINATE_COMPONENT_REJECTED_BOOLEAN: %s=%r", name, value)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(value, (int, float)):
            logger.error("COORDINATE_COMPONENT_REJECTED_NON_NUMERIC: %s=%r", name, value)
            raise TypeError("COORDINATE_COMPONENT_MUST_BE_PURE_NUMERIC_TYPE")
        float_val = float(value)
        if math.isnan(float_val) or math.isinf(float_val):
            logger.error("COORDINATE_COMPONENT_REJECTED_NAN_OR_INF: %s=%s", name, float_val)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_COORDINATE_CANNOT_BE_NAN_OR_INFINITE")
        return float_val

    @property
    def x(self) -> float:
        return self._x

    @property
    def y(self) -> float:
        return self._y

    @property
    def z(self) -> float:
        return self._z

    def distance_to(self, other: Any) -> Length:
        """Menghitung jarak Euclidean 3D ke koordinat lain, mengembalikan Length."""
        if not isinstance(other, Coordinate):
            logger.error("DISTANCE_TO_REJECTED_NON_COORDINATE: %r", other)
            raise TypeError("DISTANCE_CALCULATION_REQUIRES_A_PURE_COORDINATE_INSTANCE")

        dx = self._x - other.x
        dy = self._y - other.y
        dz = self._z - other.z

        distance_squared = dx * dx + dy * dy + dz * dz
        if isinstance(distance_squared, bool):
            logger.error("DISTANCE_SQUARED_BOOLEAN: %r", distance_squared)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")

        calculated_distance = math.sqrt(distance_squared)
        if math.isnan(calculated_distance) or math.isinf(calculated_distance):
            logger.error("DISTANCE_CALCULATION_NUMERIC_ANOMALY: %s", calculated_distance)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_SPATIAL_DISTANCE_CORRUPTED")

        return Length(value=calculated_distance)

    def midpoint(self, other: Any) -> "Coordinate":
        """Menghitung titik tengah antara dua koordinat 3D."""
        if not isinstance(other, Coordinate):
            logger.error("MIDPOINT_REJECTED_NON_COORDINATE: %r", other)
            raise TypeError("MIDPOINT_CALCULATION_REQUIRES_A_PURE_COORDINATE_INSTANCE")

        mid_x = (self._x + other.x) / 2.0
        mid_y = (self._y + other.y) / 2.0
        mid_z = (self._z + other.z) / 2.0
        return Coordinate(x=mid_x, y=mid_y, z=mid_z)

    def approximately_equal(self, other: Any, epsilon: Any = 1e-6) -> bool:
        """Memeriksa kesetaraan dengan toleransi numerik."""
        if not isinstance(other, Coordinate):
            return False

        if isinstance(epsilon, bool) or not isinstance(epsilon, (int, float)):
            logger.error("APPROX_EQUAL_EPSILON_REJECTED: %r", epsilon)
            raise TypeError("EPSILON_TOLERANCE_MUST_BE_A_PURE_NUMERIC_TYPE")

        return (
            abs(self._x - other.x) <= epsilon and
            abs(self._y - other.y) <= epsilon and
            abs(self._z - other.z) <= epsilon
        )

    def __sub__(self, other: Any) -> Any:
        """Operator pengurangan antar koordinat menghasilkan Vector 3D."""
        if not isinstance(other, Coordinate):
            logger.error("COORDINATE_SUB_REJECTED_NON_COORDINATE: %r", other)
            raise TypeError("SUBTRACTION_OPERAND_MUST_BE_AN_INSTANCE_OF_COORDINATE_CLASS")

        # Import lokal untuk mencegah circular dependency
        from fastra_core.spatial.vector import Vector

        return Vector(x=self._x - other.x, y=self._y - other.y, z=self._z - other.z)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Coordinate):
            return False
        return self._x == other.x and self._y == other.y and self._z == other.z

    def __str__(self) -> str:
        return f"({self._x:.4f}, {self._y:.4f}, {self._z:.4f})"

    def __repr__(self) -> str:
        return f"Coordinate(x={self._x}, y={self._y}, z={self._z})"