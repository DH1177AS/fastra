import pytest
from fastra_core.primitives.time import Time

class TestTime:
    def test_construct_valid(self):
        t = Time(60)
        assert t.value == 60

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            Time(-1)

    def test_from_days(self):
        t = Time.from_days(1)
        assert t.value == 86400.0

    def test_addition(self):
        t = Time.from_hours(1) + Time.from_minutes(30)
        assert t.to_hours() == 1.5

    def test_division(self):
        t = Time(3600) / 2
        assert t.value == 1800.0