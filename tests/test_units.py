import pytest
from fastra_core.units import (
    validate_compatibility, are_units_compatible, convert,
    UnitMismatchError, MissingUnitError, ConversionError,
    normalize_unit
)
from fastra_core.primitives.length import Length
from fastra_core.primitives.volume import Volume

class TestUnitCompatibility:
    def test_same_quantity_compatible(self):
        assert are_units_compatible('m', 'feet') is True

    def test_different_quantity_incompatible(self):
        assert are_units_compatible('m', 'kg') is False

    def test_validate_compatible_no_raise(self):
        # Tidak raise
        validate_compatibility('m', 'cm', 'addition')

    def test_validate_incompatible_raises(self):
        with pytest.raises(UnitMismatchError):
            validate_compatibility('m', 'kg', 'addition')

class TestUnitConversion:
    def test_length_conversion(self):
        result = convert(5, 'm', 'cm')
        assert result == 500.0

    def test_length_feet_to_meter(self):
        result = convert(1, 'foot', 'm')
        assert result == 0.3048

    def test_area_conversion(self):
        result = convert(1, 'ha', 'm²')
        assert result == 10000.0

    def test_volume_conversion(self):
        result = convert(1000, 'L', 'm³')
        assert result == 1.0

    def test_angle_conversion(self):
        result = convert(180, 'deg', 'rad')
        import math
        assert math.isclose(result, math.pi)

    def test_time_conversion(self):
        result = convert(1, 'h', 'min')
        assert result == 60.0

    def test_temperature_conversion(self):
        result = convert(0, '°C', 'K')
        assert result == 273.15

    def test_incompatible_conversion_raises(self):
        with pytest.raises(ConversionError):
            convert(1, 'm', 'kg')

class TestIntegrationPrimitiveUnits:
    def test_length_construction_with_unit_conversion(self):
        """ACTS-000-003: Konversi satuan saat membuat Length."""
        l = Length.from_feet(3.28084)
        assert l.approximately_equal(Length(1.0), epsilon=1e-4)

    def test_missing_unit_should_be_caught_by_type_system(self):
        """ACTS-000-011: Nilai tanpa satuan ditolak oleh type system."""
        # Primitive types selalu memiliki satuan, jadi ini otomatis.
        # Tes bahwa membuat float biasa tidak bisa digunakan langsung.
        with pytest.raises(TypeError):
            Length(5) + 3.0  # skalar tanpa satuan