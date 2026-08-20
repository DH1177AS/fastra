import pytest
from fastra_core.geometry.polygon import is_closed, area, is_convex, contains_point
from fastra_core.spatial.coordinate import Coordinate

# Rectangle 10x10
rect = [
    Coordinate(0,0,0),
    Coordinate(10,0,0),
    Coordinate(10,5,0),
    Coordinate(0,5,0),
    Coordinate(0,0,0)  # closed
]

def test_is_closed():
    assert is_closed(rect)
    open_poly = [Coordinate(0,0,0), Coordinate(10,0,0), Coordinate(10,5,0)]
    assert not is_closed(open_poly)

def test_area():
    a = area(rect)
    assert a.approximately_equal(a.__class__(50.0))

def test_is_convex():
    assert is_convex(rect)
    # concav shape
    concave = [
        Coordinate(0,0,0),
        Coordinate(10,0,0),
        Coordinate(5,2,0),
        Coordinate(10,5,0),
        Coordinate(0,5,0),
        Coordinate(0,0,0)
    ]
    assert not is_convex(concave)

def test_contains_point():
    inside = Coordinate(5,2,0)
    outside = Coordinate(20,20,0)
    assert contains_point(rect, inside)
    assert not contains_point(rect, outside)