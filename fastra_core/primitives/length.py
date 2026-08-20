from dataclasses import dataclass

@dataclass(frozen=True)
class Length:
    value: float
    _unit: str = 'm'

    def __post_init__(self):
        if self.value < 0:
            raise ValueError(f"Length tidak boleh negatif: {self.value}")

    @classmethod
    def from_millimeters(cls, mm: float) -> 'Length':
        if mm < 0: raise ValueError
        return cls(value=mm * 0.001, _unit='mm')
    @classmethod
    def from_centimeters(cls, cm: float) -> 'Length':
        if cm < 0: raise ValueError
        return cls(value=cm * 0.01, _unit='cm')
    @classmethod
    def from_kilometers(cls, km: float) -> 'Length':
        if km < 0: raise ValueError
        return cls(value=km * 1000.0, _unit='km')
    @classmethod
    def from_inches(cls, inches: float) -> 'Length':
        if inches < 0: raise ValueError
        return cls(value=inches * 0.0254, _unit='in')
    @classmethod
    def from_feet(cls, feet: float) -> 'Length':
        if feet < 0: raise ValueError
        return cls(value=feet * 0.3048, _unit='ft')
    @classmethod
    def from_yards(cls, yards: float) -> 'Length':
        if yards < 0: raise ValueError
        return cls(value=yards * 0.9144, _unit='yd')

    def to_millimeters(self): return self.value * 1000.0
    def to_centimeters(self): return self.value * 100.0
    def to_kilometers(self): return self.value * 0.001
    def to_inches(self): return self.value / 0.0254
    def to_feet(self): return self.value / 0.3048
    def to_yards(self): return self.value / 0.9144

    def __add__(self, other: 'Length') -> 'Length':
        if not isinstance(other, Length): raise TypeError
        return Length(self.value + other.value)
    def __sub__(self, other: 'Length') -> 'Length':
        if not isinstance(other, Length): raise TypeError
        result = self.value - other.value
        if result < 0: raise ValueError("Pengurangan menghasilkan Length negatif")
        return Length(result)
    def __mul__(self, scalar: float) -> 'Length':
        if not isinstance(scalar, (int, float)): raise TypeError
        result = self.value * scalar
        if result < 0: raise ValueError
        return Length(result)
    def __truediv__(self, scalar: float) -> 'Length':
        if not isinstance(scalar, (int, float)): raise TypeError
        if scalar == 0: raise ZeroDivisionError
        result = self.value / scalar
        if result < 0: raise ValueError
        return Length(result)

    def approximately_equal(self, other: 'Length', epsilon: float = 1e-6) -> bool:
        if not isinstance(other, Length): return False
        return abs(self.value - other.value) <= epsilon
    def __eq__(self, other): return isinstance(other, Length) and self.value == other.value
    def __lt__(self, other): return isinstance(other, Length) and self.value < other.value
    def __str__(self): return f"{self.value} m"
    def __repr__(self): return f"Length({self.value}, 'm')"
