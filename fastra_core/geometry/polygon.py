from fastra_core.spatial.coordinate import Coordinate
from fastra_core.primitives.area import Area
from fastra_core.tolerance import EPSILON_LENGTH

def is_closed(polygon, epsilon=EPSILON_LENGTH):
    if len(polygon) < 3: return False
    return polygon[0].approximately_equal(polygon[-1], epsilon)

def area(polygon):
    if not is_closed(polygon): raise ValueError("Polygon tidak tertutup")
    n = len(polygon)
    s = 0.0
    for i in range(n-1):
        x1, y1 = polygon[i].x, polygon[i].y
        x2, y2 = polygon[i+1].x, polygon[i+1].y
        s += (x1 * y2 - x2 * y1)
    return Area(abs(s) / 2.0)

def contains_point(polygon, point):
    if not is_closed(polygon): raise ValueError("Polygon tidak tertutup")
    n = len(polygon)
    inside = False
    x, y = point.x, point.y
    for i in range(n-1):
        x1, y1 = polygon[i].x, polygon[i].y
        x2, y2 = polygon[i+1].x, polygon[i+1].y
        if ((y1 > y) != (y2 > y)) and (x < (x2-x1)*(y-y1)/(y2-y1) + x1):
            inside = not inside
    return inside

def is_convex(polygon):
    if not is_closed(polygon): raise ValueError("Polygon tidak tertutup")
    n = len(polygon)
    sign = None
    for i in range(n-1):
        p0, p1, p2 = polygon[i], polygon[(i+1)%(n-1)], polygon[(i+2)%(n-1)]
        v1 = p1 - p0
        v2 = p2 - p1
        cross_z = v1.dx * v2.dy - v1.dy * v2.dx
        if abs(cross_z) < EPSILON_LENGTH: continue
        cur = cross_z > 0
        if sign is None: sign = cur
        elif sign != cur: return False
    return True


def is_self_intersecting(polygon) -> bool:
    """Deteksi sederhana apakah polygon self-intersecting (bow-tie)."""
    if len(polygon) < 4:
        return False
    def on_segment(p, q, r):
        if (q.x <= max(p.x, r.x) and q.x >= min(p.x, r.x) and
            q.y <= max(p.y, r.y) and q.y >= min(p.y, r.y)):
            return True
        return False
    def orientation(p, q, r):
        val = (q.y - p.y) * (r.x - q.x) - (q.x - p.x) * (r.y - q.y)
        if val == 0: return 0
        return 1 if val > 0 else 2
    def do_intersect(p1, q1, p2, q2):
        o1 = orientation(p1, q1, p2)
        o2 = orientation(p1, q1, q2)
        o3 = orientation(p2, q2, p1)
        o4 = orientation(p2, q2, q1)
        if o1 != o2 and o3 != o4:
            return True
        if o1 == 0 and on_segment(p1, p2, q1): return True
        if o2 == 0 and on_segment(p1, q2, q1): return True
        if o3 == 0 and on_segment(p2, p1, q2): return True
        if o4 == 0 and on_segment(p2, q1, q2): return True
        return False
    n = len(polygon)
    for i in range(n-1):
        for j in range(i+1, n-1):
            # lewati segmen yang bersebelahan (berbagi titik sudut) dan
            # pasangan sisi pertama dengan terakhir (bertemu di titik awal)
            if j == i + 1 or (i == 0 and j == n - 2):
                continue
            if do_intersect(polygon[i], polygon[i+1], polygon[j], polygon[j+1]):
                return True
    return False
