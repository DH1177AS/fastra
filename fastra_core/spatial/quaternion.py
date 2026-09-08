# fastra_core\spatial\quaternion.py

from __future__ import annotations

import logging
import math
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra_core.spatial.quaternion")


class Quaternion(BaseModel):
    """
    Primitive Value Object Spasial untuk merepresentasikan Quaternion (Rotasi 3D Hipersfer).
    Mencegah coercion hacks secara mutlak dan menjamin stabilitas normalisasi orientasi.
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
            if len(args) > 4:
                raise TypeError("Quaternion only accepts up to four positional arguments (w, x, y, z)")
            names = ['w', 'x', 'y', 'z']
            for i, val in enumerate(args):
                kwargs.setdefault(names[i], val)
        super().__init__(**kwargs)

    w: float = Field(..., description="Komponen skalar magnitudo kuaterner")
    x: float = Field(..., description="Komponen vektor imajiner arah sumbu X")
    y: float = Field(..., description="Komponen vektor imajiner arah sumbu Y")
    z: float = Field(..., description="Komponen vektor imajiner arah sumbu Z")

    @field_validator("w", "x", "y", "z", mode="before")
    @classmethod
    def validate_numeric_no_coercion(cls, value: Any) -> float:
        if isinstance(value, bool):
            logger.error("QUATERNION_COMPONENT_REJECTED_BOOLEAN: %r", value)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(value, (int, float)):
            logger.error("QUATERNION_COMPONENT_REJECTED_NON_NUMERIC: %r", value)
            raise TypeError("QUATERNION_COMPONENT_MUST_BE_PURE_NUMERIC_TYPE")
        float_val = float(value)
        if math.isnan(float_val) or math.isinf(float_val):
            logger.error("QUATERNION_COMPONENT_REJECTED_NAN_OR_INF: %s", float_val)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_QUATERNION_CANNOT_BE_NAN_OR_INFINITE")
        return float_val

    @classmethod
    def identity(cls) -> "Quaternion":
        """
        Named constructor untuk memproduksi unit identitas quaternion (Tanpa Rotasi).
        """
        return cls(w=1.0, x=0.0, y=0.0, z=0.0)

    @classmethod
    def from_axis_angle(
        cls,
        axis_x: Any,
        axis_y: Any,
        axis_z: Any,
        angle_rad: Any,
    ) -> "Quaternion":
        """
        Membangun unit rotasi 3D baru berbasis sepasang orientasi sumbu-sudut (Axis-Angle).
        Mengantisipasi kegagalan divisi nol dari masukan sumbu hampa secara fail-fast.
        """
        params = {
            "axis_x": axis_x,
            "axis_y": axis_y,
            "axis_z": axis_z,
            "angle_rad": angle_rad,
        }
        for param_name, param_val in params.items():
            if isinstance(param_val, bool):
                logger.error("QUATERNION_AXIS_ANGLE_BOOLEAN_%s: %r", param_name.upper(), param_val)
                raise TypeError(f"DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED_AT_{param_name}")
            if not isinstance(param_val, (int, float)):
                logger.error("QUATERNION_AXIS_ANGLE_NON_NUMERIC_%s: %r", param_name.upper(), param_val)
                raise TypeError(f"PARAMETER_{param_name.upper()}_MUST_BE_PURE_NUMERIC_TYPE")

        float_angle = float(angle_rad)
        if math.isnan(float_angle) or math.isinf(float_angle):
            logger.error("QUATERNION_AXIS_ANGLE_NAN_OR_INF: %s", float_angle)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_ANGLE_CANNOT_BE_NAN_OR_INFINITE")

        half_angle = float_angle / 2.0
        sin_half = math.sin(half_angle)
        cos_half = math.cos(half_angle)

        ax = float(axis_x)
        ay = float(axis_y)
        az = float(axis_z)

        axis_len_squared = ax * ax + ay * ay + az * az
        if math.isnan(axis_len_squared) or math.isinf(axis_len_squared):
            logger.error("QUATERNION_AXIS_MAGNITUDE_CORRUPTED: %s", axis_len_squared)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_AXIS_MAGNITUDE_CORRUPTED")

        if axis_len_squared < 1e-12:
            # Sumbu nol dianggap tidak ada rotasi; kembalikan identitas secara aman.
            logger.debug("QUATERNION_ZERO_AXIS_RETURNING_IDENTITY")
            return cls.identity()

        axis_len = math.sqrt(axis_len_squared)
        nx = ax / axis_len
        ny = ay / axis_len
        nz = az / axis_len

        return cls(
            w=cos_half,
            x=nx * sin_half,
            y=ny * sin_half,
            z=nz * sin_half,
        )

    def conjugate(self) -> "Quaternion":
        """
        Menghasilkan inversi arah orientasi spasial (Quaternion Conjugate).
        """
        return Quaternion(w=self.w, x=-self.x, y=-self.y, z=-self.z)

    def norm_squared(self) -> float:
        """
        Menghitung nilai norma kuadrat amplitudo internal.
        """
        result = self.w**2 + self.x**2 + self.y**2 + self.z**2
        if math.isnan(result) or math.isinf(result):
            logger.error("QUATERNION_NORM_SQUARED_CORRUPTED: %s", result)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_NORM_CALCULATION_CORRUPTED")
        return result

    def normalize(self) -> "Quaternion":
        """
        Menormalisasikan komponen objek ke dalam unit permukaan hipersfer murni (Unit Quaternion).
        """
        magnitude_squared = self.norm_squared()
        if magnitude_squared < 1e-12:
            logger.error("QUATERNION_NORMALIZE_ZERO_MAGNITUDE")
            raise ValueError("NUMERIC_SINGULARITY_DETECTED_CANNOT_NORMALIZE_ZERO_QUATERNION")
        magnitude = math.sqrt(magnitude_squared)
        return Quaternion(
            w=self.w / magnitude,
            x=self.x / magnitude,
            y=self.y / magnitude,
            z=self.z / magnitude,
        )

    def __mul__(self, other: Any) -> "Quaternion":
        """
        Operator overloading perkalian biner Hamilton untuk komposisi rotasi ganda berurutan.
        """
        if not isinstance(other, Quaternion):
            logger.error("QUATERNION_MUL_REJECTED_NON_QUATERNION: %r", other)
            raise TypeError("OPERAND_MUST_BE_AN_INSTANCE_OF_QUATERNION_CLASS")

        w1, x1, y1, z1 = self.w, self.x, self.y, self.z
        w2, x2, y2, z2 = other.w, other.x, other.y, other.z

        return Quaternion(
            w=w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
            x=w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            y=w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
            z=w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
        )

    def approximately_equal(self, other: Any, epsilon: Any = 1e-6) -> bool:
        if not isinstance(other, Quaternion):
            return False

        if isinstance(epsilon, bool) or not isinstance(epsilon, (int, float)):
            logger.error("QUATERNION_APPROX_EPSILON_REJECTED: %r", epsilon)
            raise TypeError("EPSILON_TOLERANCE_MUST_BE_A_PURE_NUMERIC_TYPE")

        return (
            abs(self.w - other.w) <= epsilon and
            abs(self.x - other.x) <= epsilon and
            abs(self.y - other.y) <= epsilon and
            abs(self.z - other.z) <= epsilon
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Quaternion):
            return False
        return (
            self.w == other.w and self.x == other.x and
            self.y == other.y and self.z == other.z
        )

    def __repr__(self) -> str:
        return f"Quaternion({self.w}, {self.x}, {self.y}, {self.z})"