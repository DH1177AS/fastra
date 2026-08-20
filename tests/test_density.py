import pytest
from fastra_core.primitives.density import Density

class TestDensity:
    def test_construct_valid(self):
        d = Density(2400)
        assert d.value == 2400

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            Density(0)

    def test_from_g_per_cm3(self):
        d = Density.from_g_per_cubic_cm(2.4)
        assert d.value == 2400.0