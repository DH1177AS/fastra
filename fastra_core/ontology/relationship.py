from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict
from fastra_core.ontology.entity_type import EntityType

class RelationshipType(Enum):
    CONTAINS = "CONTAINS"
    CONNECTED_TO = "CONNECTED_TO"
    SUPPORTS = "SUPPORTS"
    USES = "USES"
    PRODUCES = "PRODUCES"
    REFERENCES = "REFERENCES"
    DEPENDS_ON = "DEPENDS_ON"
    ASSIGNED_TO = "ASSIGNED_TO"
    COSTED_BY = "COSTED_BY"
    VERSION_OF = "VERSION_OF"

class Direction(Enum):
    DIRECTED = "DIRECTED"
    UNDIRECTED = "UNDIRECTED"

VALID_RELATION_PAIRS = {
    RelationshipType.CONTAINS: (EntityType.SPATIAL, EntityType.SPATIAL),
    RelationshipType.CONNECTED_TO: (EntityType.PHYSICAL, EntityType.PHYSICAL),
    RelationshipType.SUPPORTS: (EntityType.PHYSICAL, EntityType.PHYSICAL),
    RelationshipType.USES: (EntityType.PROCESS, EntityType.RESOURCE),
    RelationshipType.PRODUCES: (EntityType.PROCESS, EntityType.PHYSICAL),
    RelationshipType.REFERENCES: (None, None),
    RelationshipType.DEPENDS_ON: (EntityType.TEMPORAL, EntityType.TEMPORAL),
    RelationshipType.ASSIGNED_TO: (None, None),
    RelationshipType.COSTED_BY: (None, EntityType.ECONOMIC),
    RelationshipType.VERSION_OF: (None, None),
}

@dataclass
class Relationship:
    source_uuid: str
    target_uuid: str
    relationship_type: RelationshipType
    direction: Direction = Direction.DIRECTED
    properties: Dict[str, Any] = field(default_factory=dict)
# Relasi Semantik untuk ACES-300 Layer 2
HAS_SYNONYM = "HAS_SYNONYM"
CONSISTS_OF = "CONSISTS_OF"
PREREQUISITE_OF = "PREREQUISITE_OF"
ALTERNATIVE_TO = "ALTERNATIVE_TO"
COMPATIBLE_WITH = "COMPATIBLE_WITH"
IS_A = "IS_A"
INSTANCE_OF = "INSTANCE_OF"
MEMILIKI_HARGA = "MEMILIKI_HARGA"
MEMERLUKAN_MATERIAL = "MEMERLUKAN_MATERIAL"
MEMERLUKAN_TENAGA_KERJA = "MEMERLUKAN_TENAGA_KERJA"
MEMERLUKAN_PERALATAN = "MEMERLUKAN_PERALATAN"

SEMANTIC_RELATIONSHIPS = {
    HAS_SYNONYM: "Istilah alternatif untuk item yang sama",
    CONSISTS_OF: "Dekomposisi item menjadi sub-item",
    PREREQUISITE_OF: "Item yang harus diselesaikan terlebih dahulu",
    ALTERNATIVE_TO: "Item yang dapat menggantikan",
    COMPATIBLE_WITH: "Material yang kompatibel",
    IS_A: "Klasifikasi ontologis",
    INSTANCE_OF: "Keanggotaan kelas",
    MEMILIKI_HARGA: "Resource memiliki harga di wilayah tertentu",
    MEMERLUKAN_MATERIAL: "Item pekerjaan memerlukan material",
    MEMERLUKAN_TENAGA_KERJA: "Item pekerjaan memerlukan tenaga kerja",
    MEMERLUKAN_PERALATAN: "Item pekerjaan memerlukan peralatan",
}
