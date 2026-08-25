"""
ACES-600 Digital Twin Versioning System
Menyediakan version identifier, version graph (DAG), branching, dan merge.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from uuid import uuid4

class VersionError(ValueError):
    """Exception untuk kesalahan versioning."""


@dataclass(frozen=True)
class Version:
    """Version identifier MAJOR.MINOR.PATCH."""
    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def parse(cls, s: str) -> "Version":
        """Parse string versi, misal '1.2.3'."""
        try:
            parts = s.split(".")
            if len(parts) != 3:
                raise ValueError
            major, minor, patch = map(int, parts)
            return cls(major, minor, patch)
        except (ValueError, TypeError) as e:
            raise VersionError(f"Format versi tidak valid: {s!r}") from e

    def next_major(self) -> "Version":
        return Version(self.major + 1, 0, 0)

    def next_minor(self) -> "Version":
        return Version(self.major, self.minor + 1, 0)

    def next_patch(self) -> "Version":
        return Version(self.major, self.minor, self.patch + 1)


@dataclass
class VersionNode:
    """Node dalam version graph."""
    version: Version
    entity_type: str
    entity_id: str
    branch: str = "main"
    parent_id: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def __str__(self) -> str:
        return f"{self.entity_type}:{self.entity_id}@{self.version} [{self.branch}]"


class VersionGraph:
    """
    Directed Acyclic Graph (DAG) untuk versi entity.
    Mendukung branching dan merge sederhana.
    """

    def __init__(self) -> None:
        self._nodes: Dict[str, VersionNode] = {}
        self._children: Dict[str, List[str]] = {}
        self._branches: Dict[str, str] = {"main": ""}  # branch name -> head node id

    def add_version(
        self,
        entity_type: str,
        entity_id: str,
        version: Version,
        parent_id: Optional[str] = None,
        branch: str = "main",
        metadata: Optional[Dict] = None,
    ) -> VersionNode:
        """Menambahkan node versi baru ke graph."""
        if branch not in self._branches:
            # Cabang baru harus memiliki parent
            if parent_id is None:
                raise VersionError(f"Cabang {branch!r} memerlukan parent_id")
            self._branches[branch] = parent_id

        node = VersionNode(
            version=version,
            entity_type=entity_type,
            entity_id=entity_id,
            branch=branch,
            parent_id=parent_id,
            metadata=metadata or {},
        )
        self._nodes[node.id] = node

        if parent_id:
            if parent_id not in self._nodes:
                raise VersionError(f"Parent {parent_id} tidak ditemukan")
            self._children.setdefault(parent_id, []).append(node.id)

        # Update head cabang
        self._branches[branch] = node.id
        return node

    def get_node(self, node_id: str) -> Optional[VersionNode]:
        return self._nodes.get(node_id)

    def get_head(self, branch: str = "main") -> Optional[VersionNode]:
        head_id = self._branches.get(branch)
        if head_id:
            return self._nodes.get(head_id)
        return None

    def list_branches(self) -> List[str]:
        return list(self._branches.keys())

    def get_ancestors(self, node_id: str) -> List[VersionNode]:
        """Mengembalikan semua ancestor dari node."""
        ancestors = []
        node = self.get_node(node_id)
        while node and node.parent_id:
            node = self.get_node(node.parent_id)
            if node:
                ancestors.append(node)
        return ancestors

    def merge(self, source_branch: str, target_branch: str = "main") -> VersionNode:
        """
        Merge sederhana: mengambil head dari source_branch, membuat versi baru
        di target_branch dengan parent dari head source dan head target (jika berbeda).
        Resolusi konflik tidak diimplementasikan di Fase 1.
        """
        if source_branch not in self._branches or target_branch not in self._branches:
            raise VersionError("Cabang sumber/target tidak ditemukan")
        source_head = self.get_head(source_branch)
        target_head = self.get_head(target_branch)
        if source_head is None:
            raise VersionError(f"Cabang {source_branch} kosong")
        if target_head is not None and source_head.id == target_head.id:
            return target_head

        # Versi baru: minor increment dari target_head, atau fallback ke source_head
        if target_head:
            new_version = target_head.version.next_minor()
        else:
            new_version = source_head.version.next_major()

        # Parent untuk node baru: target_head (jika ada) atau source_head
        parent_id = target_head.id if target_head else source_head.id

        # Metadata merge
        metadata = {
            "merged_from": source_branch,
            "merged_from_node": source_head.id,
            "source_version": str(source_head.version),
        }

        # Buat node baru di target branch
        merged_node = self.add_version(
            entity_type=source_head.entity_type,
            entity_id=source_head.entity_id,
            version=new_version,
            parent_id=parent_id,
            branch=target_branch,
            metadata=metadata,
        )
        return merged_node

    def to_dict(self) -> Dict:
        """Serialisasi graph untuk snapshot."""
        return {
            "nodes": {k: v.__dict__ for k, v in self._nodes.items()},
            "children": self._children,
            "branches": self._branches,
        }
