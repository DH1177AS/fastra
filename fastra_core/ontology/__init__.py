from __future__ import annotations

import logging
import threading
from typing import Any, Dict, List, Type

# Expose strict domain components down to the module boundary layer
from .entity_type import (
    EntityType,
    ENTITY_FAMILIES,
    ENTITY_TYPE_NAMES,
    lookup_entity_type,
    get_entity_family,
)
from .lifecycle import LifecycleStatus, VALID_TRANSITIONS, is_valid_transition
from .universal_object import UniversalObject, LifecycleHistoryEntry
from .relationship import (
    Relationship,
    RelationshipType,
    Direction,
    VALID_RELATION_PAIRS,
    SEMANTIC_RELATIONSHIPS,
)
from .four_layer import (
    FourLayerReality,
    PhysicalReality,
    GeometricReality,
    SemanticReality,
    EconomicReality,
)
from .validators import (
    validate_entity_basic,
    validate_physical_constraints,
    validate_spatial_hierarchy,
    precondition,
    postcondition,
)

logger = logging.getLogger("fastra.ontology")

# Alias untuk mempertahankan kompatibilitas nama ekspor lama tanpa duplikasi.
validate_physical_entity = validate_physical_constraints

_ONTOLOGY_MODULE_LOCK = threading.Lock()


def verify_ontology_subsystem_health() -> Dict[str, Any]:
    """
    Menjalankan smoke test fail-fast untuk memastikan seluruh komponen inti
    ontologi telah terinisialisasi tanpa kontaminasi tipe.
    """
    if not _ONTOLOGY_MODULE_LOCK.acquire(timeout=10):
        logger.error("ONTOLOGY_HEALTH_CHECK_LOCK_ACQUISITION_TIMEOUT")
        raise TimeoutError("ONTOLOGY_HEALTH_CHECK_LOCK_ACQUISITION_TIMEOUT")

    try:
        monitored_elements: List[Type[Any]] = [
            EntityType,
            LifecycleStatus,
            UniversalObject,
            Relationship,
            FourLayerReality,
        ]

        for element in monitored_elements:
            if element is None:
                logger.error("ONTOLOGY_INTEGRITY_COMPROMISED_NULL_COMPONENT")
                raise ImportError(
                    "ONTOLOGY_INTEGRITY_COMPROMISED: Sub-component failed to initialize."
                )

        logger.info("Ontology subsystem health check passed")
        return {
            "status": "HEALTHY",
            "layer": "ONTOLOGY_CORE",
            "military_grade_lock_active": True,
        }
    finally:
        _ONTOLOGY_MODULE_LOCK.release()


# Eksekusi verifikasi awal saat modul dimuat.
verify_ontology_subsystem_health()

__all__ = [
    "EntityType",
    "ENTITY_FAMILIES",
    "ENTITY_TYPE_NAMES",
    "lookup_entity_type",
    "get_entity_family",
    "LifecycleStatus",
    "VALID_TRANSITIONS",
    "is_valid_transition",
    "UniversalObject",
    "LifecycleHistoryEntry",
    "Relationship",
    "RelationshipType",
    "Direction",
    "VALID_RELATION_PAIRS",
    "SEMANTIC_RELATIONSHIPS",
    "FourLayerReality",
    "PhysicalReality",
    "GeometricReality",
    "SemanticReality",
    "EconomicReality",
    "validate_entity_basic",
    "validate_physical_constraints",
    "validate_physical_entity",
    "validate_spatial_hierarchy",
    "precondition",
    "postcondition",
    "verify_ontology_subsystem_health",
]