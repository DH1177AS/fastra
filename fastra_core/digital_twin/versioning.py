from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.dataclasses import dataclass

from fastra_core.identity import Identity

logger = logging.getLogger("fastra_core.digital_twin.versioning")


class VersionError(ValueError):
    """Pengecualian khusus untuk kesalahan semantik tata kelola versi (Versioning Domain Exception)."""


@dataclass(frozen=True)
class Version:
    """
    Primitive Value Object untuk merepresentasikan Pengidentifikasi Versi (MAJOR.MINOR.PATCH).
    Mengunci integritas nomor rilis konstruksi secara rigid tanpa toleransi terhadap coercion hacks.
    """
    major: int
    minor: int
    patch: int

    def __post_init__(self):
        # Validasi ketat manual menggantikan field_validator
        for name, value in (("major", self.major), ("minor", self.minor), ("patch", self.patch)):
            if isinstance(value, bool):
                logger.error("VERSION_COMPONENT_BOOLEAN_REJECTED: %r", value)
                raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
            if not isinstance(value, int):
                logger.error("VERSION_COMPONENT_NON_INTEGER_REJECTED: %r", value)
                raise TypeError("VERSION_COMPONENT_MUST_BE_A_PURE_INTEGER")
            if value < 0:
                logger.error("VERSION_COMPONENT_NEGATIVE_REJECTED: %s", value)
                raise ValueError("VERSION_COMPONENT_MUST_BE_NON_NEGATIVE")

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def parse(cls, s: Any) -> "Version":
        """
        Mengurai string teks (misal '1.2.3') menjadi instansiasi objek Version murni.
        Memotong whitespace zombie secara fail-fast hulu.
        """
        if not isinstance(s, str) or not s.strip():
            logger.error("VERSION_PARSE_INVALID_INPUT: %r", s)
            raise VersionError(f"Format versi tidak valid: {s!r}")

        parts = s.strip().split(".")
        if len(parts) != 3:
            logger.error("VERSION_PARSE_TOKEN_COUNT_VIOLATION: %s", s)
            raise VersionError(f"SEMANTIC_VERSION_FORMAT_VIOLATION_MUST_CONTAIN_THREE_TOKENS: '{s}'")

        try:
            # Pydantic otomatis memvalidasi keabsahan token integer di gerbang pengisian
            return cls(major=int(parts[0]), minor=int(parts[1]), patch=int(parts[2]))
        except (ValueError, TypeError) as e:
            logger.error("VERSION_PARSE_COMPONENT_INVALID: %s", e)
            raise VersionError(f"Format komponen nomor versi tidak valid: {s!r}") from e

    def next_major(self) -> "Version":
        return Version(major=self.major + 1, minor=0, patch=0)

    def next_minor(self) -> "Version":
        return Version(major=self.major, minor=self.minor + 1, patch=0)

    def next_patch(self) -> "Version":
        return Version(major=self.major, minor=self.minor, patch=self.patch + 1)


class VersionNode(BaseModel):
    """
    Model representasi simpul riwayat versi (DAG Ledger Entry Node).
    Dilengkapi validasi regex ketat UUID v4 serta penolakan penunjuk kosong.
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    version: Version
    entity_type: str = Field(..., min_length=2, max_length=64)
    entity_id: str = Field(..., min_length=3, max_length=128)
    branch: str = Field(default="main", min_length=2, max_length=64, pattern=r"^[A-Za-z0-9\-\_]+$")
    parent_id: Optional[str] = Field(
        default=None,
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$|^$",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
    id: str = Field(
        default_factory=Identity.generate,
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    )

    @field_validator("id", mode="after")
    @classmethod
    def verify_uuid_integrity(cls, value: str) -> str:
        if not Identity.is_valid(value):
            logger.error("VERSION_NODE_INVALID_UUID: %s", value)
            raise ValueError("UUID_INTEGRITY_COMPROMISED_INVALID_STRUCTURE")
        return value

    @field_validator("entity_type", "entity_id", "branch", mode="before")
    @classmethod
    def sanitize_strings(cls, value: Any) -> str:
        if not isinstance(value, str):
            logger.error("VERSION_NODE_STRING_COERCION_REJECTED: %r", value)
            raise TypeError("VALUE_MUST_BE_A_PURE_STRING_COERCION_FORBIDDEN")
        stripped = value.strip()
        if not stripped:
            logger.error("VERSION_NODE_EMPTY_STRING_REJECTED")
            raise ValueError("CORE_VERSION_NODE_STRING_CANNOT_BE_EMPTY_OR_WHITESPACE")
        return stripped

    @field_validator("metadata", mode="before")
    @classmethod
    def validate_metadata_content(cls, value: Any) -> Dict[str, Any]:
        if not isinstance(value, dict):
            logger.error("VERSION_NODE_METADATA_NOT_DICT: %r", value)
            raise TypeError("METADATA_MUST_BE_A_VALID_DICTIONARY")
        for k, v in value.items():
            if not isinstance(k, str) or not k.strip():
                logger.error("VERSION_NODE_METADATA_INVALID_KEY: %r", k)
                raise ValueError("METADATA_KEYS_MUST_BE_NON_EMPTY_STRINGS")
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                if math.isnan(v) or math.isinf(v):
                    logger.error("VERSION_NODE_METADATA_NUMERIC_ANOMALY at key %s: %s", k, v)
                    raise ValueError(f"NUMERIC_ANOMALY_DETECTED_IN_METADATA_VALUE_AT_KEY_{k}")
        return value

    def __str__(self) -> str:
        return f"{self.entity_type}:{self.entity_id}@{self.version} [{self.branch}]"


class VersionGraph(BaseModel):
    """
    Directed Acyclic Graph (DAG) untuk penalaan tata kelola versi independen entitas.
    Mendukung percabangan (Branching) dan rekonsiliasi penggabungan (Merge Logic).
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=False,
        allow_inf_nan=False,
    )

    nodes: Dict[str, VersionNode] = Field(default_factory=dict)
    children: Dict[str, List[str]] = Field(default_factory=dict)
    branches: Dict[str, str] = Field(default_factory=lambda: {"main": ""})  # branch name -> head node id

    def add_version(
        self,
        entity_type: str,
        entity_id: str,
        version: Version,
        parent_id: Optional[str] = None,
        branch: str = "main",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> VersionNode:
        """
        Menambahkan mata rantai simpul versi baru ke dalam struktur grafik komposit DAG.
        """
        if not isinstance(version, Version):
            logger.error("ADD_VERSION_INVALID_VERSION_TYPE: %r", version)
            raise TypeError("VERSION_MUST_BE_AN_INSTANCE_OF_VERSION_CLASS")

        clean_branch = str(branch).strip()
        if not clean_branch:
            logger.error("ADD_VERSION_EMPTY_BRANCH")
            raise VersionError("BRANCH_NAME_CANNOT_BE_EMPTY_OR_WHITESPACE")

        if clean_branch not in self.branches:
            # Regulasi Cabang Baru: Cabang anyar diwajibkan mendeklarasikan simpul induk jangkar hulu
            if parent_id is None:
                logger.error("NEW_BRANCH_WITHOUT_PARENT: %s", clean_branch)
                raise VersionError(f"Cabang {clean_branch!r} memerlukan parent_id")
            self.branches[clean_branch] = parent_id

        node_payload = {
            "version": version,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "branch": clean_branch,
            "parent_id": parent_id,
            "metadata": dict(metadata) if metadata is not None else {},
        }

        # Instansiasi node tervalidasi via Pydantic
        node = VersionNode.model_validate(node_payload)

        # Proteksi deteksi dini ancaman sirkular (Self-Looping Protection)
        if parent_id and node.id == parent_id:
            logger.error("SELF_LOOP_DETECTED: %s", node.id)
            raise VersionError("CIRCULAR_DEPENDENCY_VIOLATION_NODE_CANNOT_BE_ITS_OWN_PARENT")

        if parent_id:
            if parent_id not in self.nodes:
                logger.error("PARENT_NOT_FOUND: %s", parent_id)
                raise VersionError(f"Parent {parent_id} tidak ditemukan dalam struktur grafik")

            child_list = self.children.setdefault(parent_id, [])
            if node.id not in child_list:
                child_list.append(node.id)

        self.nodes[node.id] = node
        self.branches[clean_branch] = node.id
        logger.info("Version node added: %s", node.id)
        return node

    def get_node(self, node_id: str) -> Optional[VersionNode]:
        if not isinstance(node_id, str) or not node_id.strip():
            logger.warning("GET_NODE_INVALID_ID: %r", node_id)
            return None
        return self.nodes.get(node_id.strip())

    def get_head(self, branch: str = "main") -> Optional[VersionNode]:
        if not isinstance(branch, str) or not branch.strip():
            logger.warning("GET_HEAD_INVALID_BRANCH: %r", branch)
            return None
        head_id = self.branches.get(branch.strip())
        if head_id and head_id.strip():
            return self.nodes.get(head_id)
        return None

    def list_branches(self) -> List[str]:
        return list(self.branches.keys())

    def get_ancestors(self, node_id: str) -> List[VersionNode]:
        """
        Menyusuri garis silsilah leluhur hulu (Ancestors Lineage Walkthrough) secara non-rekursif.
        Menerapkan batas pengaman sirkular tak berujung (Infinite Loop Boundary Protection).
        """
        if not isinstance(node_id, str) or not node_id.strip():
            logger.error("GET_ANCESTORS_INVALID_NODE_ID: %r", node_id)
            raise VersionError("NODE_ID_CANNOT_BE_EMPTY_OR_WHITESPACE")

        ancestors: List[VersionNode] = []
        seen_path: Set[str] = set()

        current_id: Optional[str] = node_id.strip()
        while current_id:
            if current_id in seen_path:
                logger.error("CIRCULAR_LOOP_DETECTED_AT_NODE: %s", current_id)
                raise VersionError(f"CRITICAL_GRAPH_CORRUPTION_CIRCULAR_LOOP_DETECTED_AT_NODE_{current_id}")
            seen_path.add(current_id)

            node = self.get_node(current_id)
            if node is None:
                break
            if node.parent_id is None:
                break

            parent = self.get_node(node.parent_id)
            if parent is not None:
                ancestors.append(parent)
                current_id = parent.id
            else:
                break

        return ancestors

    def merge(self, source_branch: str, target_branch: str = "main") -> VersionNode:
        """
        Mengeksekusi konsolidasi peleburan data state antar cabang (Branch Merge Service).
        Mengimplementasikan strategi evaluasi kronologis minor increment otomatis.
        """
        clean_src = str(source_branch).strip()
        clean_tgt = str(target_branch).strip()

        if not clean_src or not clean_tgt:
            logger.error("MERGE_INVALID_BRANCH_NAMES: src=%r tgt=%r", source_branch, target_branch)
            raise VersionError("BRANCH_NAME_CANNOT_BE_EMPTY_OR_WHITESPACE")

        if clean_src not in self.branches or clean_tgt not in self.branches:
            logger.error("MERGE_BRANCH_NOT_FOUND: src=%s tgt=%s", clean_src, clean_tgt)
            raise VersionError("Cabang sumber (source) atau target penggabungan tidak ditemukan")

        source_head = self.get_head(clean_src)
        target_head = self.get_head(clean_tgt)

        if source_head is None:
            logger.error("MERGE_SOURCE_BRANCH_EMPTY: %s", clean_src)
            raise VersionError(f"Cabang sumber '{clean_src}' dalam keadaan kosong")

        # Fast-Forward Guard: Jika kedua head sudah sepadan, batalkan peleburan redundan secara atomik
        if target_head is not None and source_head.id == target_head.id:
            logger.info("MERGE_FAST_FORWARD_REDUNDANT: %s == %s", source_head.id, target_head.id)
            return target_head

        # Penentuan kriteria penomoran versi rilis anyar hasil merge
        if target_head:
            new_version = target_head.version.next_minor()
        else:
            new_version = source_head.version.next_major()

        # Pemetaan silsilah dependensi relasi simpul induk
        parent_id = target_head.id if target_head else source_head.id

        merge_metadata = {
            "merged_from": clean_src,
            "merged_from_node": source_head.id,
            "source_version": str(source_head.version),
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }

        # Menambahkan simpul anyar hasil merge menuju target branch
        merged_node = self.add_version(
            entity_type=source_head.entity_type,
            entity_id=source_head.entity_id,
            version=new_version,
            parent_id=parent_id,
            branch=clean_tgt,
            metadata=merge_metadata,
        )

        logger.info("Branches merged: %s -> %s, new node=%s", clean_src, clean_tgt, merged_node.id)
        return merged_node

    def to_dict(self) -> Dict[str, Any]:
        """
        Kompilasi serialisasi grafik internal untuk kebutuhan snapshot repositori database hulu.
        """
        return {
            "nodes": {k: v.model_dump() for k, v in self.nodes.items()},
            "children": {k: list(v) for k, v in self.children.items()},
            "branches": dict(self.branches),
        }