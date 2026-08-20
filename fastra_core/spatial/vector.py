from dataclasses import dataclass
import math
from fastra_core.primitives.length import Length

@dataclass(frozen=True)
class Vector:
    dx: float
    dy: float
    dz: float

    def __post_init__(self):
        if any(math.isnan(v) for v in (self.dx, self.dy, self.dz)):
            raise ValueError("Vector tidak boleh NaN")

    def magnitude(self) -> 'Length':
        from fastra_core.primitives.length import Length
        return Length((self.dx*self.dx + self.dy*self.dy + self.dz*self.dz)**0.5)

    def cross(self, other: 'Vector') -> 'Vector':
        return Vector(
            self.dy*other.dz - self.dz*other.dy,
            self.dz*other.dx - self.dx*other.dz,
            self.dx*other.dy - self.dy*other.dx
        )

    def dot(self, other: 'Vector') -> float:
        return self.dx*other.dx + self.dy*other.dy + self.dz*other.dz

    def normalize(self) -> 'Vector':
        m = self.magnitude().value
        if m == 0:
            raise ValueError("Tidak dapat menormalisasi vektor nol")
        return Vector(self.dx/m, self.dy/m, self.dz/m)

    def approximately_equal(self, other: 'Vector', epsilon: float = 1e-6) -> bool:
        return (abs(self.dx-other.dx)<=epsilon and abs(self.dy-other.dy)<=epsilon and abs(self.dz-other.dz)<=epsilon)

    def __add__(self, other: 'Vector') -> 'Vector':
        return Vector(self.dx+other.dx, self.dy+other.dy, self.dz+other.dz)
    def __mul__(self, scalar: float) -> 'Vector':
        return Vector(self.dx*scalar, self.dy*scalar, self.dz*scalar)
