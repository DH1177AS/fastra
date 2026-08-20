from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN

@dataclass(frozen=True)
class Currency:
    value: Decimal
    _unit: str = 'IDR'

    def __post_init__(self):
        rounded = self.value.quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
        object.__setattr__(self, 'value', rounded)

    @classmethod
    def from_float(cls, amount: float) -> 'Currency':
        return cls(value=Decimal(str(amount)))

    def __add__(self, other: 'Currency') -> 'Currency':
        if not isinstance(other, Currency): raise TypeError
        return Currency(self.value + other.value)
    def __mul__(self, scalar: float) -> 'Currency':
        if not isinstance(scalar, (int, float, Decimal)): raise TypeError
        return Currency(self.value * Decimal(str(scalar)))

    def approximately_equal(self, other: 'Currency', epsilon: float = 0.5) -> bool:
        if not isinstance(other, Currency): return False
        return abs(self.value - other.value) <= Decimal(str(epsilon))
    def __eq__(self, other): return isinstance(other, Currency) and self.value == other.value
    def __str__(self): return f"Rp {self.value:,.2f}"
    def __repr__(self): return f"Currency({self.value})"
