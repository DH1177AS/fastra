# fastra_core\digital_twin\sync.py

from __future__ import annotations

import json
import logging
import math
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator

from fastra_core.identity import Identity
from fastra_core.serialization.canonical_json import to_json

logger = logging.getLogger("fastra_core.digital_twin.sync")


class OfflineStore(BaseModel):
    
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=False,
        allow_inf_nan=False,
    )

    records: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    pending_ids: List[str] = Field(default_factory=list)

    @property
    def _records(self) -> Dict[str, Dict[str, Any]]:
        return self.records
    
    @field_validator("records", mode="before")
    @classmethod
    def validate_records_dict(cls, value: Any) -> Dict[str, Dict[str, Any]]:
        if not isinstance(value, dict):
            logger.error("OFFLINE_RECORDS_MUST_BE_DICT: %r", value)
            raise TypeError("RECORDS_MUST_BE_A_VALID_DICTIONARY")
        for k, v in value.items():
            if not isinstance(k, str) or not k.strip():
                logger.error("OFFLINE_RECORD_INVALID_KEY: %r", k)
                raise ValueError("RECORD_KEYS_MUST_BE_NON_EMPTY_STRINGS")
            if not isinstance(v, dict):
                logger.error("OFFLINE_RECORD_VALUE_NOT_DICT at key %s: %r", k, v)
                raise TypeError(f"RECORD_VALUE_AT_KEY_{k}_MUST_BE_A_DICTIONARY")
        return value

    @field_validator("pending_ids", mode="before")
    @classmethod
    def validate_pending_ids(cls, value: Any) -> List[str]:
        if not isinstance(value, list):
            logger.error("PENDING_IDS_MUST_BE_LIST: %r", value)
            raise TypeError("PENDING_IDS_MUST_BE_A_LIST")
        clean_ids: List[str] = []
        for idx, item in enumerate(value):
            if not isinstance(item, str) or not item.strip():
                logger.error("PENDING_IDS_INVALID_ITEM_%d: %r", idx, item)
                raise ValueError(f"PENDING_ID_AT_INDEX_{idx}_MUST_BE_A_NON_EMPTY_STRING")
            clean_ids.append(item.strip())
        return clean_ids

    def save_record(
        self,
        record_type: str,
        data: Dict[str, Any],
        created_at: Optional[datetime] = None,
    ) -> str:
        if not isinstance(record_type, str) or not record_type.strip():
            logger.error("RECORD_TYPE_INVALID: %r", record_type)
            raise ValueError("RECORD_TYPE_CANNOT_BE_EMPTY_OR_WHITESPACE")
        if not isinstance(data, dict):
            logger.error("RECORD_DATA_INVALID: %r", data)
            raise TypeError("RECORD_DATA_MUST_BE_A_VALID_DICTIONARY")
        if created_at is not None and not isinstance(created_at, (datetime, str)):
            logger.error("CREATED_AT_INVALID_TYPE: %r", created_at)
            raise TypeError("CREATED_AT_MUST_BE_DATETIME_OR_STRING")

        local_id = Identity.generate()
        timestamp = created_at or datetime.now(timezone.utc)

        # Defensive clone to prevent external mutation
        record_entry = {
            "local_id": local_id,
            "record_type": record_type.strip(),
            "data": dict(data),
            "created_at": timestamp.isoformat() if isinstance(timestamp, datetime) else str(timestamp),
            "synced": False,
        }
        self.records[local_id] = record_entry
        self.pending_ids.append(local_id)
        logger.info("Offline record saved: %s", local_id)
        return local_id

    def get_record(self, local_id: str) -> Optional[Dict[str, Any]]:
        if not isinstance(local_id, str) or not local_id.strip():
            logger.error("GET_RECORD_INVALID_ID: %r", local_id)
            raise ValueError("LOCAL_ID_CANNOT_BE_EMPTY_OR_WHITESPACE")
        if not Identity.is_valid(local_id.strip()):
            logger.error("GET_RECORD_INVALID_UUID: %s", local_id)
            raise ValueError("INVALID_LOCAL_ID_STRUCTURE")
        return self.records.get(local_id.strip())

    def get_pending_records(self) -> List[Dict[str, Any]]:
        return [
            self.records[i]
            for i in self.pending_ids
            if i in self.records and not self.records[i].get("synced", False)
        ]

    def mark_synced(self, local_id: str) -> None:
        if not isinstance(local_id, str) or not local_id.strip():
            logger.error("MARK_SYNCED_INVALID_ID: %r", local_id)
            raise ValueError("LOCAL_ID_CANNOT_BE_EMPTY_OR_WHITESPACE")
        clean_id = local_id.strip()
        if clean_id not in self.records:
            logger.error("MARK_SYNCED_ID_NOT_FOUND: %s", clean_id)
            raise KeyError(f"RECORD_NOT_FOUND: {clean_id}")
        self.records[clean_id]["synced"] = True

    def count_pending(self) -> int:
        return len(self.get_pending_records())

    def count_total(self) -> int:
        return len(self.records)


class SQLiteOfflineStore:
    """Penyimpanan offline berbasis SQLite persisten terproteksi."""

    def __init__(self, db_path: str = ":memory:") -> None:
        if not isinstance(db_path, str) or not db_path.strip():
            raise ValueError("PERSISTENCE_ERROR_DATABASE_PATH_CANNOT_BE_NULL_OR_EMPTY")

        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()

        if db_path != ":memory:":
            self.conn.execute("PRAGMA journal_mode=WAL;")

        self._create_table()
        logger.info("SQLite offline store initialized: %s", db_path)

    def _create_table(self) -> None:
        with self._lock:
            try:
                self.conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS offline_records (
                        local_id TEXT PRIMARY KEY,
                        record_type TEXT NOT NULL,
                        data TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        synced INTEGER NOT NULL DEFAULT 0
                    )
                    """
                )
                self.conn.commit()
            except sqlite3.Error as exc:
                self.conn.rollback()
                logger.error("OFFLINE_TABLE_CREATION_FAILED: %s", exc)
                raise RuntimeError(f"DATABASE_INITIALIZATION_FAILED: {exc}") from exc

    def _verify_numeric_integrity(self, node: Any) -> None:
        if node is None:
            return
        if isinstance(node, dict):
            for v in node.values():
                self._verify_numeric_integrity(v)
        elif isinstance(node, (list, tuple, set)):
            for item in node:
                self._verify_numeric_integrity(item)
        elif isinstance(node, (int, float)) and not isinstance(node, bool):
            if math.isnan(node) or math.isinf(node):
                raise ValueError("NUMERIC_ANOMALY_DETECTED_SYNC_STATE_CONTAINS_NAN_OR_INFINITE_VALUE")

    def _sanitize_json_loads(self, raw_str: Optional[str]) -> Any:
        if not raw_str or not raw_str.strip():
            return {}
        try:
            parsed = json.loads(raw_str)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.error("INVALID_JSON_IN_OFFLINE_STORE: %r", raw_str)
            raise ValueError(f"OFFLINE_JSON_CORRUPTION: {exc}") from exc
        self._verify_numeric_integrity(parsed)
        return parsed

    def save_record(
        self,
        record_type: str,
        data: Dict[str, Any],
        created_at: Optional[datetime] = None,
    ) -> str:
        if not isinstance(record_type, str) or not record_type.strip():
            logger.error("SAVE_RECORD_INVALID_RECORD_TYPE: %r", record_type)
            raise ValueError("RECORD_TYPE_CANNOT_BE_EMPTY")
        if not isinstance(data, dict):
            logger.error("SAVE_RECORD_INVALID_DATA: %r", data)
            raise TypeError("RECORD_DATA_MUST_BE_A_DICTIONARY")
        if created_at is not None and not isinstance(created_at, (datetime, str)):
            logger.error("SAVE_RECORD_INVALID_CREATED_AT: %r", created_at)
            raise TypeError("CREATED_AT_MUST_BE_DATETIME_OR_STRING")

        self._verify_numeric_integrity(data)

        local_id = Identity.generate()
        ts = created_at or datetime.now(timezone.utc)
        ts_str = ts.isoformat() if isinstance(ts, datetime) else str(ts)

        with self._lock:
            cursor = self.conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO offline_records (local_id, record_type, data, created_at, synced)
                    VALUES (?, ?, ?, ?, 0)
                    """,
                    (local_id, record_type.strip(), to_json(data), ts_str),
                )
                self.conn.commit()
                logger.info("Offline SQLite record saved: %s", local_id)
                return local_id
            except sqlite3.Error as exc:
                self.conn.rollback()
                logger.error("OFFLINE_SQLITE_SAVE_FAILED: %s", exc)
                raise RuntimeError(f"OFFLINE_QUEUE_TRANSACTION_FAILED: {exc}") from exc

    def get_record(self, local_id: str) -> Optional[Dict[str, Any]]:
        if not isinstance(local_id, str) or not local_id.strip():
            logger.error("GET_RECORD_INVALID_ID: %r", local_id)
            raise ValueError("LOCAL_ID_CANNOT_BE_EMPTY_OR_WHITESPACE")
        if not Identity.is_valid(local_id.strip()):
            logger.error("GET_RECORD_INVALID_UUID: %s", local_id)
            raise ValueError("INVALID_LOCAL_ID_STRUCTURE")

        clean_id = local_id.strip()
        with self._lock:
            row = self.conn.execute(
                "SELECT * FROM offline_records WHERE local_id = ?", (clean_id,)
            ).fetchone()
            if row is None:
                return None
            return {
                "local_id": row["local_id"],
                "record_type": row["record_type"],
                "data": self._sanitize_json_loads(row["data"]),
                "created_at": row["created_at"],
                "synced": bool(row["synced"]),
            }

    def get_pending_records(self) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self.conn.execute("SELECT * FROM offline_records WHERE synced = 0").fetchall()
            return [
                {
                    "local_id": r["local_id"],
                    "record_type": r["record_type"],
                    "data": self._sanitize_json_loads(r["data"]),
                    "created_at": r["created_at"],
                    "synced": False,
                }
                for r in rows
            ]

    def mark_synced(self, local_id: str) -> None:
        if not isinstance(local_id, str) or not local_id.strip():
            logger.error("MARK_SYNCED_INVALID_ID: %r", local_id)
            raise ValueError("LOCAL_ID_CANNOT_BE_EMPTY_OR_WHITESPACE")
        if not Identity.is_valid(local_id.strip()):
            logger.error("MARK_SYNCED_INVALID_UUID: %s", local_id)
            raise ValueError("INVALID_LOCAL_ID_STRUCTURE")

        clean_id = local_id.strip()
        with self._lock:
            try:
                self.conn.execute(
                    "UPDATE offline_records SET synced = 1 WHERE local_id = ?", (clean_id,)
                )
                self.conn.commit()
            except sqlite3.Error as exc:
                self.conn.rollback()
                logger.error("OFFLINE_SQLITE_MARK_SYNCED_FAILED: %s", exc)
                raise RuntimeError(f"DATABASE_TRANSACTION_FAILED_MARK_SYNCED: {exc}") from exc

    def count_pending(self) -> int:
        with self._lock:
            row = self.conn.execute(
                "SELECT COUNT(*) AS cnt FROM offline_records WHERE synced = 0"
            ).fetchone()
            return int(row["cnt"]) if row else 0

    def count_total(self) -> int:
        with self._lock:
            row = self.conn.execute(
                "SELECT COUNT(*) AS cnt FROM offline_records"
            ).fetchone()
            return int(row["cnt"]) if row else 0

    def close(self) -> None:
        with self._lock:
            self.conn.close()
            logger.info("SQLite offline store connection closed")


class SyncResult(BaseModel):
    """
    Model representasi laporan ringkasan eksekusi sinkronisasi data (Sync Report Ledger).
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    pushed_count: int = Field(default=0, ge=0)
    pulled_count: int = Field(default=0, ge=0)
    pending_after: int = Field(default=0, ge=0)
    details: Tuple[Dict[str, Any], ...] = Field(default_factory=tuple)


class SyncEngine(BaseModel):
    """
    Mesin orkestrasi rekonsiliasi data sinkronisasi (Offline-First Reconciliation Engine).
    Strategi penyelesaian konflik: Last-Write-Wins terpotong stempel kronologis.
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=False,
        allow_inf_nan=False,
    )

    server_store: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    def push(self, offline_store: Any) -> SyncResult:
        """
        Mendorong antrean lokal menuju server pusat digital twin secara atomik.
        """
        if offline_store is None or not hasattr(offline_store, "get_pending_records"):
            logger.error("INVALID_OFFLINE_STORE_INSTANCE: %r", offline_store)
            raise TypeError("INVALID_OFFLINE_STORE_INSTANCE_PROVIDED")

        pushed = 0
        details_list: List[Dict[str, Any]] = []

        for record in offline_store.get_pending_records():
            rec_id = record["local_id"]

            # Defensive clone data before transmission
            self.server_store[rec_id] = dict(record["data"])
            offline_store.mark_synced(rec_id)

            pushed += 1
            details_list.append(
                {
                    "local_id": rec_id,
                    "record_type": record["record_type"],
                    "status": "PUSHED",
                }
            )

        logger.info("Push completed: %d records sent", pushed)
        return SyncResult(
            pushed_count=pushed,
            pulled_count=0,
            pending_after=int(offline_store.count_pending()),
            details=tuple(details_list),
        )

    def pull(self) -> List[Dict[str, Any]]:
        return [dict(v) for v in self.server_store.values()]

    def resolve_conflict(
        self,
        local_data: Dict[str, Any],
        server_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Menyelesaikan sengketa tumpang tindih mutasi data (Conflict Resolution Matrix).
        Mengimplementasikan strategi Last-Write-Wins berbasis penalaan ISO stempel waktu.
        """
        if not isinstance(local_data, dict) or not isinstance(server_data, dict):
            logger.error("CONFLICT_INPUTS_MUST_BE_DICTS: local=%r server=%r", local_data, server_data)
            raise TypeError("CONFLICT_RESOLUTION_INPUTS_MUST_BE_PURE_DICTIONARIES")

        local_ts_raw = local_data.get("updated_at", "")
        server_ts_raw = server_data.get("updated_at", "")

        local_ts = str(local_ts_raw).strip()
        server_ts = str(server_ts_raw).strip()

        # Last-Write-Wins: memilih entri dengan timestamp paling baru.
        # Jika kedua kosong, pilih data lokal.
        if not local_ts and not server_ts:
            return dict(local_data)

        if local_ts >= server_ts:
            return dict(local_data)

        return dict(server_data)