"""
ACES-600 Digital Twin Query & Reporting (hardened)
Query timestamp robust dengan datetime parsing dan tanpa broad except continue.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastra_core.digital_twin.snapshot import SnapshotStore, Snapshot
from fastra_core.digital_twin.audit import AuditStore


def _parse_iso_safe(s: str) -> Optional[datetime]:
    """Parse ISO 8601 menjadi datetime UTC-aware. Mengembalikan None jika gagal."""
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


class QueryEngine:
    def __init__(self, snapshot_store: SnapshotStore, audit_store: AuditStore) -> None:
        self.snapshot_store = snapshot_store
        self.audit_store = audit_store

    def get_state_at_date(self, project_uuid: str, target_date: str) -> Optional[Snapshot]:
        target_dt = _parse_iso_safe(target_date)
        if target_dt is None:
            return None
        candidates = []
        for s in self.snapshot_store.get_all_snapshots(project_uuid):
            snap_dt = _parse_iso_safe(s.timestamp)
            if snap_dt is not None and snap_dt <= target_dt:
                candidates.append((snap_dt, s))
        if not candidates:
            return None
        candidates.sort(key=lambda x: x[0])
        return candidates[-1][1]

    def get_entity_history(self, entity_uuid: str) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self.audit_store.get_events_by_entity(entity_uuid)]

    def get_rab_trend(self, project_uuid: str) -> List[Dict[str, Any]]:
        trend = []
        for snap in self.snapshot_store.get_all_snapshots(project_uuid):
            if snap.rab_state is None:
                continue
            rab_state = snap.rab_state
            grand_total = None
            if isinstance(rab_state, dict):
                grand_total = rab_state.get("grand_total")
                if grand_total is None and "summary" in rab_state:
                    grand_total = rab_state["summary"].get("grand_total")
            trend.append({
                "snapshot_uuid": snap.snapshot_uuid,
                "snapshot_name": snap.snapshot_name,
                "timestamp": snap.timestamp,
                "grand_total": grand_total,
            })
        return trend

    def trace_rab_to_ccm(self, snapshot_uuid: str, rab_item_code: str) -> List[str]:
        snapshot = self.snapshot_store.get_snapshot(snapshot_uuid)
        if snapshot is None or snapshot.boq_state is None:
            return []
        boq_state = snapshot.boq_state
        entities = snapshot.ccm_state.get("entities", {})
        divisions = boq_state.get("divisions", {})
        for div in divisions.values():
            for item in div.get("items", []):
                if item.get("item_code") == rab_item_code or item.get("code") == rab_item_code:
                    source_entities = item.get("source_entities", [])
                    if source_entities:
                        return [eid for eid in source_entities if eid in entities]
        return []
