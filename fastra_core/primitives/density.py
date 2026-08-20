from dataclasses import dataclass

@dataclass(frozen=True)
class Density:
    value: float
    _unit: str = 'kg/m³'

    def __post_init__(self):
        if self.value <= 0:
            raise ValueError(f"Density harus > 0")
    @classmethod
    def from_g_per_cubic_cm(cls, val: float) -> 'Density':
        if val <= 0: raise ValueError
        return cls(value=val * 1000.0)
    def __eq__(self, other): return isinstance(other, Density) and self.value == other.value
