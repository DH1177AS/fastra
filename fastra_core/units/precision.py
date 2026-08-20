from enum import Enum
from decimal import Decimal, ROUND_HALF_EVEN, ROUND_UP, ROUND_DOWN, ROUND_FLOOR

class RoundingPolicy(Enum):
    BANKER = "banker"
    UP = "up"
    DOWN = "down"
    TRUNCATE = "truncate"

    def get_decimal_mode(self):
        return {
            RoundingPolicy.BANKER: ROUND_HALF_EVEN,
            RoundingPolicy.UP: ROUND_UP,
            RoundingPolicy.DOWN: ROUND_DOWN,
            RoundingPolicy.TRUNCATE: ROUND_FLOOR,
        }[self]

class PrecisionProfile:
    def __init__(self, significant_digits=6, decimal_places=2, policy=RoundingPolicy.BANKER):
        self.significant_digits = significant_digits
        self.decimal_places = decimal_places
        self.policy = policy

    def round(self, value: Decimal) -> Decimal:
        mode = self.policy.get_decimal_mode()
        return value.quantize(Decimal(10) ** -self.decimal_places, rounding=mode)
