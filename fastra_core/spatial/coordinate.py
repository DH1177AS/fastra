from dataclasses import dataclass
import math
from fastra_core.primitives.length import Length

@dataclass(frozen=True)
class Coordinate:
    x: float
    y: float
    z: float

    def __post_init__(self):
        if any(math.isnan(v) for v in (self.x, self.y, self.z)):
            raise ValueError("Coordinate tidak boleh NaN")

    def distance_to(self, other: 'Coordinate') -> 'Length':
        from fastra_core.primitives.length import Length
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return Length((dx*dx + dy*dy + dz*dz)**0.5)

    def midpoint(self, other: 'Coordinate') -> 'Coordinate':
        return Coordinate((self.x+other.x)/2, (self.y+other.y)/2, (self.z+other.z)/2)

    def approximately_equal(self, other: 'Coordinate', epsilon: float = 1e-6) -> bool:
        return (abs(self.x-other.x)<=epsilon and abs(self.y-other.y)<=epsilon and abs(self.z-other.z)<=epsilon)

    def __sub__(self, other: 'Coordinate'):
        from fastra_core.spatial.vector import Vector
        return Vector(self.x-other.x, self.y-other.y, self.z-other.z)
