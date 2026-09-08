# fastra_core/ontology/validators.py

from __future__ import annotations

import functools
import logging
from typing import Any, Callable, Dict, List, Set

from fastra_core.ontology.entity_type import EntityType
from fastra_core.ontology.relationship import Relationship
from fastra_core.ontology.universal_object import UniversalObject

logger = logging.getLogger("fastra.ontology.validators")


def validate_entity_basic(entity: Any) -> None:
    """
    Melakukan verifikasi struktural asas entitas ontologi grafik pengetahuan.
    Menerapkan kebijakan strict fail-fast: memutus eksekusi instan jika mendeteksi anomali.
    """
    if entity is None:
        logger.error("VALIDATION_REJECTED_NULL_ENTITY")
        raise TypeError("VALIDATION_FAILED_ENTITY_OBJECT_CANNOT_BE_NULL")

    if not isinstance(entity, UniversalObject):
        logger.error("VALIDATION_REJECTED_INVALID_TYPE: %r", entity)
        raise TypeError("VALIDATION_FAILED_OBJECT_MUST_BE_AN_INSTANCE_OF_UNIVERSAL_OBJECT")

    if not entity.uuid or not entity.uuid.strip():
        logger.error("VALIDATION_REJECTED_EMPTY_UUID")
        raise ValueError("INTEGRITY_VIOLATION_ENTITY_UUID_CANNOT_BE_EMPTY")

    if not entity.name or not entity.name.strip():
        logger.error("VALIDATION_REJECTED_EMPTY_NAME")
        raise ValueError("INTEGRITY_VIOLATION_ENTITY_NAME_CANNOT_BE_EMPTY")

    if entity.version < 1:
        logger.error("VALIDATION_REJECTED_INVALID_VERSION: %s", entity.version)
        raise ValueError("INTEGRITY_VIOLATION_ENTITY_VERSION_MUST_BE_AT_LEAST_ONE")


def validate_physical_constraints(entity: Any, has_geometry: bool) -> None:
    """
    Memverifikasi pemenuhan hukum dimensional realitas fisik berdasarkan standar teknik sipil.
    Setiap entitas bertipe PHYSICAL diwajibkan memiliki representasi geometri terikat.
    """
    validate_entity_basic(entity)

    if not isinstance(has_geometry, bool):
        logger.error("PHYSICAL_CONSTRAINT_REJECTED_NON_BOOL_GEOMETRY_FLAG: %r", has_geometry)
        raise TypeError("GEOMETRY_FLAG_MUST_BE_A_BOOLEAN")

    if entity.entity_type == EntityType.PHYSICAL and not has_geometry:
        logger.error(
            "PHYSICAL_CONSTRAINT_VIOLATION: entity=%s uuid=%s",
            entity.name,
            entity.uuid,
        )
        raise ValueError(
            f"SPATIAL_CONSTRAINT_VIOLATION: Physical entity '{entity.name}' "
            f"with UUID {entity.uuid} must possess a valid geometric configuration."
        )


def validate_physical_entity(entity: Any, has_geometry: bool) -> List[str]:
    """
    Membungkus validate_physical_constraints menjadi fungsi yang mengembalikan daftar pesan kesalahan,
    sesuai kontrak test ACTS-100 yang mengharapkan iterable.
    """
    errors: List[str] = []
    try:
        validate_physical_constraints(entity, has_geometry)
    except (TypeError, ValueError) as exc:
        errors.append(str(exc))
    return errors


def _validate_spatial_hierarchy_impl(contains_map: Any) -> None:
    """
    Mendeteksi keberadaan siklus ilegal (Circular Dependency) dalam hirarki spasial CONTAINS.
    Menggunakan Iterative Stack-Based DFS untuk memblokir risiko Stack Overflow akibat serangan payload besar.
    """
    if contains_map is None:
        logger.error("SPATIAL_MAP_REJECTED_NULL")
        raise TypeError("SPATIAL_MAP_CANNOT_BE_NULL")

    if not isinstance(contains_map, dict):
        logger.error("SPATIAL_MAP_REJECTED_NON_DICT: %r", contains_map)
        raise TypeError("SPATIAL_MAP_MUST_BE_A_DICTIONARY")

    visited: Set[str] = set()
    edge_index_tracker: Dict[str, int] = {node: 0 for node in contains_map}

    for root_node in contains_map:
        if not isinstance(root_node, str) or not root_node.strip():
            logger.error("SPATIAL_MAP_INVALID_NODE_KEY: %r", root_node)
            raise ValueError("SPATIAL_MAP_KEYS_MUST_BE_NON_EMPTY_STRINGS")

        if root_node in visited:
            continue

        stack: List[str] = [root_node]
        in_current_path: Set[str] = {root_node}

        while stack:
            current_node = stack[-1]
            children = contains_map.get(current_node, [])
            if not isinstance(children, list):
                logger.error("SPATIAL_MAP_CHILDREN_NOT_LIST at node %s", current_node)
                raise TypeError("SPATIAL_MAP_CHILDREN_MUST_BE_LISTS")
            current_index = edge_index_tracker.get(current_node, 0)

            if current_index < len(children):
                next_child = children[current_index]
                edge_index_tracker[current_node] = current_index + 1

                if not isinstance(next_child, str) or not next_child.strip():
                    logger.error("SPATIAL_MAP_INVALID_CHILD_ID at %s: %r", current_node, next_child)
                    raise ValueError("SPATIAL_MAP_CHILD_IDS_MUST_BE_NON_EMPTY_STRINGS")

                if next_child in in_current_path:
                    logger.error(
                        "SPATIAL_CIRCULAR_DEPENDENCY_DETECTED: %s -> %s",
                        current_node,
                        next_child,
                    )
                    raise ValueError(
                        f"CIRCULAR_DEPENDENCY_DETECTED_IN_SPATIAL_HIERARCHY: "
                        f"Cycle identified involving pathway connection from '{current_node}' back to '{next_child}'."
                    )

                if next_child not in visited:
                    visited.add(next_child)
                    stack.append(next_child)
                    in_current_path.add(next_child)
            else:
                popped_node = stack.pop()
                in_current_path.remove(popped_node)
                visited.add(popped_node)


def validate_spatial_hierarchy(contains_map: Any) -> List[str]:
    """
    Memvalidasi tidak adanya siklus pada peta hirarki spasial.
    Mengembalikan daftar pesan kesalahan jika ditemukan siklus atau input tidak valid.
    """
    errors: List[str] = []
    try:
        _validate_spatial_hierarchy_impl(contains_map)
    except (TypeError, ValueError) as exc:
        errors.append(str(exc))
    return errors

def validate_relationship(
    rel: Any,
    source_type: Any,
    target_type: Any,
) -> None:
    """
    Memverifikasi keabsahan semantik busur relasi grafik berdasarkan matriks taksonomi hulu.
    Mengeksekusi penolakan instan (fail-fast) jika mendeteksi pelanggaran tipe pasangan.
    """
    if rel is None:
        logger.error("RELATIONSHIP_REJECTED_NULL")
        raise TypeError("RELATIONSHIP_OBJECT_CANNOT_BE_NULL")

    if not isinstance(rel, Relationship):
        logger.error("RELATIONSHIP_REJECTED_INVALID_TYPE: %r", rel)
        raise TypeError("RELATIONSHIP_MUST_BE_AN_INSTANCE_OF_RELATIONSHIP")

    if not isinstance(source_type, EntityType) or not isinstance(target_type, EntityType):
        logger.error(
            "RELATIONSHIP_TYPE_METADATA_REJECTED: source=%r target=%r",
            source_type,
            target_type,
        )
        raise TypeError("SOURCE_AND_TARGET_METADATA_TYPES_MUST_BE_PURE_ENTITY_TYPE_ENUMS")

    rel.validate_semantic_constraints(source_type=source_type, target_type=target_type)


def precondition(
    condition_callable: Callable[[], bool],
    message: str = "Precondition constraint violation encountered",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator formal untuk memvalidasi pemenuhan syarat kondisi (Prerequisite) sebelum fungsi dieksekusi.
    """
    if not callable(condition_callable):
        logger.error("PRECONDITION_REJECTED_NON_CALLABLE: %r", condition_callable)
        raise TypeError("CONDITION_CALLABLE_MUST_BE_CALLABLE")

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not condition_callable():
                logger.error("PRECONDITION_FAILURE: %s", message)
                raise ValueError(f"PRECONDITION_CONSTRAINT_FAILURE: {message}")
            return func(*args, **kwargs)

        return wrapper

    return decorator


def postcondition(
    condition_callable: Callable[[Any], bool],
    message: str = "Postcondition constraint violation encountered",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator formal untuk memvalidasi pemenuhan keabsahan keluaran data (Post-requisite) setelah fungsi dieksekusi.
    """
    if not callable(condition_callable):
        logger.error("POSTCONDITION_REJECTED_NON_CALLABLE: %r", condition_callable)
        raise TypeError("CONDITION_CALLABLE_MUST_BE_CALLABLE")

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            if not condition_callable(result):
                logger.error("POSTCONDITION_FAILURE: %s", message)
                raise ValueError(f"POSTCONDITION_CONSTRAINT_FAILURE: {message}")
            return result

        return wrapper

    return decorator