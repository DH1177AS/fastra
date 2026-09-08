# fastra_core/numerical/geometry.py

from __future__ import annotations

import logging
import math
from typing import Any, List

from fastra_core.spatial.coordinate import Coordinate
from fastra_core.primitives.area import Area
from fastra_core.tolerance import EPSILON_LENGTH

logger = logging.getLogger("fastra.numerical.geometry")


def orient2d(a: Any, b: Any, c: Any) -> float:
    """
    Menghitung orientasi 2D (Predikat Robust Determinant) tiga titik koordinat.
    Mengembalikan nilai positif (berlawanan jarum jam), negatif (searah), atau nol (kolinear).
    """
    if not isinstance(a, Coordinate) or not isinstance(b, Coordinate) or not isinstance(c, Coordinate):
        logger.error("ORIENT2D_INPUT_TYPE_VIOLATION: a=%r b=%r c=%r", a, b, c)
        raise TypeError("NUMERICAL_GEOMETRY_TYPE_VIOLATION_INPUTS_MUST_BE_PURE_COORDINATE_INSTANCES")

    determinant = (a.x - c.x) * (b.y - c.y) - (a.y - c.y) * (b.x - c.x)

    if isinstance(determinant, bool):
        logger.error("ORIENT2D_RESULT_BOOLEAN: %r", determinant)
        raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
    if math.isnan(determinant) or math.isinf(determinant):
        logger.error("ORIENT2D_RESULT_NAN_OR_INF: %s", determinant)
        raise ValueError("NUMERIC_ANOMALY_DETECTED_DETERMINANT_CALCULATIONS_CORRUPTED")

    return float(determinant)


def point_in_polygon(polygon: Any, point: Any) -> bool:
    """
    Menentukan apakah sebuah titik berada di dalam poligon menggunakan metode ray casting.
    Mendukung poligon yang diwakili sebagai list of Coordinate (atau tuple (x,y)).
    """
    # Normalisasi input menjadi list of Coordinate
    if not isinstance(polygon, (list, tuple)):
        raise TypeError("POLYGON_INPUT_MUST_BE_A_VALID_LIST_OF_COORDINATES")
    if not polygon:
        return False

    # Jika elemen sudah berupa Coordinate, gunakan langsung; jika tidak, coba konversi dari tuple
    if isinstance(polygon[0], Coordinate):
        coords = polygon
    else:
        try:
            coords = [Coordinate(p[0], p[1]) for p in polygon]
        except (TypeError, IndexError) as exc:
            raise TypeError("POLYGON_ELEMENTS_MUST_BE_COORDINATES_OR_TUPLES") from exc

    if not isinstance(point, Coordinate):
        try:
            point = Coordinate(point[0], point[1])
        except (TypeError, IndexError) as exc:
            raise TypeError("POINT_MUST_BE_COORDINATE_OR_TUPLE") from exc

    n = len(coords)
    if n < 3:
        return False

    inside = False
    px, py = float(point.x), float(point.y)

    # Ray casting
    for i in range(n):
        x1, y1 = float(coords[i].x), float(coords[i].y)
        x2, y2 = float(coords[(i + 1) % n].x), float(coords[(i + 1) % n].y)

        if ((y1 > py) != (y2 > py)) and (
            px < (x2 - x1) * (py - y1) / (y2 - y1 + 1e-12) + x1
        ):
            inside = not inside

    return inside


def polygon_area(polygon: Any) -> Area:
    """
    Menghitung luas poligon sederhana (tidak self-intersecting) dengan formula shoelace.
    Mendukung list of Coordinate atau list of tuple (x,y).
    """
    if not isinstance(polygon, (list, tuple)):
        raise TypeError("POLYGON_INPUT_MUST_BE_A_VALID_LIST_OF_COORDINATES")
    if len(polygon) < 3:
        return Area(value=0.0)

    if isinstance(polygon[0], Coordinate):
        coords = polygon
    else:
        try:
            coords = [Coordinate(p[0], p[1]) for p in polygon]
        except (TypeError, IndexError) as exc:
            raise TypeError("POLYGON_ELEMENTS_MUST_BE_COORDINATES_OR_TUPLES") from exc

    n = len(coords)
    area_sum = 0.0
    for i in range(n):
        x1, y1 = float(coords[i].x), float(coords[i].y)
        x2, y2 = float(coords[(i + 1) % n].x), float(coords[(i + 1) % n].y)
        area_sum += x1 * y2 - x2 * y1

    area_val = abs(area_sum) / 2.0
    if math.isnan(area_val) or math.isinf(area_val):
        raise ValueError("NUMERIC_ANOMALY_DETECTED_POLYGON_AREA_CORRUPTED")

    return Area(value=area_val)


def point_in_polygon_robust(polygon: Any, point: Any) -> bool:
    """Alias aman untuk point_in_polygon dengan validasi penuh."""
    return point_in_polygon(polygon, point)


def polygon_area_robust(polygon: Any) -> Area:
    """Alias aman untuk polygon_area dengan validasi penuh."""
    return polygon_area(polygon)


def closest_point_on_segment(p: Any, a: Any, b: Any) -> Coordinate:
    """
    Menghitung titik koordinat terdekat pada segmen garis lurus [A, B] dari titik acuan P.
    """
    if not isinstance(p, Coordinate) or not isinstance(a, Coordinate) or not isinstance(b, Coordinate):
        raise TypeError("NUMERICAL_GEOMETRY_TYPE_VIOLATION_INPUTS_MUST_BE_PURE_COORDINATE_INSTANCES")

    abx, aby, abz = b.x - a.x, b.y - a.y, b.z - a.z
    apx, apy, apz = p.x - a.x, p.y - a.y, p.z - a.z

    segment_length_squared = abx * abx + aby * aby + abz * abz

    if abs(segment_length_squared) < (EPSILON_LENGTH * EPSILON_LENGTH):
        return Coordinate(x=a.x, y=a.y, z=a.z)

    t = (apx * abx + apy * aby + apz * abz) / segment_length_squared
    t_clamped = max(0.0, min(1.0, t))

    final_x = a.x + t_clamped * abx
    final_y = a.y + t_clamped * aby
    final_z = a.z + t_clamped * abz

    if (
        math.isnan(final_x) or math.isinf(final_x)
        or math.isnan(final_y) or math.isinf(final_y)
        or math.isnan(final_z) or math.isinf(final_z)
    ):
        raise ValueError("NUMERIC_ANOMALY_DETECTED_CLOSEST_POINT_COORDINATES_CORRUPTED")

    return Coordinate(x=final_x, y=final_y, z=final_z)