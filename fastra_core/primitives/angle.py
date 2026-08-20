import math
from dataclasses import dataclass

@dataclass(frozen=True)
class Angle:
    value: float
    _unit: str = 'rad'

    @classmethod
    def from_degrees(cls, deg: float) -> 'Angle':
        return cls(value=math.radians(deg))

    def to_degrees(self): return math.degrees(self.value)
    def normalized(self) -> 'Angle':
        return Angle(value=self.value % (2 * math.pi))

    def __add__(self, other: 'Angle') -> 'Angle':
        if not isinstance(other, Angle): raise TypeError
        return Angle(self.value + other.value)

    def approximately_equal(self, other: 'Angle', epsilon: float = 1e-9) -> bool:
        if not isinstance(other, Angle): return False
        return abs(self.value - other.value) <= epsilon
    def __eq__(self, other): return isinstance(other, Angle) and self.value == other.value
    def __str__(self): return f"{self.to_degrees():.2f}°"
