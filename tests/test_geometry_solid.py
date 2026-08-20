from fastra_core.geometry.solid import BoundingBox, intersect_box, union_box
from fastra_core.spatial.coordinate import Coordinate

def test_bounding_box_volume():
    box = BoundingBox(Coordinate(0,0,0), Coordinate(2,3,4))
    v = box.volume()
    assert v.value == 24.0

def test_bounding_box_surface_area():
    box = BoundingBox(Coordinate(0,0,0), Coordinate(2,3,4))
    sa = box.surface_area()
    assert sa.value == 2*(2*3 + 2*4 + 3*4)  # 52

def test_intersect_box():
    b1 = BoundingBox(Coordinate(0,0,0), Coordinate(2,2,2))
    b2 = BoundingBox(Coordinate(1,1,1), Coordinate(3,3,3))
    inter = intersect_box(b1, b2)
    assert inter.volume().value == 1.0  # 1x1x1

def test_union_box():
    b1 = BoundingBox(Coordinate(0,0,0), Coordinate(1,1,1))
    b2 = BoundingBox(Coordinate(2,2,2), Coordinate(3,3,3))
    u = union_box(b1, b2)
    assert u.volume().value == 27.0  # 3x3x3