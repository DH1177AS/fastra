import pytest
import json
from fastra_core.errors.exceptions import GeometryError, CompilerError
from fastra_core.serialization.canonical_json import to_json, from_json
from fastra_core.serialization.hash import canonical_hash
from fastra_core.versioning.schema_version import SchemaVersion, VersionCompatibility

class TestErrorModel:
    def test_geometry_error(self):
        with pytest.raises(GeometryError):
            raise GeometryError("Polygon tidak tertutup")

class TestSerialization:
    def test_roundtrip(self):
        data = {"key": "value", "number": 42}
        json_str = to_json(data)
        assert from_json(json_str) == data

    def test_hash_consistency(self):
        data = {"a": 1, "b": 2}
        h1 = canonical_hash(data)
        h2 = canonical_hash({"b":2, "a":1})
        assert h1 == h2

class TestVersioning:
    def test_compatible(self):
        v1 = SchemaVersion(1, 0, 0)
        v2 = SchemaVersion(1, 0, 5)
        assert v1.is_compatible_with(v2) == VersionCompatibility.COMPATIBLE

    def test_incompatible(self):
        v1 = SchemaVersion(1, 0, 0)
        v2 = SchemaVersion(2, 0, 0)
        assert v1.is_compatible_with(v2) == VersionCompatibility.INCOMPATIBLE
