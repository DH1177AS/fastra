import math
from typing import List
from fastra_core.spatial.coordinate import Coordinate
from fastra_core.primitives.area import Area

def orient2d(a: Coordinate, b: Coordinate, c: Coordinate) -> float:
    return (a.x - c.x) * (b.y - c.y) - (a.y - c.y) * (b.x - c.x)

def point_in_polygon(polygon: List[Coordinate], point: Coordinate) -> bool:
    n = len(polygon)
    inside = False
    x, y = point.x, point.y
    for i in range(n - 1):
        x1, y1 = polygon[i].x, polygon[i].y
        x2, y2 = polygon[i+1].x, polygon[i+1].y
        if ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1) + x1):
            inside = not inside
    return inside

def polygon_area(polygon: List[Coordinate]) -> Area:
    if len(polygon) < 3:
        return Area(0.0)
    s = 0.0
    n = len(polygon)
    for i in range(n - 1):
        s += (polygon[i].x * polygon[i+1].y - polygon[i+1].x * polygon[i].y)
    return Area(abs(s) / 2.0)

def closest_point_on_segment(p: Coordinate, a: Coordinate, b: Coordinate) -> Coordinate:
    abx, aby, abz = b.x - a.x, b.y - a.y, b.z - a.z
    apx, apy, apz = p.x - a.x, p.y - a.y, p.z - a.z
    t = (apx*abx + apy*aby + apz*abz) / (abx*abx + aby*aby + abz*abz + 1e-30)
    t = max(0.0, min(1.0, t))
    return Coordinate(a.x + t*abx, a.y + t*aby, a.z + t*abz)
