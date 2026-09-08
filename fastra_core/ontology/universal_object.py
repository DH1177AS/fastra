# fastra_core\ontology\universal_object.py

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from fastra_core.identity import Identity
from fastra_core.ontology.entity_type import EntityType
from fastra_core.ontology.lifecycle import LifecycleStatus, is_valid_transition

logger = logging.getLogger("fastra.ontology.universal_object")


class LifecycleHistoryEntry(BaseModel):
    """
    Model representasi log riwayat transisi status siklus hidup objek (Immutable Audit Trail).
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
                allow_inf_nan=False,
    )

    from_status: LifecycleStatus
    to_status: LifecycleStatus
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: str = Field(default="system", min_length=3, max_length=128)
    change_reason: str = Field(..., min_length=5, max_length=512)


class UniversalObject(BaseModel):
    """
    Model Inti Universal Object (Ontology Root Entity).
    Mengunci keabsahan seluruh siklus hidup entitas grafik dengan mode frozen murni.
    Sistem mutasi wajib melintasi gerbang replikasi baru demi menjamin kepatuhan audit trail.
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        allow_inf_nan=False,
    )

    uuid: str = Field(
        default_factory=Identity.generate,
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    )
    id: Optional[str] = Field(default=None, min_length=1, max_length=64)
    unit: Optional[str] = Field(default=None, min_length=1, max_length=16)
    name: str = Field(default="Unnamed Object", min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1024)
    entity_type: EntityType = Field(default=EntityType.PHYSICAL)
    version: int = Field(default=1, ge=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = Field(default="system", min_length=3, max_length=128)
    updated_by: str = Field(default="system", min_length=3, max_length=128)
    change_reason: Optional[str] = Field(default=None, min_length=5, max_length=512)
    status: LifecycleStatus = Field(default=LifecycleStatus.DRAFT)
    lifecycle_history: Tuple[LifecycleHistoryEntry, ...] = Field(default_factory=tuple)
    tags: Tuple[str, ...] = Field(default_factory=tuple)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("uuid", mode="after")
    @classmethod
    def verify_uuid_integrity(cls, value: str) -> str:
        if not Identity.is_valid(value):
            logger.error("UUID_INTEGRITY_COMPROMISED: %s", value)
            raise ValueError("UUID_INTEGRITY_COMPROMISED_INVALID_STRUCTURE")
        return value

    @field_validator("name", "description", "change_reason", mode="before")
    @classmethod
    def sanitize_strings(cls, value: Any) -> Optional[str]:
        if value is None:
            return None
        if not isinstance(value, str):
            logger.error("STRING_COERCION_REJECTED: %r", value)
            raise TypeError("VALUE_MUST_BE_A_PURE_STRING_COERCION_FORBIDDEN")
        stripped = value.strip()
        if not stripped and value != "":
            logger.error("WHITESPACE_ONLY_STRING_REJECTED")
            raise ValueError("STRING_CANNOT_CONSIST_OF_WHITESPACE_ONLY")
        return stripped

    @field_validator("metadata", mode="before")
    @classmethod
    def validate_metadata_content(cls, value: Any) -> Dict[str, Any]:
        if not isinstance(value, dict):
            logger.error("METADATA_NON_DICT_REJECTED: %r", value)
            raise TypeError("METADATA_MUST_BE_A_VALID_DICTIONARY")
        for k, v in value.items():
            if not isinstance(k, str) or not k.strip():
                logger.error("METADATA_INVALID_KEY: %r", k)
                raise ValueError("METADATA_KEYS_MUST_BE_NON_EMPTY_STRINGS")
            if isinstance(v, (dict, list, set)):
                logger.error("METADATA_DEEP_NESTED_MUTABLE_REJECTED at key %s", k)
                raise TypeError("DEEP_NESTED_MUTABLE_STRUCTURES_FORBIDDEN_IN_METADATA_ROOT")
        return value

    @model_validator(mode="after")
    def verify_temporal_chronology(self) -> "UniversalObject":
        if self.updated_at < self.created_at:
            logger.error(
                "CHRONOLOGICAL_ANOMALY: updated_at=%s < created_at=%s",
                self.updated_at,
                self.created_at,
            )
            raise ValueError("CHRONOLOGICAL_ANOMALY_UPDATED_AT_CANNOT_PREDATE_CREATED_AT")
        return self

    def copy_with_update(
        self, updated_by: str, change_reason: str, **kwargs: Any
    ) -> "UniversalObject":
        """
        Melakukan pembaruan atribut objek secara aman melalui mekanisme replikasi defensif.
        Menghasilkan instansiasi objek baru yang terisolasi penuh dengan increment versi otomatis.
        """
        if any(
            key in kwargs
            for key in ("uuid", "created_at", "created_by", "version")
        ):
            logger.error("IMMUTABLE_CORE_MUTATION_ATTEMPT: %s", kwargs.keys())
            raise ValueError("IMMUTABLE_CORE_ATTRIBUTES_CANNOT_BE_MUTATED_BY_CONSUMER")

        clean_updated_by = str(updated_by).strip()
        clean_change_reason = str(change_reason).strip()

        if len(clean_updated_by) < 3 or len(clean_change_reason) < 5:
            logger.error(
                "UPDATE_METADATA_LENGTH_VIOLATION: updated_by=%r, reason=%r",
                clean_updated_by,
                clean_change_reason,
            )
            raise ValueError("UPDATED_BY_AND_CHANGE_REASON_MUST_FULFILL_MINIMUM_LENGTHS")

        current_data = self.model_dump()

        # Ekstrak data immutable koleksi agar tidak terpolusi referensinya
        current_metadata = dict(current_data.pop("metadata", {}))
        current_tags = list(current_data.pop("tags", ()))
        current_history = list(self.lifecycle_history)

        # Timpa data payload internal dengan parameter input kwargs yang sah
        for key, val in kwargs.items():
            if key in current_data:
                current_data[key] = val
            elif key == "metadata" and isinstance(val, dict):
                current_metadata.update(val)
            elif key == "tags" and isinstance(val, (list, tuple)):
                current_tags = list(val)
            else:
                logger.error("UNKNOWN_UPDATE_FIELD_REJECTED: %s", key)
                raise ValueError(f"UNKNOWN_UPDATE_FIELD: {key}")

        current_data["version"] = self.version + 1
        current_data["updated_at"] = datetime.now(timezone.utc)
        current_data["updated_by"] = clean_updated_by
        current_data["change_reason"] = clean_change_reason
        current_data["metadata"] = current_metadata
        current_data["tags"] = tuple(current_tags)
        current_data["lifecycle_history"] = tuple(current_history)

        return UniversalObject(**current_data)

    def transition_status(
        self,
        new_status: LifecycleStatus,
        updated_by: str,
        change_reason: str,
    ) -> "UniversalObject":
        """
        Menjalankan proses perpindahan status siklus hidup secara formal dan aman.
        Mencatatkan histori lama ke penampung log audit trail secara permanen.
        """
        if not isinstance(new_status, LifecycleStatus):
            logger.error("TRANSITION_TARGET_TYPE_REJECTED: %r", new_status)
            raise TypeError("TARGET_STATUS_MUST_BE_AN_INSTANCE_OF_LIFECYCLE_STATUS_ENUM")

        if not is_valid_transition(self.status, new_status):
            logger.error(
                "ILLEGAL_LIFECYCLE_TRANSITION: %s -> %s",
                self.status.value,
                new_status.value,
            )
            raise ValueError(
                f"ILLEGAL_LIFECYCLE_TRANSITION: {self.status.value} -> {new_status.value}"
            )

        clean_updated_by = str(updated_by).strip()
        clean_change_reason = str(change_reason).strip()

        new_history_entry = LifecycleHistoryEntry(
            from_status=self.status,
            to_status=new_status,
            updated_by=clean_updated_by,
            change_reason=clean_change_reason,
        )

        extended_history = list(self.lifecycle_history)
        extended_history.append(new_history_entry)

        return self.copy_with_update(
            updated_by=clean_updated_by,
            change_reason=clean_change_reason,
            status=new_status,
            lifecycle_history=tuple(extended_history),
        )

    def transition_to(self, new_status: LifecycleStatus, updated_by: str = "system", change_reason: str = "Lifecycle transition") -> "UniversalObject":
        """
        Melakukan transisi status siklus hidup secara in-place dengan tetap mematuhi
        seluruh pemeriksaan keabsahan transisi dan audit trail.
        """
        if not isinstance(new_status, LifecycleStatus):
            raise TypeError("TARGET_STATUS_MUST_BE_AN_INSTANCE_OF_LIFECYCLE_STATUS_ENUM")

        if not is_valid_transition(self.status, new_status):
            raise ValueError(
                f"ILLEGAL_LIFECYCLE_TRANSITION: {self.status.value} -> {new_status.value}"
            )

        clean_updated_by = str(updated_by).strip()
        clean_change_reason = str(change_reason).strip()

        new_history_entry = LifecycleHistoryEntry(
            from_status=self.status,
            to_status=new_status,
            updated_by=clean_updated_by,
            change_reason=clean_change_reason,
        )

        # Mutasi internal terkontrol
        object.__setattr__(self, "status", new_status)
        object.__setattr__(self, "updated_by", clean_updated_by)
        object.__setattr__(self, "change_reason", clean_change_reason)
        object.__setattr__(self, "updated_at", datetime.now(timezone.utc))
        object.__setattr__(self, "version", self.version + 1)
        object.__setattr__(self, "lifecycle_history", tuple(list(self.lifecycle_history) + [new_history_entry]))
        return self
