import math
import pytest
from fastra_core.primitives.angle import Angle

class TestAngle:
    def test_from_degrees(self):
        a = Angle.from_degrees(180)
        assert math.isclose(a.value, math.pi)

    def test_normalized(self):
        a = Angle.from_degrees(370)
        n = a.normalized()
        assert math.isclose(n.to_degrees(), 10.0)

    def test_addition(self):
        a1 = Angle.from_degrees(30)
        a2 = Angle.from_degrees(60)
        result = a1 + a2
        assert math.isclose(result.to_degrees(), 90.0)

    def test_approximately_equal(self):
        a1 = Angle(1.0)
        a2 = Angle(1.0000000001)
        assert a1.approximately_equal(a2)