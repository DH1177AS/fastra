"""
ACES-000 §6.13 (amandemen): Quaternion
Representasi rotasi 3D.
"""

import math
from dataclasses import dataclass

@dataclass(frozen=True)
class Quaternion:
    w: float
    x: float
    y: float
    z: float

    def __post_init__(self):
        if any(math.isnan(v) for v in (self.w, self.x, self.y, self.z)):
            raise ValueError("Quaternion tidak boleh NaN")

    @classmethod
    def identity(cls) -> 'Quaternion':
        return cls(1, 0, 0, 0)

    @classmethod
    def from_axis_angle(cls, axis_x, axis_y, axis_z, angle_rad):
        """Buat quaternion dari rotasi sumbu-sudut."""
        half = angle_rad / 2.0
        s = math.sin(half)
        # Normalisasi sumbu
        axis_len = math.sqrt(axis_x**2 + axis_y**2 + axis_z**2)
        if axis_len == 0:
            return cls.identity()
        nx, ny, nz = axis_x/axis_len, axis_y/axis_len, axis_z/axis_len
        return cls(w=math.cos(half), x=nx*s, y=ny*s, z=nz*s)

    def conjugate(self) -> 'Quaternion':
        return Quaternion(self.w, -self.x, -self.y, -self.z)

    def norm_squared(self) -> float:
        return self.w**2 + self.x**2 + self.y**2 + self.z**2

    def normalize(self) -> 'Quaternion':
        n = math.sqrt(self.norm_squared())
        if n == 0:
            return Quaternion.identity()
        return Quaternion(self.w/n, self.x/n, self.y/n, self.z/n)

    def __mul__(self, other):
        """Perkalian quaternion (komposisi rotasi)."""
        if not isinstance(other, Quaternion):
            raise TypeError
        w1, x1, y1, z1 = self.w, self.x, self.y, self.z
        w2, x2, y2, z2 = other.w, other.x, other.y, other.z
        return Quaternion(
            w = w1*w2 - x1*x2 - y1*y2 - z1*z2,
            x = w1*x2 + x1*w2 + y1*z2 - z1*y2,
            y = w1*y2 - x1*z2 + y1*w2 + z1*x2,
            z = w1*z2 + x1*y2 - y1*x2 + z1*w2
        )

    def approximately_equal(self, other: 'Quaternion', epsilon: float = 1e-6) -> bool:
        if not isinstance(other, Quaternion):
            return False
        return (abs(self.w-other.w) <= epsilon and abs(self.x-other.x) <= epsilon and
                abs(self.y-other.y) <= epsilon and abs(self.z-other.z) <= epsilon)

    def __eq__(self, other):
        if not isinstance(other, Quaternion):
            return False
        return (self.w, self.x, self.y, self.z) == (other.w, other.x, other.y, other.z)

    def __repr__(self):
        return f"Quaternion({self.w}, {self.x}, {self.y}, {self.z})"