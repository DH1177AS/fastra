from dataclasses import dataclass

@dataclass(frozen=True)
class Temperature:
    value: float
    _unit: str = 'K'

    @classmethod
    def from_celsius(cls, c: float) -> 'Temperature':
        return cls(value=c + 273.15)
    @classmethod
    def from_fahrenheit(cls, f: float) -> 'Temperature':
        return cls(value=(f - 32) * 5/9 + 273.15)
    def to_celsius(self): return self.value - 273.15
    def to_fahrenheit(self): return (self.value - 273.15) * 9/5 + 32

    def __eq__(self, other): return isinstance(other, Temperature) and self.value == other.value
    def __lt__(self, other): return isinstance(other, Temperature) and self.value < other.value
    def __gt__(self, other): return isinstance(other, Temperature) and self.value > other.value
    def __str__(self): return f"{self.to_celsius():.1f} °C"
