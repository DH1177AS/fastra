import math
from fastra_core.geometry.fundamental import distance, midpoint, cross_product, dot_product, area_of_triangle
from fastra_core.spatial.coordinate import Coordinate
from fastra_core.spatial.vector import Vector

def test_distance():
    p1 = Coordinate(0,0,0)
    p2 = Coordinate(3,4,0)
    d = distance(p1, p2)
    assert d.approximately_equal(d.__class__(5.0))

def test_midpoint():
    p1 = Coordinate(0,0,0)
    p2 = Coordinate(2,2,0)
    m = midpoint(p1, p2)
    assert m.approximately_equal(Coordinate(1,1,0))

def test_cross_product():
    v1 = Vector(1,0,0)
    v2 = Vector(0,1,0)
    c = cross_product(v1, v2)
    assert c.approximately_equal(Vector(0,0,1))

def test_dot_product():
    v1 = Vector(1,0,0)
    v2 = Vector(1,0,0)
    assert dot_product(v1, v2) == 1.0

def test_area_of_triangle():
    p1 = Coordinate(0,0,0)
    p2 = Coordinate(3,0,0)
    p3 = Coordinate(0,4,0)
    area = area_of_triangle(p1, p2, p3)
    assert area.approximately_equal(area.__class__(6.0))