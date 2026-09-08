# fastra_core\geometry\fundamental.py

from __future__ import annotations

import logging
from decimal import Decimal
import math
from typing import Any

from fastra_core.spatial.coordinate import Coordinate
from fastra_core.spatial.vector import Vector
from fastra_core.primitives.length import Length
from fastra_core.primitives.area import Area

logger = logging.getLogger("fastra.geometry.fundamental")


def distance(p1: Any, p2: Any) -> Length:
    """
    Menghitung jarak spasial absolut antara dua titik koordinat.
    Menerapkan strict fail-fast validation tipe terikat sejak hulu eksekusi.
    """
    if not isinstance(p1, Coordinate) or not isinstance(p2, Coordinate):
        logger.error("DISTANCE_INPUT_TYPE_VIOLATION: p1=%r p2=%r", p1, p2)
        raise TypeError("GEOMETRY_TYPE_VIOLATION_INPUTS_MUST_BE_PURE_COORDINATE_INSTANCES")

    return p1.distance_to(p2)


def midpoint(p1: Any, p2: Any) -> Coordinate:
    """
    Menghitung titik tengah (midpoint) geometris antara dua koordinat ruang 3D.
    Menghalau celah coercion hacks data boolean secara rigid.
    """
    if not isinstance(p1, Coordinate) or not isinstance(p2, Coordinate):
        logger.error("MIDPOINT_INPUT_TYPE_VIOLATION: p1=%r p2=%r", p1, p2)
        raise TypeError("GEOMETRY_TYPE_VIOLATION_INPUTS_MUST_BE_PURE_COORDINATE_INSTANCES")

    mid_x = (p1.x + p2.x) / 2.0
    mid_y = (p1.y + p2.y) / 2.0
    mid_z = (p1.z + p2.z) / 2.0

    if (
        math.isnan(mid_x) or math.isinf(mid_x)
        or math.isnan(mid_y) or math.isinf(mid_y)
        or math.isnan(mid_z) or math.isinf(mid_z)
    ):
        logger.error(
            "MIDPOINT_NUMERIC_ANOMALY: x=%s y=%s z=%s",
            mid_x,
            mid_y,
            mid_z,
        )
        raise ValueError("NUMERIC_ANOMALY_DETECTED_MIDPOINT_CALVERS_CANNOT_BE_NAN_OR_INFINITE")

    return Coordinate(x=mid_x, y=mid_y, z=mid_z)


def cross_product(v1: Any, v2: Any) -> Vector:
    """
    Menghitung perkalian silang (cross product) vektor 3D untuk menentukan ortogonalitas ruang.
    """
    if not isinstance(v1, Vector) or not isinstance(v2, Vector):
        logger.error("CROSS_PRODUCT_INPUT_TYPE_VIOLATION: v1=%r v2=%r", v1, v2)
        raise TypeError("GEOMETRY_TYPE_VIOLATION_INPUTS_MUST_BE_PURE_VECTOR_INSTANCES")

    return v1.cross(v2)


def dot_product(v1: Any, v2: Any) -> float:
    """
    Menghitung perkalian titik (dot product) antara dua entitas vektor.
    """
    if not isinstance(v1, Vector) or not isinstance(v2, Vector):
        logger.error("DOT_PRODUCT_INPUT_TYPE_VIOLATION: v1=%r v2=%r", v1, v2)
        raise TypeError("GEOMETRY_TYPE_VIOLATION_INPUTS_MUST_BE_PURE_VECTOR_INSTANCES")

    result = v1.dot(v2)
    if isinstance(result, bool):
        logger.error("DOT_PRODUCT_RESULT_BOOLEAN: %r", result)
        raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
    if not isinstance(result, (int, float)):
        logger.error("DOT_PRODUCT_RESULT_NON_NUMERIC: %r", result)
        raise TypeError("DOT_PRODUCT_RESULT_MUST_BE_PURE_NUMERIC_TYPE")
    if math.isnan(float(result)) or math.isinf(float(result)):
        logger.error("DOT_PRODUCT_RESULT_NAN_OR_INF: %s", result)
        raise ValueError("NUMERIC_ANOMALY_DETECTED_DOT_PRODUCT_CANNOT_BE_NAN_OR_INFINITE")

    return float(result)


def normalize(v: Any) -> Vector:
    """
    Menormalisasi arah vektor ke dalam bentuk unit komponen panjang absolut dasar.
    """
    if not isinstance(v, Vector):
        logger.error("NORMALIZE_INPUT_TYPE_VIOLATION: %r", v)
        raise TypeError("GEOMETRY_TYPE_VIOLATION_INPUT_MUST_BE_A_PURE_VECTOR_INSTANCE")

    return v.normalize()


def area_of_triangle(p1: Any, p2: Any, p3: Any) -> Area:
    """
    Menghitung luas permukaan segitiga 3D menggunakan norma magnitude perkalian silang vektor.
    Menolak bypass coercion hacks dan mengunci integritas kalkulasi spasial QS.
    """
    if not isinstance(p1, Coordinate) or not isinstance(p2, Coordinate) or not isinstance(p3, Coordinate):
        logger.error(
            "TRIANGLE_AREA_INPUT_TYPE_VIOLATION: p1=%r p2=%r p3=%r",
            p1,
            p2,
            p3,
        )
        raise TypeError("GEOMETRY_TYPE_VIOLATION_INPUTS_MUST_BE_PURE_COORDINATE_INSTANCES")

    # Menggunakan representasi operator overloading formal yang aman
    v1: Vector = p2 - p1
    v2: Vector = p3 - p1

    cross_result: Vector = v1.cross(v2)
    length_magnitude: Length = cross_result.magnitude()

    # Menghitung perkalian skalar luas secara aman via method murni primitive value object
    calculated_area: Area = Area(value=Decimal("0.5") * length_magnitude.value)
    return calculated_area