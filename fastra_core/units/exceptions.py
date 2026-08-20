class UnitError(Exception): pass
class UnitMismatchError(UnitError):
    def __init__(self, unit1, unit2, operation=""):
        msg = f"Satuan tidak kompatibel: '{unit1}' dan '{unit2}'"
        if operation: msg += f" dalam operasi '{operation}'"
        super().__init__(msg)
class MissingUnitError(UnitError): pass
class ConversionError(UnitError): pass
