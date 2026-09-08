from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastra_core.digital_twin.audit import AuditStore
from fastra_core.digital_twin.snapshot import Snapshot, SnapshotStore
from fastra_core.identity import Identity

logger = logging.getLogger("fastra_core.digital_twin.query")


def _parse_iso_safe(s: Any) -> Optional[datetime]:
    if isinstance(s, datetime):
        if s.tzinfo is None:
            return s.replace(tzinfo=timezone.utc)
        return s.astimezone(timezone.utc)

    if not isinstance(s, str) or not s.strip():
        return None

    try:
        dt = datetime.fromisoformat(s.strip())
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (ValueError, OverflowError) as exc:
        logger.warning("Invalid ISO datetime string: %r (%s)", s, exc)
        return None


class QueryEngine:
    def __init__(self, snapshot_store: SnapshotStore, audit_store: AuditStore) -> None:
        if not isinstance(snapshot_store, SnapshotStore):
            logger.error("QUERY_ENGINE_SNAPSHOT_STORE_TYPE_MISMATCH: %r", snapshot_store)
            raise TypeError("SNAPSHOT_STORE_MUST_BE_AN_INSTANCE_OF_SNAPSHOT_STORE")
        if not isinstance(audit_store, AuditStore):
            logger.error("QUERY_ENGINE_AUDIT_STORE_TYPE_MISMATCH: %r", audit_store)
            raise TypeError("AUDIT_STORE_MUST_BE_AN_INSTANCE_OF_AUDIT_STORE")

        self.snapshot_store = snapshot_store
        self.audit_store = audit_store

    def get_state_at_date(self, project_uuid: str, target_date: str) -> Optional[Snapshot]:
        if not isinstance(project_uuid, str) or not Identity.is_valid(project_uuid):
            raise ValueError(f"QUERY_ENGINE_VIOLATION_INVALID_PROJECT_UUID_STRUCTURE: {project_uuid}")

        target_dt = _parse_iso_safe(target_date)
        if target_dt is None:
            logger.error("Invalid ISO target date: %r", target_date)
            raise ValueError(f"QUERY_ENGINE_VIOLATION_INVALID_ISO_TARGET_DATE_FORMAT: '{target_date}'")

        candidates: List[Tuple[datetime, Snapshot]] = []
        for s in self.snapshot_store.get_all_snapshots(project_uuid):
            if not isinstance(s, Snapshot):
                logger.warning("Skipping non-Snapshot object in store: %r", s)
                continue
            snap_dt = _parse_iso_safe(s.timestamp)
            if snap_dt is not None and snap_dt <= target_dt:
                candidates.append((snap_dt, s))

        if not candidates:
            logger.info("No snapshot at or before %s for project %s", target_dt.isoformat(), project_uuid)
            return None

        candidates.sort(key=lambda item: item[0], reverse=True)
        latest_snapshot = candidates[0][1]
        logger.debug("Recovered snapshot %s at %s", latest_snapshot.snapshot_uuid, target_dt.isoformat())
        return latest_snapshot

    def get_audit_trail_for_entity(self, entity_uuid: str) -> List[Dict[str, Any]]:
        if not isinstance(entity_uuid, str) or not Identity.is_valid(entity_uuid):
            raise ValueError(f"QUERY_ENGINE_VIOLATION_INVALID_ENTITY_UUID_STRUCTURE: {entity_uuid}")

        events = self.audit_store.get_events_by_entity(entity_uuid)
        return [e.to_dict() for e in events]

    def get_rab_trend(self, project_uuid: str) -> List[Dict[str, Any]]:
        if not isinstance(project_uuid, str) or not Identity.is_valid(project_uuid):
            raise ValueError(f"QUERY_ENGINE_VIOLATION_INVALID_PROJECT_UUID_STRUCTURE: {project_uuid}")

        trend: List[Dict[str, Any]] = []
        for snap in self.snapshot_store.get_all_snapshots(project_uuid):
            if not isinstance(snap, Snapshot):
                logger.warning("Skipping non-Snapshot object: %r", snap)
                continue
            if snap.rab_state is None:
                continue

            rab_state = snap.rab_state
            grand_total: Optional[float] = None

            if isinstance(rab_state, dict):
                raw_total = rab_state.get("grand_total")
                if raw_total is None and isinstance(rab_state.get("summary"), dict):
                    raw_total = rab_state["summary"].get("grand_total")

                if raw_total is not None:
                    if isinstance(raw_total, dict) and "value" in raw_total:
                        grand_total = float(raw_total["value"])
                    else:
                        try:
                            grand_total = float(raw_total)
                        except (TypeError, ValueError) as exc:
                            logger.error("Invalid grand_total value in snapshot %s: %r", snap.snapshot_uuid, raw_total)
                            raise ValueError(
                                f"INVALID_RAB_GRAND_TOTAL_IN_SNAPSHOT_{snap.snapshot_uuid}"
                            ) from exc

            if grand_total is not None:
                if isinstance(grand_total, bool) or math.isnan(grand_total) or math.isinf(grand_total):
                    logger.error("RAB grand_total numeric anomaly in snapshot %s: %s", snap.snapshot_uuid, grand_total)
                    raise ValueError(
                        f"NUMERIC_ANOMALY_DETECTED_IN_RAB_GRAND_TOTAL_TREND_AT_SNAPSHOT_{snap.snapshot_uuid}"
                    )

            trend.append({
                "snapshot_uuid": snap.snapshot_uuid,
                "snapshot_name": str(snap.snapshot_name).strip(),
                "timestamp": snap.timestamp.isoformat() if isinstance(snap.timestamp, datetime) else str(snap.timestamp),
                "grand_total": grand_total,
            })

        logger.debug("RAB trend produced %d points for project %s", len(trend), project_uuid)
        return trend

    def trace_rab_to_ccm(self, snapshot_uuid: str, rab_item_code: str) -> List[str]:
        if not isinstance(snapshot_uuid, str) or not snapshot_uuid.strip():
            raise ValueError(f"QUERY_ENGINE_VIOLATION_INVALID_SNAPSHOT_UUID_STRUCTURE: {snapshot_uuid}")

        if not isinstance(rab_item_code, str) or not rab_item_code.strip():
            raise ValueError("QUERY_ENGINE_VIOLATION_INVALID_RAB_ITEM_CODE_PARAMETER")

        snapshot = self.snapshot_store.get_snapshot(snapshot_uuid)
        if snapshot is None or snapshot.boq_state is None:
            logger.info("Snapshot %s not found or has no BOQ state", snapshot_uuid)
            return []

        boq_state = snapshot.boq_state
        entities = snapshot.ccm_state.get("entities", {})
        if not isinstance(entities, dict):
            return []

        divisions = boq_state.get("divisions", {})
        if not isinstance(divisions, dict):
            return []

        clean_item_code = rab_item_code.strip()

        for div in divisions.values():
            if not isinstance(div, dict):
                continue
            items = div.get("items", [])
            if not isinstance(items, (list, tuple)):
                continue

            for item in items:
                if not isinstance(item, dict):
                    continue

                if item.get("item_code") == clean_item_code or item.get("code") == clean_item_code:
                    source_entities = item.get("source_entities", [])
                    if not isinstance(source_entities, (list, tuple)):
                        continue

                    result = [
                        str(eid).strip()
                        for eid in source_entities
                        if eid and isinstance(eid, str) and eid.strip() in entities
                    ]
                    logger.debug("Trace RAB item %s -> %d entities", clean_item_code, len(result))
                    return result

        return []