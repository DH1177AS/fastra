from dataclasses import dataclass

@dataclass(frozen=True)
class Time:
    value: float
    _unit: str = 's'

    def __post_init__(self):
        if self.value < 0:
            raise ValueError(f"Time tidak boleh negatif: {self.value}")

    @classmethod
    def from_minutes(cls, m: float) -> 'Time':
        if m < 0: raise ValueError
        return cls(value=m * 60.0)
    @classmethod
    def from_hours(cls, h: float) -> 'Time':
        if h < 0: raise ValueError
        return cls(value=h * 3600.0)
    @classmethod
    def from_days(cls, d: float) -> 'Time':
        if d < 0: raise ValueError
        return cls(value=d * 86400.0)

    def to_minutes(self): return self.value / 60.0
    def to_hours(self): return self.value / 3600.0
    def to_days(self): return self.value / 86400.0

    def __add__(self, other: 'Time') -> 'Time':
        if not isinstance(other, Time): raise TypeError
        return Time(self.value + other.value)
    def __truediv__(self, scalar: float) -> 'Time':
        if not isinstance(scalar, (int, float)): raise TypeError
        if scalar == 0: raise ZeroDivisionError
        result = self.value / scalar
        if result < 0: raise ValueError
        return Time(result)

    def approximately_equal(self, other: 'Time', epsilon: float = 1e-6) -> bool:
        if not isinstance(other, Time): return False
        return abs(self.value - other.value) <= epsilon
    def __eq__(self, other): return isinstance(other, Time) and self.value == other.value
    def __str__(self): return f"{self.to_hours():.2f} jam"
