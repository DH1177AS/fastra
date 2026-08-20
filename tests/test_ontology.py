"""
ACTS-100 tests
"""
import pytest
from fastra_core.ontology.entity_type import EntityType
from fastra_core.ontology.lifecycle import LifecycleStatus, is_valid_transition
from fastra_core.ontology.universal_object import UniversalObject
from fastra_core.ontology.relationship import Relationship, RelationshipType
from fastra_core.ontology.four_layer import FourLayerReality
from fastra_core.ontology.validators import (
    validate_entity_basic, validate_physical_entity,
    validate_spatial_hierarchy, validate_relationship
)

class TestEntityType:
    def test_12_types_exist(self):
        assert len(EntityType) == 12

    def test_entity_has_type(self):
        obj = UniversalObject(name="Test", entity_type=EntityType.PHYSICAL)
        assert obj.entity_type == EntityType.PHYSICAL

class TestUniversalObject:
    def test_has_unique_uuid(self):
        obj1 = UniversalObject(name="A")
        obj2 = UniversalObject(name="B")
        assert obj1.uuid != obj2.uuid

    def test_version_starts_at_1(self):
        obj = UniversalObject(name="A")
        assert obj.version == 1

    def test_invalid_uuid_raises(self):
        with pytest.raises(ValueError):
            UniversalObject(uuid="not-valid", name="Test")

class TestLifecycle:
    def test_valid_transition(self):
        assert is_valid_transition(LifecycleStatus.DRAFT, LifecycleStatus.ACTIVE)

    def test_invalid_transition(self):
        assert not is_valid_transition(LifecycleStatus.OBSOLETE, LifecycleStatus.ACTIVE)

class TestFourLayerReality:
    def test_all_layers_exist(self):
        fl = FourLayerReality()
        assert fl.physical is not None
        assert fl.geometric is not None
        assert fl.semantic is not None
        assert fl.economic is not None

class TestRelationship:
    def test_create_relationship(self):
        rel = Relationship("uuid1", "uuid2", RelationshipType.CONTAINS)
        assert rel.source_uuid == "uuid1"

class TestValidators:
    def test_physical_without_geometry(self):
        obj = UniversalObject(name="Dinding", entity_type=EntityType.PHYSICAL)
        errors = validate_physical_entity(obj, has_geometry=False)
        assert len(errors) == 1

    def test_spatial_cycle(self):
        errors = validate_spatial_hierarchy({"A": ["B"], "B": ["A"]})
        assert len(errors) > 0