# fastra_core\spatial\matrix4x4.py

from __future__ import annotations

import logging
import math
from typing import Any, List, Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra_core.spatial.matrix4x4")


class Matrix4x4(BaseModel):
    """
    Primitive Value Object Spasial untuk representasi Matriks Transformasi 4x4.
    Menjamin imutabilitas penuh di level memori terendah dengan memetakan array ke tipe Tuple.
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
                raise TypeError("Matrix4x4 only accepts a single positional argument for elements")
            kwargs.setdefault("elements", args[0])
        super().__init__(**kwargs)

    elements: Tuple[float, ...] = Field(
        ...,
        description="16 elemen matriks bertipe float dalam susunan column-major order",
    )

    @field_validator("elements", mode="before")
    @classmethod
    def validate_and_compress_matrix_elements(cls, value: Any) -> Tuple[float, ...]:
        if isinstance(value, (list, tuple)):
            if len(value) != 16:
                logger.error("MATRIX_SIZE_VIOLATION: expected 16, got %d", len(value))
                raise ValueError("MATRIX_SIZE_VIOLATION_MUST_CONTAIN_EXACTLY_16_ELEMENTS")

            clean_elements: List[float] = []
            for idx, e in enumerate(value):
                if isinstance(e, bool):
                    logger.error("MATRIX_ELEMENT_AT_INDEX_%d_REJECTED_BOOLEAN: %r", idx, e)
                    raise TypeError(f"DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED_AT_INDEX_{idx}")
                if not isinstance(e, (int, float)):
                    logger.error("MATRIX_ELEMENT_AT_INDEX_%d_REJECTED_NON_NUMERIC: %r", idx, e)
                    raise TypeError(f"MATRIX_ELEMENT_MUST_BE_PURE_NUMERIC_AT_INDEX_{idx}")

                float_val = float(e)
                if math.isnan(float_val) or math.isinf(float_val):
                    logger.error("MATRIX_ELEMENT_AT_INDEX_%d_REJECTED_NAN_OR_INF: %s", idx, float_val)
                    raise ValueError(f"NUMERIC_ANOMALY_DETECTED_AT_INDEX_{idx}_CANNOT_BE_NAN_OR_INFINITE")
                clean_elements.append(float_val)

            return tuple(clean_elements)

        logger.error("MATRIX_ELEMENTS_REJECTED_INVALID_CONTAINER: %r", value)
        raise TypeError("MATRIX_ELEMENTS_MUST_BE_PROVIDED_IN_A_VALID_COLLECTION_CONTAINER")

    @classmethod
    def identity(cls) -> "Matrix4x4":
        """
        Named constructor untuk menghasilkan matriks identitas 4x4 standar.
        """
        return cls(elements=(
            1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0,
        ))

    @classmethod
    def from_rows(
        cls,
        r0: Any,
        r1: Any,
        r2: Any,
        r3: Any,
    ) -> "Matrix4x4":
        """
        Membangun objek Matriks 4x4 dari 4 susunan baris horizontal.
        Otomatis ditransformasikan ke bentuk internal column-major order.
        """
        rows = (r0, r1, r2, r3)
        for r_idx, row in enumerate(rows):
            if not isinstance(row, (list, tuple)) or len(row) != 4:
                logger.error("ROW_SIZE_VIOLATION_AT_ROW_%d: %r", r_idx, row)
                raise ValueError(f"ROW_SIZE_VIOLATION_AT_ROW_{r_idx}_MUST_CONTAIN_EXACTLY_4_ELEMENTS")

        return cls(elements=(
            r0[0], r1[0], r2[0], r3[0],
            r0[1], r1[1], r2[1], r3[1],
            r0[2], r1[2], r2[2], r3[2],
            r0[3], r1[3], r2[3], r3[3],
        ))

    def get_element(self, row: Any, col: Any) -> float:
        """
        Mengakses nilai elemen individual secara aman berdasarkan koordinat baris dan kolom.
        """
        if isinstance(row, bool) or isinstance(col, bool):
            logger.error("MATRIX_INDEX_BOOLEAN_REJECTED: row=%r col=%r", row, col)
            raise TypeError("MATRIX_INDEX_MUST_BE_A_PURE_INTEGER_TYPE")
        if not isinstance(row, int) or not isinstance(col, int):
            logger.error("MATRIX_INDEX_NON_INTEGER_REJECTED: row=%r col=%r", row, col)
            raise TypeError("MATRIX_INDEX_MUST_BE_A_PURE_INTEGER_TYPE")
        if not (0 <= row <= 3) or not (0 <= col <= 3):
            logger.error("MATRIX_BOUNDARY_VIOLATION: row=%d col=%d", row, col)
            raise IndexError("MATRIX_BOUNDARY_VIOLATION_INDEX_OUT_OF_RANGE_0_TO_3")
        return self.elements[col * 4 + row]

    def to_row_major(self) -> List[float]:
        """
        Mengekspor representasi elemen internal ke dalam format row-major list.
        """
        return [
            self.get_element(0, 0), self.get_element(0, 1), self.get_element(0, 2), self.get_element(0, 3),
            self.get_element(1, 0), self.get_element(1, 1), self.get_element(1, 2), self.get_element(1, 3),
            self.get_element(2, 0), self.get_element(2, 1), self.get_element(2, 2), self.get_element(2, 3),
            self.get_element(3, 0), self.get_element(3, 1), self.get_element(3, 2), self.get_element(3, 3),
        ]

    def transpose(self) -> "Matrix4x4":
        """
        Melakukan operasi transposisi posisi baris menjadi kolom.
        """
        m = self.elements
        return Matrix4x4(elements=(
            m[0], m[4], m[8], m[12],
            m[1], m[5], m[9], m[13],
            m[2], m[6], m[10], m[14],
            m[3], m[7], m[11], m[15],
        ))

    def __mul__(self, other: Any) -> Any:
        """
        Operator overloading perkalian matriks homogen biner terikat.
        """
        if isinstance(other, Matrix4x4):
            return self._multiply_matrix(other)

        # Local imports to prevent circular dependency at module load time.
        from fastra_core.spatial.coordinate import Coordinate
        from fastra_core.spatial.vector import Vector

        if isinstance(other, (Coordinate, Vector)):
            return self._multiply_spatial_object(other)

        logger.error("MATRIX_MUL_UNSUPPORTED_OPERAND_TYPE: %r", other)
        raise TypeError(f"ALGEBRAIC_TYPE_VIOLATION_CANNOT_MULTIPLY_MATRIX4X4_WITH_{type(other)}")

    def _multiply_matrix(self, other: Any) -> "Matrix4x4":
        if not isinstance(other, Matrix4x4):
            logger.error("MATRIX_MULTIPLY_INTERNAL_TYPE_VIOLATION: %r", other)
            raise TypeError("MATRIX_MULTIPLICATION_OPERAND_MUST_BE_MATRIX4X4")
        result_flat: List[float] = []
        for col in range(4):
            for row in range(4):
                sum_accumulator = 0.0
                for k in range(4):
                    sum_accumulator += self.get_element(row, k) * other.get_element(k, col)
                result_flat.append(sum_accumulator)
        return Matrix4x4(elements=result_flat)

    def _multiply_spatial_object(self, v: Any) -> Any:
        """
        Mengalikan matriks transformasi dengan entitas spasial 3D (w=1 secara implisit).
        Memelihara pengembalian tipe kelas asal (Coordinate/Vector) tanpa memicu degradasi data.
        """
        x_calc = self.get_element(0, 0) * v.x + self.get_element(0, 1) * v.y + self.get_element(0, 2) * v.z + self.get_element(0, 3)
        y_calc = self.get_element(1, 0) * v.x + self.get_element(1, 1) * v.y + self.get_element(1, 2) * v.z + self.get_element(1, 3)
        z_calc = self.get_element(2, 0) * v.x + self.get_element(2, 1) * v.y + self.get_element(2, 2) * v.z + self.get_element(2, 3)
        w_calc = self.get_element(3, 0) * v.x + self.get_element(3, 1) * v.y + self.get_element(3, 2) * v.z + self.get_element(3, 3)

        if abs(w_calc) > 1e-12:
            return type(v)(x=x_calc / w_calc, y=y_calc / w_calc, z=z_calc / w_calc)
        return type(v)(x=x_calc, y=y_calc, z=z_calc)

    def inverse(self) -> "Matrix4x4":
        """
        Pendelegasian operasi penghitungan invers matriks secara aman ke modul numerik pusat.
        Menghilangkan redudansi kode algoritmik lokal yang rapuh.
        """
        from fastra_core.numerical.matrix import inverse_matrix

        return inverse_matrix(m=self)

    def approximately_equal(self, other: Any, epsilon: Any = 1e-6) -> bool:
        if not isinstance(other, Matrix4x4):
            return False
        if isinstance(epsilon, bool) or not isinstance(epsilon, (int, float)):
            logger.error("MATRIX_APPROX_EPSILON_REJECTED: %r", epsilon)
            raise TypeError("EPSILON_TOLERANCE_MUST_BE_A_PURE_NUMERIC_TYPE")
        return all(abs(a - b) <= epsilon for a, b in zip(self.elements, other.elements))

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Matrix4x4):
            return False
        return self.elements == other.elements

    def __repr__(self) -> str:
        return f"Matrix4x4(elements={list(self.elements)})"