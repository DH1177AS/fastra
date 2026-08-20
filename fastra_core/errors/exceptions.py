class CESError(Exception):
    code: str = "CES-000"
    message: str = ""

    def __init__(self, message="", code=None):
        super().__init__(message)
        self.message = message
        if code: self.code = code

class GeometryError(CESError):
    code = "GEO-001"

class TopologyError(CESError):
    code = "TOP-001"

class UnitError(CESError):
    code = "UNIT-001"

class CostError(CESError):
    code = "COST-001"

class ValidationError(CESError):
    code = "VAL-001"

class CompilerError(CESError):
    code = "COMP-001"

class SerializationError(CESError):
    code = "SER-001"

class VersionError(CESError):
    code = "VER-001"
