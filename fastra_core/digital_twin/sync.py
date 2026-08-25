"""
ACES-600 Offline-First Sync Engine (hardened)
Menyimpan data lokal (SQLite), antrian upload, dan sinkronisasi.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


class OfflineStore:
    """
    Penyimpanan offline in-memory (untuk kompatibilitas). 
    Gunakan SQLiteOfflineStore untuk persistensi nyata.
    """

    def __init__(self) -> None:
        self._records: Dict[str, Dict[str, Any]] = {}
        self._pending_ids: List[str] = []

    def save_record(self, record_type: str, data: Dict[str, Any], created_at: Optional[str] = None) -> str:
        local_id = str(uuid4())
        self._records[local_id] = {
            "local_id": local_id,
            "record_type": record_type,
            "data": data,
            "created_at": created_at or datetime.now(timezone.utc).isoformat(),
            "synced": False,
        }
        self._pending_ids.append(local_id)
        return local_id

    def get_record(self, local_id: str) -> Optional[Dict[str, Any]]:
        return self._records.get(local_id)

    def get_pending_records(self) -> List[Dict[str, Any]]:
        return [self._records[i] for i in self._pending_ids if not self._records[i]["synced"]]

    def mark_synced(self, local_id: str) -> None:
        if local_id in self._records:
            self._records[local_id]["synced"] = True

    def count_pending(self) -> int:
        return len(self.get_pending_records())

    def count_total(self) -> int:
        return len(self._records)


class SQLiteOfflineStore:
    """Penyimpanan offline berbasis SQLite (persisten)."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS offline_records (
                local_id TEXT PRIMARY KEY,
                record_type TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                synced INTEGER NOT NULL DEFAULT 0
            )
        """)
        self.conn.commit()

    def save_record(self, record_type: str, data: Dict[str, Any], created_at: Optional[str] = None) -> str:
        local_id = str(uuid4())
        self.conn.execute(
            "INSERT INTO offline_records (local_id, record_type, data, created_at, synced) VALUES (?, ?, ?, ?, 0)",
            (
                local_id, record_type,
                json.dumps(data, default=str),
                created_at or datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()
        return local_id

    def get_record(self, local_id: str) -> Optional[Dict[str, Any]]:
        row = self.conn.execute("SELECT * FROM offline_records WHERE local_id = ?", (local_id,)).fetchone()
        if row is None:
            return None
        return {
            "local_id": row["local_id"],
            "record_type": row["record_type"],
            "data": json.loads(row["data"]),
            "created_at": row["created_at"],
            "synced": bool(row["synced"]),
        }

    def get_pending_records(self) -> List[Dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM offline_records WHERE synced = 0").fetchall()
        return [
            {
                "local_id": r["local_id"],
                "record_type": r["record_type"],
                "data": json.loads(r["data"]),
                "created_at": r["created_at"],
                "synced": bool(r["synced"]),
            }
            for r in rows
        ]

    def mark_synced(self, local_id: str) -> None:
        self.conn.execute("UPDATE offline_records SET synced = 1 WHERE local_id = ?", (local_id,))
        self.conn.commit()

    def count_pending(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) FROM offline_records WHERE synced = 0").fetchone()
        return row[0]

    def count_total(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) FROM offline_records").fetchone()
        return row[0]

    def close(self) -> None:
        self.conn.close()


@dataclass
class SyncResult:
    pushed_count: int
    pulled_count: int
    pending_after: int
    details: List[Dict[str, Any]] = field(default_factory=list)


class SyncEngine:
    """Mesin sinkronisasi offline-first. Conflict resolution: last-write-wins."""

    def __init__(self) -> None:
        self.server_store: Dict[str, Dict[str, Any]] = {}

    def push(self, offline_store) -> SyncResult:
        pushed = 0
        details = []
        for record in offline_store.get_pending_records():
            self.server_store[record["local_id"]] = record["data"]
            offline_store.mark_synced(record["local_id"])
            pushed += 1
            details.append({
                "local_id": record["local_id"],
                "record_type": record["record_type"],
                "status": "PUSHED",
            })
        return SyncResult(
            pushed_count=pushed,
            pulled_count=0,
            pending_after=offline_store.count_pending(),
            details=details,
        )

    def pull(self) -> List[Dict[str, Any]]:
        return list(self.server_store.values())

    def resolve_conflict(self, local_data: Dict[str, Any], server_data: Dict[str, Any]) -> Dict[str, Any]:
        local_ts = local_data.get("updated_at", "")
        server_ts = server_data.get("updated_at", "")
        if local_ts >= server_ts:
            return local_data
        return server_data
