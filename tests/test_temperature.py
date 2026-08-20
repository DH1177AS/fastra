from fastra_core.primitives.temperature import Temperature

class TestTemperature:
    def test_from_celsius(self):
        t = Temperature.from_celsius(0)
        assert t.value == 273.15

    def test_conversion(self):
        t = Temperature.from_celsius(100)
        assert t.to_fahrenheit() == 212.0

    def test_comparison(self):
        assert Temperature.from_celsius(30) > Temperature.from_celsius(20)