from typing import List, Dict
from fastra_core.ontology.entity_type import EntityType
from fastra_core.ontology.relationship import Relationship
from fastra_core.ontology.universal_object import UniversalObject

def validate_entity_basic(entity: UniversalObject) -> List[str]:
    errors = []
    if not entity.uuid:
        errors.append("UUID tidak boleh kosong")
    if not entity.name:
        errors.append("Nama tidak boleh kosong")
    if entity.version < 1:
        errors.append("Versi harus >= 1")
    return errors

def validate_physical_entity(entity: UniversalObject, has_geometry: bool = False) -> List[str]:
    errors = []
    if entity.entity_type == EntityType.PHYSICAL and not has_geometry:
        errors.append(f"Physical entity '{entity.name}' harus memiliki geometri")
    return errors

def validate_spatial_hierarchy(contains_map: Dict[str, List[str]]) -> List[str]:
    errors = []
    def dfs(node, visited, stack):
        visited.add(node)
        stack.add(node)
        for child in contains_map.get(node, []):
            if child not in visited:
                dfs(child, visited, stack)
            elif child in stack:
                errors.append(f"Siklus terdeteksi pada CONTAINS: {node} -> {child}")
        stack.remove(node)
    visited: set = set()
    for node in contains_map:
        if node not in visited:
            dfs(node, visited, set())
    return errors

def validate_relationship(rel, source_type, target_type):
    errors = []
    expected = VALID_RELATION_PAIRS.get(rel.relationship_type)
    if expected:
        exp_src, exp_tgt = expected
        if exp_src is not None and source_type != exp_src:
            errors.append(f"Relasi {rel.relationship_type.value} memerlukan source {exp_src.value}")
        if exp_tgt is not None and target_type != exp_tgt:
            errors.append(f"Relasi {rel.relationship_type.value} memerlukan target {exp_tgt.value}")
    return errors


def precondition(condition: bool, message: str = "Precondition failed"):
    """Dekorator preconditions: memeriksa kondisi sebelum method/property."""
    if not condition:
        raise ValueError(message)

def postcondition(condition: bool, message: str = "Postcondition failed"):
    """Dekorator postconditions: memeriksa kondisi setelah method/property."""
    if not condition:
        raise ValueError(message)
