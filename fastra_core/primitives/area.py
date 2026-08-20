from dataclasses import dataclass

@dataclass(frozen=True)
class Area:
    value: float
    _unit: str = 'm²'

    def __post_init__(self):
        if self.value < 0:
            raise ValueError(f"Area tidak boleh negatif: {self.value}")

    @classmethod
    def from_square_centimeters(cls, cm2: float) -> 'Area':
        if cm2 < 0: raise ValueError
        return cls(value=cm2 * 1e-4, _unit='cm²')
    @classmethod
    def from_hectares(cls, ha: float) -> 'Area':
        if ha < 0: raise ValueError
        return cls(value=ha * 10000.0, _unit='ha')

    def to_square_centimeters(self): return self.value * 1e4
    def to_hectares(self): return self.value * 1e-4

    def __add__(self, other: 'Area') -> 'Area':
        if not isinstance(other, Area): raise TypeError
        return Area(self.value + other.value)
    def __mul__(self, scalar: float) -> 'Area':
        if not isinstance(scalar, (int, float)): raise TypeError
        result = self.value * scalar
        if result < 0: raise ValueError
        return Area(result)

    def approximately_equal(self, other: 'Area', epsilon: float = 1e-6) -> bool:
        if not isinstance(other, Area): return False
        return abs(self.value - other.value) <= epsilon
    def __eq__(self, other): return isinstance(other, Area) and self.value == other.value
    def __str__(self): return f"{self.value} m²"
    def __repr__(self): return f"Area({self.value})"
