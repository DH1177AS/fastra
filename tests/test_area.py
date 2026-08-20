import pytest
from fastra_core.primitives.area import Area

class TestArea:
    def test_construct_valid(self):
        a = Area(10.0)
        assert a.value == 10.0

    def test_construct_negative_raises(self):
        with pytest.raises(ValueError):
            Area(-5.0)

    def test_conversion(self):
        a = Area.from_square_centimeters(10000)  # 1 m²
        assert a.value == 1.0
        assert a.to_square_centimeters() == 10000.0

    def test_addition(self):
        assert (Area(5) + Area(3)).value == 8.0

    def test_multiplication(self):
        assert (Area(5) * 2).value == 10.0

    def test_approximate_equal(self):
        assert Area(1.0000001).approximately_equal(Area(1.0))