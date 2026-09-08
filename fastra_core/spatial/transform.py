# fastra_core\spatial\transform.py

from __future__ import annotations

import logging
import math
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from fastra_core.spatial.vector import Vector
from fastra_core.spatial.quaternion import Quaternion
from fastra_core.spatial.matrix4x4 import Matrix4x4
from fastra_core.spatial.coordinate import Coordinate

logger = logging.getLogger("fastra_core.spatial.transform")


class Transform(BaseModel):
    """
    Primitive Value Object Spasial untuk merepresentasikan Transformasi Affine 3D.
    Menggabungkan komponen translasi, rotasi kuaterner, dan skala spasial secara rigid.
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
                raise TypeError("Transform only accepts up to three positional arguments (translation, rotation, scale)")
            names = ['translation', 'rotation', 'scale']
            for i, val in enumerate(args):
                kwargs.setdefault(names[i], val)
        super().__init__(**kwargs)

    translation: Vector = Field(default_factory=lambda: Vector(x=0.0, y=0.0, z=0.0))
    rotation: Quaternion = Field(default_factory=Quaternion.identity)
    scale: Vector = Field(default_factory=lambda: Vector(x=1.0, y=1.0, z=1.0))

    @model_validator(mode="after")
    def verify_scale_components_positive(self) -> "Transform":
        """
        Validasi batas fisis regangan (Scale Boundary Verification).
        Melarang nilai skala nol atau negatif demi mencegah deformasi hancur atau runtuhnya matriks.
        """
        if self.scale.x <= 0.0:
            logger.error("TRANSFORM_SCALE_X_NON_POSITIVE: %s", self.scale.x)
            raise ValueError("SCALE_COMPONENT_X_MUST_BE_POSITIVE")
        if self.scale.y <= 0.0:
            logger.error("TRANSFORM_SCALE_Y_NON_POSITIVE: %s", self.scale.y)
            raise ValueError("SCALE_COMPONENT_Y_MUST_BE_POSITIVE")
        if self.scale.z <= 0.0:
            logger.error("TRANSFORM_SCALE_Z_NON_POSITIVE: %s", self.scale.z)
            raise ValueError("SCALE_COMPONENT_Z_MUST_BE_POSITIVE")
        return self

    @classmethod
    def identity(cls) -> "Transform":
        """
        Named constructor untuk menghasilkan objek identitas transformasi (Tanpa Deformasi).
        """
        return cls(
            translation=Vector(x=0.0, y=0.0, z=0.0),
            rotation=Quaternion.identity(),
            scale=Vector(x=1.0, y=1.0, z=1.0),
        )

    @classmethod
    def from_translation(cls, dx: Any, dy: Any, dz: Any) -> "Transform":
        """
        Named constructor cepat untuk memproduksi objek pergeseran posisi (Translasi) murni.
        """
        params = {"dx": dx, "dy": dy, "dz": dz}
        for param_name, param_val in params.items():
            if isinstance(param_val, bool):
                logger.error("TRANSFORM_TRANSLATION_BOOLEAN_%s: %r", param_name.upper(), param_val)
                raise TypeError(f"DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED_AT_{param_name}")
            if not isinstance(param_val, (int, float)):
                logger.error("TRANSFORM_TRANSLATION_NON_NUMERIC_%s: %r", param_name.upper(), param_val)
                raise TypeError(f"PARAMETER_{param_name.upper()}_MUST_BE_PURE_NUMERIC_TYPE")

            float_val = float(param_val)
            if math.isnan(float_val) or math.isinf(float_val):
                logger.error("TRANSFORM_TRANSLATION_NAN_OR_INF_%s: %s", param_name.upper(), float_val)
                raise ValueError(f"NUMERIC_ANOMALY_DETECTED_AT_{param_name.upper()}_CANNOT_BE_NAN_OR_INFINITE")

        return cls(
            translation=Vector(x=float(dx), y=float(dy), z=float(dz)),
            rotation=Quaternion.identity(),
            scale=Vector(x=1.0, y=1.0, z=1.0),
        )

    def to_matrix(self) -> Matrix4x4:
        """
        Mengonversi koordinat affine (Translasi, Rotasi, Skala) ke dalam representasi Matrix4x4 homogen.
        Menerapkan pemetaan matematis presisi tanpa memicu precision bleeding.
        """
        q = self.rotation.normalize()
        w, x, y, z = q.w, q.x, q.y, q.z

        xx, yy, zz = x * x, y * y, z * z
        xy, xz, yz = x * y, x * z, y * z
        wx, wy, wz = w * x, w * y, w * z

        sx, sy, sz = self.scale.x, self.scale.y, self.scale.z
        tx, ty, tz = self.translation.x, self.translation.y, self.translation.z

        # Memetakan baris-baris matriks column-major order homogen secara presisi
        row0 = [sx * (1.0 - 2.0 * (yy + zz)), sy * (2.0 * (xy - wz)),       sz * (2.0 * (xz + wy)),       tx]
        row1 = [sx * (2.0 * (xy + wz)),       sy * (1.0 - 2.0 * (xx + zz)), sz * (2.0 * (yz - wx)),       ty]
        row2 = [sx * (2.0 * (xz - wy)),       sy * (2.0 * (yz + wx)),       sz * (1.0 - 2.0 * (xx + yy)), tz]
        row3 = [0.0, 0.0, 0.0, 1.0]

        return Matrix4x4.from_rows(row0, row1, row2, row3)

    def inverse(self) -> "Transform":
        """
        Menghitung inversi matematis penuh dari transformasi objek secara non-destruktif.
        Membongkar rotasi Hamiltonian secara analitis untuk menjamin kepatuhan ACTS-000-008.
        """
        inv_rot = self.rotation.conjugate()
        s = self.scale
        t = self.translation

        # Proteksi divisi dengan angka nol sebelum proses inversi komponen skala
        if abs(s.x) < 1e-24 or abs(s.y) < 1e-24 or abs(s.z) < 1e-24:
            logger.error("TRANSFORM_INVERSE_SCALE_SINGULARITY: sx=%s sy=%s sz=%s", s.x, s.y, s.z)
            raise ValueError("NUMERICAL_SINGULARITY_SCALE_COMPONENTS_TOO_CLOSE_TO_ZERO")

        # Vektor hasil bagi komponen pergeseran terhadap skala dasar
        tx_s = Vector(x=t.x / s.x, y=t.y / s.y, z=t.z / s.z)

        # Rotasi konjugasi Hamiltonian murni terhadap titik spasial: v' = q * v * q*
        q = inv_rot
        vx, vy, vz = tx_s.x, tx_s.y, tx_s.z

        # Perkalian biner q * v (w=0 secara implisit)
        t1_w = -q.x * vx - q.y * vy - q.z * vz
        t1_x =  q.w * vx + q.y * vz - q.z * vy
        t1_y =  q.w * vy + q.z * vx - q.x * vz
        t1_z =  q.w * vz + q.x * vy - q.y * vx

        # Hasil akhir t1 dikalikan q_conjugate (di mana q* = self.rotation)
        q_conj = self.rotation
        inv_tx = t1_w * q_conj.x + t1_x * q_conj.w + t1_y * q_conj.z - t1_z * q_conj.y
        inv_ty = t1_w * q_conj.y - t1_x * q_conj.z + t1_y * q_conj.w + t1_z * q_conj.x
        inv_tz = t1_w * q_conj.z + t1_x * q_conj.y - t1_y * q_conj.x + t1_z * q_conj.w

        # Inversi skala fisis
        inv_sx = 1.0 / s.x
        inv_sy = 1.0 / s.y
        inv_sz = 1.0 / s.z

        return Transform(
            translation=Vector(x=-inv_tx, y=-inv_ty, z=-inv_tz),
            rotation=inv_rot,
            scale=Vector(x=inv_sx, y=inv_sy, z=inv_sz),
        )

    def apply_to_point(self, point: Any) -> Coordinate:
        """
        Mentransformasikan posisi titik koordinat 3D ke ruang dimensi baru via perkalian matriks homogen.
        """
        if not isinstance(point, Coordinate):
            logger.error("TRANSFORM_APPLY_TO_POINT_NON_COORDINATE: %r", point)
            raise TypeError("TRANSFORM_OPERATION_VIOLATION_TARGET_MUST_BE_A_PURE_COORDINATE_INSTANCE")
        m = self.to_matrix()
        return m * point

    def approximately_equal(self, other: Any, epsilon: Any = 1e-6) -> bool:
        if not isinstance(other, Transform):
            return False
        if isinstance(epsilon, bool) or not isinstance(epsilon, (int, float)):
            logger.error("TRANSFORM_APPROX_EPSILON_REJECTED: %r", epsilon)
            raise TypeError("EPSILON_TOLERANCE_MUST_BE_A_PURE_NUMERIC_TYPE")
        return (
            self.translation.approximately_equal(other.translation, epsilon) and
            self.rotation.approximately_equal(other.rotation, epsilon) and
            self.scale.approximately_equal(other.scale, epsilon)
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Transform):
            return False
        return (
            self.translation == other.translation and
            self.rotation == other.rotation and
            self.scale == other.scale
        )

    def __repr__(self) -> str:
        return f"Transform(translation={self.translation}, rotation={self.rotation}, scale={self.scale})"