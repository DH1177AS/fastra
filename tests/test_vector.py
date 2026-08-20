import math
import pytest
from fastra_core.spatial.vector import Vector
from fastra_core.primitives.length import Length

class TestVector:
    def test_magnitude(self):
        v = Vector(3, 4, 0)
        assert v.magnitude().approximately_equal(Length(5))

    def test_normalize(self):
        v = Vector(3, 0, 0)
        n = v.normalize()
        assert n.approximately_equal(Vector(1, 0, 0))

    def test_normalize_zero_raises(self):
        with pytest.raises(ValueError):
            Vector(0, 0, 0).normalize()

    def test_dot(self):
        v1 = Vector(1, 0, 0)
        v2 = Vector(0, 1, 0)
        assert v1.dot(v2) == 0

    def test_cross(self):
        v1 = Vector(1, 0, 0)
        v2 = Vector(0, 1, 0)
        result = v1.cross(v2)
        assert result.approximately_equal(Vector(0, 0, 1))

    def test_addition(self):
        v1 = Vector(1, 2, 3)
        v2 = Vector(4, 5, 6)
        assert (v1 + v2).approximately_equal(Vector(5, 7, 9))