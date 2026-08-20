import pytest
from fastra_core.primitives.mass import Mass

class TestMass:
    def test_construct_valid(self):
        m = Mass(10.0)
        assert m.value == 10.0

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            Mass(-1)

    def test_from_grams(self):
        m = Mass.from_grams(5000)
        assert m.value == 5.0
        assert m.to_grams() == 5000.0

    def test_from_metric_tons(self):
        m = Mass.from_metric_tons(2)
        assert m.value == 2000.0

    def test_addition(self):
        assert (Mass(5) + Mass(3)).value == 8.0