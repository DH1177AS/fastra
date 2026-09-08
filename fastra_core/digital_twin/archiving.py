from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator

from fastra_core.identity import Identity
from fastra_core.serialization.hash import canonical_hash
from fastra_core.serialization.canonical_json import to_json

from fastra_core.digital_twin.snapshot import SnapshotStore
from fastra_core.digital_twin.as_built import AsBuiltStore
from fastra_core.digital_twin.audit import AuditStore

logger = logging.getLogger("fastra_core.digital_twin.archiving")

# === DEBUG SEMENTARA: simpan JSON kanonik saat create, untuk dibandingkan saat verify ===
_DEBUG_CANONICAL_JSON_AT_CREATE: Dict[str, str] = {}
# === END DEBUG GLOBALS ===


class ArchiveRecord(BaseModel):
    """Model arsip digital twin dengan perhitungan checksum deterministik."""
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    archive_uuid: str = Field(default_factory=lambda: str(Identity.generate()), min_length=1, max_length=64)
    project_uuid: str = Field(..., min_length=1, max_length=64)
    archived_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    project_metadata: Dict[str, Any] = Field(default_factory=dict)
    snapshots: Tuple[Dict[str, Any], ...] = Field(default_factory=tuple)
    as_built_records: Tuple[Dict[str, Any], ...] = Field(default_factory=tuple)
    audit_events: Tuple[Dict[str, Any], ...] = Field(default_factory=tuple)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    checksum: str = Field(default="", min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")

    @field_validator("project_metadata", "metadata", mode="before")
    @classmethod
    def validate_metadata_dict(cls, value: Any) -> Dict[str, Any]:
        if not isinstance(value, dict):
            raise TypeError("METADATA_MUST_BE_A_DICTIONARY")
        return value

    @field_validator("snapshots", "as_built_records", "audit_events", mode="before")
    @classmethod
    def validate_tuple_of_dicts(cls, value: Any) -> Tuple[Any, ...]:
        if not isinstance(value, (list, tuple)):
            raise TypeError("COLLECTION_MUST_BE_A_LIST_OR_TUPLE")
        return tuple(value)

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "archive_uuid": self.archive_uuid,
            "project_uuid": self.project_uuid,
            "archived_at": self.archived_at,
            "project_metadata": self.project_metadata,
            "snapshots": self.snapshots,
            "as_built_records": self.as_built_records,
            "audit_events": self.audit_events,
            "metadata": self.metadata,
        }

    def calculate_canonical_checksum(self) -> str:
        return canonical_hash(self.to_canonical_dict())

    def verify_integrity(self) -> bool:
        """Verifikasi checksum arsip terhadap data saat ini."""
        if not self.checksum:
            return False
        expected = self.calculate_canonical_checksum()
        match = expected == self.checksum
        if not match:
            logger.error(
                "ARCHIVE_CHECKSUM_MISMATCH: archive=%s expected=%s actual=%s",
                self.archive_uuid,
                expected,
                self.checksum,
            )
            # === DEBUG SEMENTARA: auto-diff JSON kanonik create vs verify ===
            try:
                json_at_verify = to_json(self.to_canonical_dict())
                json_at_create = _DEBUG_CANONICAL_JSON_AT_CREATE.get(self.archive_uuid)
                if json_at_create is None:
                    logger.error(
                        "DEBUG_NO_CREATE_TIME_SNAPSHOT_FOUND_FOR: %s "
                        "(archive dibuat di proses/objek store yang berbeda?)",
                        self.archive_uuid,
                    )
                elif json_at_create == json_at_verify:
                    logger.error(
                        "DEBUG_JSON_STRINGS_ARE_IDENTICAL_BUT_HASH_DIFFERS: %s "
                        "-> BUG ADA DI canonical_hash()/hashlib SENDIRI, BUKAN DI SERIALISASI",
                        self.archive_uuid,
                    )
                else:
                    import difflib
                    diff = "\n".join(
                        difflib.unified_diff(
                            [json_at_create],
                            [json_at_verify],
                            fromfile="at_create",
                            tofile="at_verify",
                            lineterm="",
                        )
                    )
                    logger.error("DEBUG_CANONICAL_JSON_DIFF:\n%s", diff)
                    with open(os.path.join(tempfile.gettempdir(), f"archive_debug_{self.archive_uuid}_create.json"), "w", encoding="utf-8") as f:
                        f.write(json_at_create)
                    with open(os.path.join(tempfile.gettempdir(), f"archive_debug_{self.archive_uuid}_verify.json"), "w", encoding="utf-8") as f:
                        f.write(json_at_verify)
                    logger.error(
                        "DEBUG_FULL_DUMPS_WRITTEN_TO: /tmp/archive_debug_%s_create.json AND _verify.json",
                        self.archive_uuid,
                    )
            except Exception as dump_exc:
                logger.error("DEBUG_INSTRUMENTATION_FAILED: %s", dump_exc)
            # === END DEBUG ===
        return match


class ArchiveStore(BaseModel):
    """Penyimpanan arsip digital twin."""
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=False,
        allow_inf_nan=False,
    )

    archives: Dict[str, ArchiveRecord] = Field(default_factory=dict)

    def create_archive(
        self,
        project_uuid: str,
        snapshot_store: SnapshotStore,
        as_built_store: AsBuiltStore,
        audit_store: AuditStore,
        project_metadata: Optional[Dict[str, Any]] = None,
        archived_at: Optional[datetime | str] = None,
    ) -> ArchiveRecord:
        """Buat arsip baru dengan data yang konsisten untuk checksum."""
        if not isinstance(project_uuid, str) or not project_uuid.strip():
            raise ValueError(f"INVALID_PROJECT_UUID_STRUCTURE: {project_uuid}")

        if archived_at is None:
            archived_at_iso = datetime.now(timezone.utc).isoformat()
        elif isinstance(archived_at, datetime):
            archived_at_iso = archived_at.isoformat()
        elif isinstance(archived_at, str):
            archived_at_iso = archived_at
        else:
            raise TypeError("ARCHIVED_AT_MUST_BE_DATETIME_OR_STRING")

        snapshots_raw = [s.model_dump(mode="json") for s in snapshot_store.get_all_snapshots(project_uuid)]
        as_built_raw = [r.model_dump(mode="json") for r in as_built_store.get_all_records(project_uuid)]
        audit_raw = [e.model_dump(mode="json") for e in audit_store.get_all_events()]

        temp_record_data = {
            "archive_uuid": str(Identity.generate()),
            "project_uuid": project_uuid,
            "archived_at": archived_at_iso,
            "project_metadata": project_metadata or {},
            "snapshots": snapshots_raw,
            "as_built_records": as_built_raw,
            "audit_events": audit_raw,
            "metadata": {},
            "checksum": "0" * 64,
        }

        interim_record = ArchiveRecord.model_validate(temp_record_data)
        computed_checksum = interim_record.calculate_canonical_checksum()

        final_record_data = dict(temp_record_data)
        final_record_data["checksum"] = computed_checksum

        final_archive = ArchiveRecord.model_validate(final_record_data)
        self.archives[final_archive.archive_uuid] = final_archive

        # === DEBUG SEMENTARA: simpan JSON kanonik persis saat ini untuk dibandingkan nanti ===
        _DEBUG_CANONICAL_JSON_AT_CREATE[final_archive.archive_uuid] = to_json(final_archive.to_canonical_dict())
        # === END DEBUG ===

        logger.info("Archive created: %s", final_archive.archive_uuid)
        return final_archive

    def get_archive(self, archive_uuid: str) -> Optional[ArchiveRecord]:
        if not isinstance(archive_uuid, str) or not archive_uuid.strip():
            raise ValueError(f"INVALID_QUERY_ARCHIVE_UUID: {archive_uuid}")
        return self.archives.get(archive_uuid)

    def list_archives(self, project_uuid: Optional[str] = None) -> List[ArchiveRecord]:
        if project_uuid is not None:
            if not isinstance(project_uuid, str) or not project_uuid.strip():
                raise ValueError(f"INVALID_QUERY_PROJECT_UUID: {project_uuid}")
            return [a for a in self.archives.values() if a.project_uuid == project_uuid]
        return list(self.archives.values())

    def restore_archive(self, archive_uuid: str) -> ArchiveRecord:
        """Pulihkan arsip dengan verifikasi checksum."""
        archive = self.get_archive(archive_uuid)
        if archive is None:
            raise KeyError(f"ARCHIVE_RECORD_NOT_FOUND_FOR_UUID: {archive_uuid}")

        if not archive.verify_integrity():
            raise ValueError(
                f"CRYPTOGRAPHIC_INTEGRITY_VIOLATION: Archive record '{archive_uuid}' tampered."
            )

        restored_data = archive.model_dump(mode="json")
        restored_data["archive_uuid"] = str(Identity.generate())
        restored_data["checksum"] = "0" * 64

        interim_restored = ArchiveRecord.model_validate(restored_data)
        new_checksum = interim_restored.calculate_canonical_checksum()

        final_restored_data = dict(restored_data)
        final_restored_data["checksum"] = new_checksum

        restored_archive = ArchiveRecord.model_validate(final_restored_data)
        logger.info("Archive restored: %s", restored_archive.archive_uuid)
        return restored_archive