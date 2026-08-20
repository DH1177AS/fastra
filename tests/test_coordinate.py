import math
import pytest
from fastra_core.spatial.coordinate import Coordinate
from fastra_core.primitives.length import Length

class TestCoordinate:
    def test_construct(self):
        c = Coordinate(1.0, 2.0, 3.0)
        assert c.x == 1.0

    def test_nan_raises(self):
        with pytest.raises(ValueError):
            Coordinate(float('nan'), 0, 0)

    def test_distance_to(self):
        c1 = Coordinate(0, 0, 0)
        c2 = Coordinate(3, 4, 0)
        d = c1.distance_to(c2)
        assert d.approximately_equal(Length(5.0))

    def test_midpoint(self):
        c1 = Coordinate(0, 0, 0)
        c2 = Coordinate(10, 10, 10)
        mid = c1.midpoint(c2)
        assert mid.approximately_equal(Coordinate(5, 5, 5))

    def test_approximate_equal(self):
        c1 = Coordinate(1.0000001, 2.0, 3.0)
        c2 = Coordinate(1.0, 2.0, 3.0)
        assert c1.approximately_equal(c2)