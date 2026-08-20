from fastra_core.spatial.coordinate import Coordinate
from fastra_core.spatial.vector import Vector
from fastra_core.primitives.length import Length
from fastra_core.primitives.area import Area

def distance(p1, p2): return p1.distance_to(p2)
def midpoint(p1, p2): return Coordinate((p1.x+p2.x)/2, (p1.y+p2.y)/2, (p1.z+p2.z)/2)
def cross_product(v1, v2): return v1.cross(v2)
def dot_product(v1, v2): return v1.dot(v2)
def normalize(v): return v.normalize()
def area_of_triangle(p1, p2, p3):
    v1 = p2 - p1
    v2 = p3 - p1
    cross = v1.cross(v2)
    return Area(0.5 * cross.magnitude().value)
