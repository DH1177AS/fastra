from dataclasses import dataclass

@dataclass(frozen=True)
class Volume:
    value: float
    _unit: str = 'm³'

    def __post_init__(self):
        if self.value < 0:
            raise ValueError(f"Volume tidak boleh negatif: {self.value}")

    @classmethod
    def from_liters(cls, l: float) -> 'Volume':
        if l < 0: raise ValueError
        return cls(value=l * 0.001, _unit='L')
    def to_liters(self): return self.value * 1000.0

    def __add__(self, other: 'Volume') -> 'Volume':
        if not isinstance(other, Volume): raise TypeError
        return Volume(self.value + other.value)
    def __mul__(self, scalar: float) -> 'Volume':
        if not isinstance(scalar, (int, float)): raise TypeError
        result = self.value * scalar
        if result < 0: raise ValueError
        return Volume(result)

    def approximately_equal(self, other: 'Volume', epsilon: float = 1e-9) -> bool:
        if not isinstance(other, Volume): return False
        return abs(self.value - other.value) <= epsilon
    def __eq__(self, other): return isinstance(other, Volume) and self.value == other.value
    def __str__(self): return f"{self.value} m³"
    def __repr__(self): return f"Volume({self.value})"
