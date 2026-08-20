import math
from fastra_core.spatial.transform import Transform
from fastra_core.spatial.vector import Vector
from fastra_core.spatial.quaternion import Quaternion
from fastra_core.spatial.coordinate import Coordinate

class TestTransform:
    def test_identity(self):
        t = Transform.identity()
        p = Coordinate(1,2,3)
        result = t.apply_to_point(p)
        assert result.approximately_equal(p)

    def test_translation(self):
        t = Transform.from_translation(5,0,0)
        p = Coordinate(1,1,1)
        result = t.apply_to_point(p)
        assert result.approximately_equal(Coordinate(6,1,1))

    def test_inverse_roundtrip(self):
        """ACTS-000-008: inverse mengembalikan ke posisi semula."""
        t = Transform(
            translation=Vector(10,20,30),
            rotation=Quaternion.from_axis_angle(0,0,1, math.pi/4),
            scale=Vector(2,2,2)
        )
        p = Coordinate(1,2,3)
        p_transformed = t.apply_to_point(p)
        p_back = t.inverse().apply_to_point(p_transformed)
        assert p_back.approximately_equal(p)

    def test_scale_zero_raises(self):
        import pytest
        with pytest.raises(ValueError):
            Transform(Vector(0,0,0), Quaternion.identity(), Vector(0,1,1))