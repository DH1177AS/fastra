# fastra_core\ontology\entity_type.py

from __future__ import annotations

import logging
from enum import Enum
from types import MappingProxyType
from typing import Any, Dict, List, Mapping, Optional

logger = logging.getLogger("fastra.ontology.entity_type")


class EntityType(str, Enum):
    """
    Strict Domain Enum untuk mendefinisikan Tipe Entitas Ontologi Konstruksi & Proyek.
    Mewarisi `str` untuk menjamin interaktivitas serialisasi murni tanpa coercion hacks,
    dan dikunci dengan pembatasan mutasi yang ketat.
    """
    PHYSICAL = "Physical"
    SPATIAL = "Spatial"
    TEMPORAL = "Temporal"
    ECONOMIC = "Economic"
    RESOURCE = "Resource"
    HUMAN = "Human"
    ORGANIZATION = "Organization"
    PROCESS = "Process"
    RULE = "Rule"
    EVENT = "Event"
    DOCUMENT = "Document"
    RELATIONSHIP = "Relationship"


_ENTITY_FAMILIES_INTERNAL: Dict[EntityType, List[str]] = {
    EntityType.PHYSICAL: ["Structural Element", "Architectural Element", "MEP Element"],
    EntityType.SPATIAL: ["Macro Space", "Meso Space", "Micro Space"],
    EntityType.RESOURCE: ["Material", "Equipment", "Consumable"],
    EntityType.HUMAN: ["Labor", "Professional"],
    EntityType.PROCESS: ["Construction Process", "Inspection Process", "Procurement Process"],
}

_ENTITY_TYPE_NAMES_INTERNAL: Dict[str, EntityType] = {e.value: e for e in EntityType}

ENTITY_FAMILIES: Mapping[EntityType, List[str]] = MappingProxyType(_ENTITY_FAMILIES_INTERNAL)
ENTITY_TYPE_NAMES: Mapping[str, EntityType] = MappingProxyType(_ENTITY_TYPE_NAMES_INTERNAL)


def lookup_entity_type(name: Any) -> EntityType:
    """
    Fungsi lookup tipe entitas dengan validasi strict fail-fast.
    Menolak manipulasi tipe data terselubung dan mengamankan integritas runtime ontologi.
    """
    if not isinstance(name, str):
        logger.error("ENTITY_TYPE_LOOKUP_REJECTED_NON_STRING_INPUT: %r", name)
        raise TypeError("ENTITY_TYPE_NAME_MUST_BE_A_PURE_STRING")

    clean_name = name.strip()
    if not clean_name:
        logger.error("ENTITY_TYPE_LOOKUP_REJECTED_EMPTY_OR_WHITESPACE")
        raise ValueError("ENTITY_TYPE_NAME_CANNOT_BE_EMPTY_OR_WHITESPACE")

    resolved_type: Optional[EntityType] = ENTITY_TYPE_NAMES.get(clean_name)
    if resolved_type is None:
        logger.error("ENTITY_TYPE_LOOKUP_INVALID_NAME: %s", clean_name)
        raise KeyError(f"INVALID_ONTOLOGY_ENTITY_TYPE_NAME: {clean_name}")

    return resolved_type


def get_entity_family(entity_type: Any) -> List[str]:
    """
    Mengambil taksonomi sub-famili entitas berdasarkan tipe entitas hulu.
    Menjamin proteksi data terhadap manipulasi referensi array (defensive copy return).
    """
    if not isinstance(entity_type, EntityType):
        logger.error("ENTITY_FAMILY_LOOKUP_REJECTED_INVALID_TYPE: %r", entity_type)
        raise TypeError("ARGUMENT_MUST_BE_AN_INSTANCE_OF_ENTITY_TYPE_ENUM")

    family_list: Optional[List[str]] = ENTITY_FAMILIES.get(entity_type)
    if family_list is None:
        logger.debug("ENTITY_FAMILY_NOT_FOUND_FOR_ENTITY_TYPE: %s", entity_type.value)
        return []

    return list(family_list)