import pytest
from decimal import Decimal
from fastra_core.primitives.currency import Currency

class TestCurrency:
    def test_construct_rounds_to_2_decimal(self):
        c = Currency(Decimal('100.555'))
        assert c.value == Decimal('100.56')  # banker's rounding: 5 -> even (6)

    def test_construct_rounds_half_even(self):
        c = Currency(Decimal('100.545'))
        assert c.value == Decimal('100.54')  # 4 genap, turun

    def test_addition(self):
        c1 = Currency(Decimal('100.00'))
        c2 = Currency(Decimal('50.50'))
        result = c1 + c2
        assert result.value == Decimal('150.50')

    def test_multiplication(self):
        c = Currency(Decimal('100.00'))
        result = c * 2.5
        assert result.value == Decimal('250.00')

    def test_approximate_equal(self):
        c1 = Currency(Decimal('100.00'))
        c2 = Currency(Decimal('100.49'))
        assert c1.approximately_equal(c2, epsilon=0.5)
        c3 = Currency(Decimal('100.51'))
        assert not c1.approximately_equal(c3, epsilon=0.5)

    def test_negative_currency(self):
        c = Currency(Decimal('-50.00'))
        assert c.value == Decimal('-50.00')