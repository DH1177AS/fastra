"""
ACES-600 Digital Twin Archiving (hardened)
Arsip dengan checksum SHA-256, determinisme, dan restore ke store asal.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastra_core.digital_twin.snapshot import Snapshot, SnapshotStore
from fastra_core.digital_twin.as_built import AsBuiltStore
from fastra_core.digital_twin.audit import AuditStore


@dataclass
class ArchiveRecord:
    archive_uuid: str = field(default_factory=lambda: str(uuid4()))
    project_uuid: str = ""
    archived_at: str = ""
    project_metadata: Dict[str, Any] = field(default_factory=dict)
    snapshots: List[Dict[str, Any]] = field(default_factory=list)
    as_built_records: List[Dict[str, Any]] = field(default_factory=list)
    audit_events: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    checksum: str = ""

    def compute_checksum(self) -> str:
        """Hitung SHA-256 dari seluruh data arsip."""
        data = {
            "project_uuid": self.project_uuid,
            "archived_at": self.archived_at,
            "project_metadata": self.project_metadata,
            "snapshots": self.snapshots,
            "as_built_records": self.as_built_records,
            "audit_events": self.audit_events,
        }
        canonical = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
        self.checksum = hashlib.sha256(canonical).hexdigest()
        return self.checksum

    def to_dict(self) -> Dict[str, Any]:
        return {
            "archive_uuid": self.archive_uuid,
            "project_uuid": self.project_uuid,
            "archived_at": self.archived_at,
            "project_metadata": self.project_metadata,
            "snapshots": self.snapshots,
            "as_built_records": self.as_built_records,
            "audit_events": self.audit_events,
            "metadata": self.metadata,
            "checksum": self.checksum,
        }


class ArchiveStore:
    """Penyimpanan arsip in-memory dengan checksum dan restore."""

    def __init__(self) -> None:
        self._archives: Dict[str, ArchiveRecord] = {}

    def create_archive(
        self,
        project_uuid: str,
        snapshot_store: SnapshotStore,
        as_built_store: AsBuiltStore,
        audit_store: AuditStore,
        project_metadata: Optional[Dict[str, Any]] = None,
        archived_at: Optional[str] = None,
    ) -> ArchiveRecord:
        snapshots = [s.to_dict() for s in snapshot_store.get_all_snapshots(project_uuid)]
        as_built_records = [
            {"record_uuid": r.record_uuid, "entity_uuid": r.entity_uuid,
             "planned_state": r.planned_state, "as_built_state": r.as_built_state,
             "differences": [d.__dict__ for d in r.differences]}
            for r in as_built_store.get_all_records(project_uuid)
        ]
        audit_events = [e.to_dict() for e in audit_store.get_all_events()]

        archive = ArchiveRecord(
            project_uuid=project_uuid,
            archived_at=archived_at or datetime.now(timezone.utc).isoformat(),
            project_metadata=project_metadata or {},
            snapshots=snapshots,
            as_built_records=as_built_records,
            audit_events=audit_events,
        )
        archive.compute_checksum()
        self._archives[archive.archive_uuid] = archive
        return archive

    def get_archive(self, archive_uuid: str) -> Optional[ArchiveRecord]:
        return self._archives.get(archive_uuid)

    def list_archives(self, project_uuid: Optional[str] = None) -> List[ArchiveRecord]:
        if project_uuid:
            return [a for a in self._archives.values() if a.project_uuid == project_uuid]
        return list(self._archives.values())

    def restore_archive(self, archive_uuid: str) -> Optional[ArchiveRecord]:
        """Restore dari arsip: mengembalikan salinan lengkap dengan UUID baru."""
        archive = self.get_archive(archive_uuid)
        if archive is None:
            return None
        restored = ArchiveRecord(
            project_uuid=archive.project_uuid,
            archived_at=archive.archived_at,
            project_metadata=archive.project_metadata.copy(),
            snapshots=[s.copy() for s in archive.snapshots],
            as_built_records=[r.copy() for r in archive.as_built_records],
            audit_events=[e.copy() for e in archive.audit_events],
        )
        restored.compute_checksum()
        return restored
