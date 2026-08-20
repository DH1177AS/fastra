import pytest
from fastra_core.numerical.geometry import orient2d, point_in_polygon, polygon_area
from fastra_core.numerical.matrix import inverse_matrix
from fastra_core.spatial.coordinate import Coordinate
from fastra_core.spatial.matrix4x4 import Matrix4x4

class TestGeometry:
    def test_orient2d_ccw(self):
        a, b, c = Coordinate(0,0,0), Coordinate(1,0,0), Coordinate(0,1,0)
        assert orient2d(a,b,c) > 0

    def test_point_in_rectangle(self):
        rect = [Coordinate(0,0,0), Coordinate(10,0,0), Coordinate(10,5,0), Coordinate(0,5,0), Coordinate(0,0,0)]
        assert point_in_polygon(rect, Coordinate(5,2,0))
        assert not point_in_polygon(rect, Coordinate(20,20,0))

    def test_polygon_area(self):
        rect = [Coordinate(0,0,0), Coordinate(10,0,0), Coordinate(10,5,0), Coordinate(0,5,0), Coordinate(0,0,0)]
        a = polygon_area(rect)
        assert a.approximately_equal(a.__class__(50.0))

class TestMatrix:
    def test_inverse_translation(self):
        T = Matrix4x4.from_rows([1,0,0,5],[0,1,0,3],[0,0,1,2],[0,0,0,1])
        inv = inverse_matrix(T)
        prod = T * inv
        assert prod.approximately_equal(Matrix4x4.identity())
