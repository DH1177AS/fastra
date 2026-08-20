from dataclasses import dataclass

@dataclass(frozen=True)
class Mass:
    value: float
    _unit: str = 'kg'

    def __post_init__(self):
        if self.value < 0:
            raise ValueError(f"Mass tidak boleh negatif: {self.value}")

    @classmethod
    def from_grams(cls, g: float) -> 'Mass':
        if g < 0: raise ValueError
        return cls(value=g * 0.001)
    @classmethod
    def from_metric_tons(cls, t: float) -> 'Mass':
        if t < 0: raise ValueError
        return cls(value=t * 1000.0)
    def to_grams(self): return self.value * 1000.0
    def to_metric_tons(self): return self.value * 0.001

    def __add__(self, other: 'Mass') -> 'Mass':
        if not isinstance(other, Mass): raise TypeError
        return Mass(self.value + other.value)

    def approximately_equal(self, other: 'Mass', epsilon: float = 1e-6) -> bool:
        if not isinstance(other, Mass): return False
        return abs(self.value - other.value) <= epsilon
    def __eq__(self, other): return isinstance(other, Mass) and self.value == other.value
    def __str__(self): return f"{self.value} kg"
