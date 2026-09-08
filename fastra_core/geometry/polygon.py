# fastra_core\geometry\polygon.py

from __future__ import annotations

import logging
import math
from typing import Any, List, Optional

from fastra_core.spatial.coordinate import Coordinate
from fastra_core.primitives.area import Area
from fastra_core.tolerance import EPSILON_LENGTH

logger = logging.getLogger("fastra.geometry.polygon")


def is_closed(polygon: Any, epsilon: float = EPSILON_LENGTH) -> bool:
    """
    Memverifikasi apakah rangkaian titik sudut poligon tertutup secara spasial.
    Mengevaluasi kesamaan absolut antara koordinat awal dan akhir.
    """
    if not isinstance(polygon, list):
        logger.error("POLYGON_IS_CLOSED_REJECTED_NON_LIST: %r", polygon)
        raise TypeError("POLYGON_MUST_BE_A_VALID_LIST_OF_COORDINATES")

    n = len(polygon)
    if n < 3:
        return False

    for idx, vertex in enumerate(polygon):
        if not isinstance(vertex, Coordinate):
            logger.error("POLYGON_ELEMENT_AT_INDEX_%d_NOT_COORDINATE: %r", idx, vertex)
            raise TypeError(f"POLYGON_ELEMENT_AT_INDEX_{idx}_MUST_BE_A_PURE_COORDINATE_INSTANCE")

    return polygon[0].approximately_equal(polygon[-1], epsilon)


def area(polygon: Any) -> Area:
    """
    Menghitung luas penampang poligon menggunakan rumus tali sepatu Shoelace Gauss.
    Menerapkan perlindungan anti-crash dan validasi penutupan spasial secara fail-fast.
    """
    if not isinstance(polygon, list):
        logger.error("POLYGON_AREA_REJECTED_NON_LIST: %r", polygon)
        raise TypeError("POLYGON_MUST_BE_A_VALID_LIST_OF_COORDINATES")

    if not is_closed(polygon):
        logger.error("POLYGON_AREA_REJECTED_NOT_CLOSED")
        raise ValueError("GEOMETRIC_INTEGRITY_VIOLATION_POLYGON_IS_NOT_CLOSED")

    n = len(polygon)
    shoelace_sum = 0.0

    for i in range(n - 1):
        x1, y1 = polygon[i].x, polygon[i].y
        x2, y2 = polygon[i + 1].x, polygon[i + 1].y

        shoelace_sum += (x1 * y2 - x2 * y1)

    if math.isnan(shoelace_sum) or math.isinf(shoelace_sum):
        logger.error("POLYGON_AREA_NUMERIC_ANOMALY: %s", shoelace_sum)
        raise ValueError("NUMERIC_ANOMALY_DETECTED_POLYGON_AREA_CALCULATION_CORRUPTED")

    calculated_value = abs(shoelace_sum) / 2.0
    return Area(value=calculated_value)


def contains_point(polygon: Any, point: Any) -> bool:
    """
    Mendeteksi apakah titik koordinat berada di dalam batas perimeter poligon.
    Menggunakan algoritma Ray-Casting Jordan modern yang terproteksi dari ancaman Division-by-Zero.
    """
    if not isinstance(polygon, list):
        logger.error("POLYGON_CONTAINS_POINT_REJECTED_NON_LIST: %r", polygon)
        raise TypeError("POLYGON_MUST_BE_A_VALID_LIST_OF_COORDINATES")

    if not is_closed(polygon):
        logger.error("POLYGON_CONTAINS_POINT_REJECTED_NOT_CLOSED")
        raise ValueError("GEOMETRIC_INTEGRITY_VIOLATION_POLYGON_IS_NOT_CLOSED")

    if not isinstance(point, Coordinate):
        logger.error("POLYGON_CONTAINS_POINT_REJECTED_NON_COORDINATE: %r", point)
        raise TypeError("TARGET_POINT_MUST_BE_AN_INSTANCE_OF_COORDINATE_CLASS")

    n = len(polygon)
    inside = False
    x, y = point.x, point.y

    for i in range(n - 1):
        x1, y1 = polygon[i].x, polygon[i].y
        x2, y2 = polygon[i + 1].x, polygon[i + 1].y

        # Proteksi total ray-casting terhadap segmen horizontal dan pembagian dengan nol
        if (y1 > y) != (y2 > y):
            denom = y2 - y1
            if abs(denom) > 1e-12:
                intersect_x = (x2 - x1) * (y - y1) / denom + x1
                if x < intersect_x:
                    inside = not inside

    return inside


def is_convex(polygon: Any) -> bool:
    """
    Mengevaluasi apakah struktur poligon bersifat konveks (cembung sempurna).
    Memanfaatkan pengujian tanda arah perkalian silang komponen 2D secara rigid.
    """
    if not isinstance(polygon, list):
        logger.error("POLYGON_IS_CONVEX_REJECTED_NON_LIST: %r", polygon)
        raise TypeError("POLYGON_MUST_BE_A_VALID_LIST_OF_COORDINATES")

    if not is_closed(polygon):
        logger.error("POLYGON_IS_CONVEX_REJECTED_NOT_CLOSED")
        raise ValueError("GEOMETRIC_INTEGRITY_VIOLATION_POLYGON_IS_NOT_CLOSED")

    n = len(polygon)
    if n < 4:  # Minimal segitiga bertutup (3 simpul unik + 1 simpul tutup = 4 elemen)
        return True

    sign: Optional[bool] = None

    for i in range(n - 1):
        p0 = polygon[i]
        p1 = polygon[(i + 1) % (n - 1)]
        p2 = polygon[(i + 2) % (n - 1)]

        # Menghitung komponen silang arah z bidang datar (2D Cross Product Analog)
        dx1, dy1 = p1.x - p0.x, p1.y - p0.y
        dx2, dy2 = p2.x - p1.x, p2.y - p1.y

        cross_z = dx1 * dy2 - dy1 * dx2

        if abs(cross_z) < EPSILON_LENGTH:
            continue

        current_sign = cross_z > 0.0

        if sign is None:
            sign = current_sign
        elif sign != current_sign:
            return False

    return True


def is_self_intersecting(polygon: Any) -> bool:
    """
    Mendeteksi keberadaan interseksi mandiri (Self-Intersection/Bow-Tie anomaly)
    pada rangkaian segmen pembentuk perimeter poligon secara non-rekursif.
    """
    if not isinstance(polygon, list):
        logger.error("POLYGON_SELF_INTERSECT_REJECTED_NON_LIST: %r", polygon)
        raise TypeError("POLYGON_MUST_BE_A_VALID_LIST_OF_COORDINATES")

    n = len(polygon)
    if n < 4:
        return False

    for idx, vertex in enumerate(polygon):
        if not isinstance(vertex, Coordinate):
            logger.error("POLYGON_SELF_INTERSECT_ELEMENT_AT_INDEX_%d_NOT_COORDINATE: %r", idx, vertex)
            raise TypeError(f"POLYGON_ELEMENT_AT_INDEX_{idx}_MUST_BE_A_PURE_COORDINATE_INSTANCE")

    def on_segment(p: Coordinate, q: Coordinate, r: Coordinate) -> bool:
        return (q.x <= max(p.x, r.x) and q.x >= min(p.x, r.x) and
                q.y <= max(p.y, r.y) and q.y >= min(p.y, r.y))

    def orientation(p: Coordinate, q: Coordinate, r: Coordinate) -> int:
        val = (q.y - p.y) * (r.x - q.x) - (q.x - p.x) * (r.y - q.y)
        if abs(val) < 1e-12:
            return 0
        return 1 if val > 0.0 else 2

    def do_intersect(p1: Coordinate, q1: Coordinate, p2: Coordinate, q2: Coordinate) -> bool:
        o1 = orientation(p1, q1, p2)
        o2 = orientation(p1, q1, q2)
        o3 = orientation(p2, q2, p1)
        o4 = orientation(p2, q2, q1)

        if o1 != o2 and o3 != o4:
            return True

        if o1 == 0 and on_segment(p1, p2, q1):
            return True
        if o2 == 0 and on_segment(p1, q2, q1):
            return True
        if o3 == 0 and on_segment(p2, p1, q2):
            return True
        if o4 == 0 and on_segment(p2, q1, q2):
            return True

        return False

    for i in range(n - 1):
        for j in range(i + 1, n - 1):
            # Mengabaikan segmen bersebelahan yang berbagi simpul identik secara legal
            if j == i + 1 or (i == 0 and j == n - 2):
                continue
            if do_intersect(polygon[i], polygon[i + 1], polygon[j], polygon[j + 1]):
                return True

    return False