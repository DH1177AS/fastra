from .exceptions import UnitMismatchError, MissingUnitError

COMPATIBLE_GROUPS = {
    'length': {'m','mm','cm','km','inch','foot','feet','yard'},
    'area': {'m²','mm²','cm²','km²','ha','hektar'},
    'volume': {'m³','cm³','l','liter'},
    'mass': {'kg','g','ton'},
    'angle': {'rad','deg','degree'},
    'time': {'s','min','h','hour','day','week','month'},
    'currency': {'idr','usd','eur'},
    'temperature': {'k','°c','°f','c','f'},
    'density': {'kg/m³','g/cm³'}
}
ALIASES = {'feet':'foot','ft':'foot','hektar':'ha','liter':'l','degree':'deg','hour':'h','c':'°c','f':'°f'}

def normalize_unit(u):
    if not u: return u
    u = u.strip()
    if u in ALIASES: return ALIASES[u]
    return u.lower()

def get_quantity_type(unit):
    norm = normalize_unit(unit)
    for qtype, units in COMPATIBLE_GROUPS.items():
        if norm in units:
            return qtype
    return "unknown"

def are_units_compatible(u1, u2):
    if not u1 or not u2:
        return False
    t1 = get_quantity_type(u1)
    t2 = get_quantity_type(u2)
    return t1 == t2 and t1 != "unknown"

def validate_compatibility(u1, u2, operation=""):
    if not are_units_compatible(u1, u2):
        raise UnitMismatchError(u1, u2, operation)
    return True

def validate_unit_presence(value, unit):
    if unit is None or unit == "":
        raise MissingUnitError(value)


def validate_dimension(unit: str, expected_quantity_type: str) -> None:
    """Validasi bahwa unit memiliki dimensi kuantitas yang diharapkan.
    Contoh: validate_dimension("m²", "area") -> True
    """
    if not unit:
        raise MissingUnitError(unit)
    qtype = get_quantity_type(unit)
    if qtype != expected_quantity_type:
        raise UnitMismatchError(unit, expected_quantity_type, f"expected {expected_quantity_type}")


def validate_unit_not_unknown(unit: str) -> None:
    """Validasi bahwa unit dikenal oleh sistem (tidak unknown)."""
    if not unit:
        raise MissingUnitError(unit)
    qtype = get_quantity_type(unit)
    if qtype == "unknown":
        raise UnitMismatchError(unit, "known unit", "unit tidak dikenal")
