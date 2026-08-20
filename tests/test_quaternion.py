import math
from fastra_core.spatial.quaternion import Quaternion

class TestQuaternion:
    def test_identity(self):
        q = Quaternion.identity()
        assert q.w == 1 and q.x == 0

    def test_axis_angle_z_90(self):
        q = Quaternion.from_axis_angle(0,0,1, math.pi/2)
        # Rotasi 90 derajat sekitar Z
        assert abs(q.w - math.cos(math.pi/4)) < 1e-6
        assert abs(q.z - math.sin(math.pi/4)) < 1e-6

    def test_conjugate(self):
        q = Quaternion(0.707, 0.707, 0, 0)
        c = q.conjugate()
        assert c.x == -q.x

    def test_normalize(self):
        q = Quaternion(2, 0, 0, 0).normalize()
        assert q.w == 1.0