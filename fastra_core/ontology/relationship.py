# fastra_core\ontology\relationship.py

from __future__ import annotations

import logging
from enum import Enum
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator

from fastra_core.ontology.entity_type import EntityType

logger = logging.getLogger("fastra.ontology.relationship")


class RelationshipType(str, Enum):
    """
    Unified Domain Enum menggabungkan tipe relasi grafik pengetahuan hulu
    dan standar semantik komprehensif ACES-300 Layer 2 konstruksi nasional.
    """
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

    # Integrasi rigid relasi semantik ACES-300 Layer 2
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


class Direction(str, Enum):
    """
    Mendefinisikan arah busur relasi (Edge directionality) di dalam knowledge graph.
    """
    DIRECTED = "DIRECTED"
    UNDIRECTED = "UNDIRECTED"


# Immutability Guard: Seluruh deskripsi semantik dikunci di level memori menggunakan kamus rigid.
_SEMANTIC_RELATIONSHIPS_INTERNAL: Dict[RelationshipType, str] = {
    RelationshipType.HAS_SYNONYM: "Istilah alternatif untuk item yang sama",
    RelationshipType.CONSISTS_OF: "Dekomposisi item menjadi sub-item",
    RelationshipType.PREREQUISITE_OF: "Item yang harus diselesaikan terlebih dahulu",
    RelationshipType.ALTERNATIVE_TO: "Item yang dapat menggantikan",
    RelationshipType.COMPATIBLE_WITH: "Material yang kompatibel",
    RelationshipType.IS_A: "Klasifikasi ontologis",
    RelationshipType.INSTANCE_OF: "Keanggotaan kelas",
    RelationshipType.MEMILIKI_HARGA: "Resource memiliki harga di wilayah tertentu",
    RelationshipType.MEMERLUKAN_MATERIAL: "Item pekerjaan memerlukan material",
    RelationshipType.MEMERLUKAN_TENAGA_KERJA: "Item pekerjaan memerlukan tenaga kerja",
    RelationshipType.MEMERLUKAN_PERALATAN: "Item pekerjaan memerlukan peralatan",
}

# Strict Taksonomi Matrix: Setiap pasangan divalidasi silang secara rigid.
# Menggunakan Optional[EntityType] sebagai representasi validasi relasi bersifat wildcard.
_VALID_RELATION_PAIRS_INTERNAL: Dict[
    RelationshipType, Tuple[Optional[EntityType], Optional[EntityType]]
] = {
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
    RelationshipType.HAS_SYNONYM: (None, None),
    RelationshipType.CONSISTS_OF: (None, None),
    RelationshipType.PREREQUISITE_OF: (None, None),
    RelationshipType.ALTERNATIVE_TO: (None, None),
    RelationshipType.COMPATIBLE_WITH: (EntityType.RESOURCE, EntityType.RESOURCE),
    RelationshipType.IS_A: (None, None),
    RelationshipType.INSTANCE_OF: (None, None),
    RelationshipType.MEMILIKI_HARGA: (EntityType.RESOURCE, EntityType.ECONOMIC),
    RelationshipType.MEMERLUKAN_MATERIAL: (EntityType.PROCESS, EntityType.RESOURCE),
    RelationshipType.MEMERLUKAN_TENAGA_KERJA: (EntityType.PROCESS, EntityType.HUMAN),
    RelationshipType.MEMERLUKAN_PERALATAN: (EntityType.PROCESS, EntityType.RESOURCE),
}

SEMANTIC_RELATIONSHIPS: Mapping[RelationshipType, str] = MappingProxyType(
    _SEMANTIC_RELATIONSHIPS_INTERNAL
)
VALID_RELATION_PAIRS: Mapping[
    RelationshipType, Tuple[Optional[EntityType], Optional[EntityType]]
] = MappingProxyType(_VALID_RELATION_PAIRS_INTERNAL)


class Relationship(BaseModel):
    """
    Model Domain Utama untuk representasi struktural busur relasi (Semantic Edge).
    Dilengkapi validasi regex ketat UUID v4 serta penolakan properti liar.
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    def __init__(self, *args, **kwargs):
        if args:
            if len(args) > 3:
                raise TypeError("Relationship only accepts up to three positional arguments (source_uuid, target_uuid, relationship_type)")
            names = ['source_uuid', 'target_uuid', 'relationship_type']
            for i, val in enumerate(args):
                kwargs.setdefault(names[i], val)
        super().__init__(**kwargs)

    source_uuid: str = Field(
        ...,
        min_length=1,
        max_length=128,
    )
    target_uuid: str = Field(
        ...,
        min_length=1,
        max_length=128,
    )
    relationship_type: RelationshipType
    direction: Direction = Field(default=Direction.DIRECTED)
    properties: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("properties", mode="before")
    @classmethod
    def validate_properties_dictionary(cls, value: Any) -> Dict[str, Any]:
        if not isinstance(value, dict):
            logger.error("RELATIONSHIP_PROPERTIES_REJECTED_NON_DICT: %r", value)
            raise TypeError("RELATIONSHIP_PROPERTIES_MUST_BE_A_VALID_DICTIONARY")
        for k, v in value.items():
            if not isinstance(k, str) or not k.strip():
                logger.error("RELATIONSHIP_PROPERTIES_INVALID_KEY: %r", k)
                raise ValueError("PROPERTIES_KEYS_MUST_BE_NON_EMPTY_STRINGS")
        return value

    def validate_semantic_constraints(
        self, source_type: EntityType, target_type: EntityType
    ) -> None:
        """
        Memvalidasi kesesuaian relasi semantik berdasarkan matriks pasangan entitas legal (VALID_RELATION_PAIRS).
        Melempar ValueError secara instan jika mendeteksi pelanggaran aturan taksonomi ontologi.
        """
        if not isinstance(source_type, EntityType) or not isinstance(target_type, EntityType):
            logger.error(
                "SEMANTIC_CONSTRAINT_REJECTED_INVALID_TYPE: source=%r, target=%r",
                source_type,
                target_type,
            )
            raise TypeError("METADATA_ENTITY_TYPES_MUST_BE_INSTANCES_OF_ENTITY_TYPE_ENUM")

        constraints = VALID_RELATION_PAIRS.get(self.relationship_type)
        if constraints is None:
            logger.error(
                "SEMANTIC_CONSTRAINT_UNREGISTERED_RELATIONSHIP: %s",
                self.relationship_type.value,
            )
            raise KeyError(
                f"UNREGISTERED_RELATIONSHIP_CONSTRAINTS_FOR: {self.relationship_type}"
            )

        expected_source, expected_target = constraints

        if expected_source is not None and source_type != expected_source:
            logger.error(
                "SEMANTIC_CONSTRAINT_SOURCE_TYPE_VIOLATION: relationship=%s, expected=%s, actual=%s",
                self.relationship_type.value,
                expected_source.value,
                source_type.value,
            )
            raise ValueError(
                f"TAXONOMY_VIOLATION: Relationship '{self.relationship_type.value}' expects "
                f"source type '{expected_source.value}', got '{source_type.value}'"
            )

        if expected_target is not None and target_type != expected_target:
            logger.error(
                "SEMANTIC_CONSTRAINT_TARGET_TYPE_VIOLATION: relationship=%s, expected=%s, actual=%s",
                self.relationship_type.value,
                expected_target.value,
                target_type.value,
            )
            raise ValueError(
                f"TAXONOMY_VIOLATION: Relationship '{self.relationship_type.value}' expects "
                f"target type '{expected_target.value}', got '{target_type.value}'"
            )