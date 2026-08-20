import pytest
from fastra_core.primitives.volume import Volume

class TestVolume:
    def test_construct_valid(self):
        v = Volume(5.0)
        assert v.value == 5.0

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            Volume(-1)

    def test_from_liters(self):
        v = Volume.from_liters(1000)
        assert v.value == 1.0
        assert v.to_liters() == 1000.0

    def test_addition(self):
        assert (Volume(2) + Volume(3)).value == 5.0