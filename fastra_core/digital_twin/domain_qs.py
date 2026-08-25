"""
ACES-600 Domain QS Services
Progress weighting otomatis, VO propagation, as-built finalization, archive restore.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastra_core.digital_twin.database_extended import ExtendedDigitalTwinDB
from fastra_core.digital_twin import Snapshot, ProgressEntry, ChangeOrder, AsBuiltRecord, ArchiveRecord, AuditEvent


class QSDomainService:
    def __init__(self, db: ExtendedDigitalTwinDB):
        self.db = db

    def calculate_progress_weight_map(self, project_uuid: str) -> Dict[str, float]:
        """
        Hitung bobot progress per work_item_code dari snapshot terakhir.
        Menggunakan total biaya dari RAB jika tersedia, jika tidak menggunakan quantity.
        """
        snapshots = self.db.list_snapshots(project_uuid)
        if not snapshots:
            return {}
        # gunakan snapshot terakhir
        latest = snapshots[-1]
        boq = latest.boq_state or {}
        weights: Dict[str, float] = {}
        divisions = boq.get("divisions", {})
        total_cost = 0.0
        item_costs: Dict[str, float] = {}
        for div in divisions.values():
            for item in div.get("items", []):
                code = item.get("item_code") or item.get("code")
                if not code:
                    continue
                cost = item.get("total_price") or item.get("subtotal") or item.get("cost")
                if cost is None:
                    cost = float(item.get("quantity", 0.0))
                item_costs[code] = float(cost)
                total_cost += float(cost)
        if total_cost > 0:
            for code, cost in item_costs.items():
                weights[code] = cost / total_cost
        return weights

    def propagate_vo(self, vo_uuid: str) -> Dict[str, Any]:
        """
        Simulasi propagasi VO: hitung net cost impact dari cost_impact.
        """
        vo = self.db.get_change_order(vo_uuid)
        if vo is None:
            return {"error": "VO not found"}
        net_change = vo.calculate_cost_impact()
        self.db.save_change_order(vo)
        return {
            "vo_uuid": vo_uuid,
            "net_change": net_change,
            "status": vo.status,
        }

    def finalize_as_built(self, project_uuid: str, as_built_entity_states: Optional[Dict[str, Any]] = None) -> Snapshot:
        """
        Buat snapshot AS_BUILT final untuk project.
        Menggabungkan ccm_state dari snapshot terakhir dengan as_built_entity_states.
        """
        snapshots = self.db.list_snapshots(project_uuid)
        if not snapshots:
            raise ValueError("No snapshots found")
        latest = snapshots[-1]
        ccm_state = latest.ccm_state.copy()
        entities = ccm_state.get("entities", {})
        if as_built_entity_states:
            for eid, state in as_built_entity_states.items():
                if eid in entities:
                    entities[eid].update(state)
                else:
                    entities[eid] = state
        ccm_state["entities"] = entities
        snap = Snapshot(
            snapshot_uuid=str(uuid4()),
            snapshot_name="As-Built Final",
            snapshot_type="AS_BUILT",
            project_uuid=project_uuid,
            timestamp=datetime.now(timezone.utc).isoformat(),
            ccm_state=ccm_state,
            boq_state=latest.boq_state,
            rab_state=latest.rab_state,
            schedule_state=latest.schedule_state,
            description="Final as-built snapshot",
        )
        self.db.save_snapshot(snap)
        return snap

    def restore_archive(self, archive_uuid: str) -> int:
        """
        Restore archive ke database: simpan kembali snapshot, as-built records.
        Mengembalikan jumlah record yang direstore.
        """
        archive = self.db.get_archive_record(archive_uuid)
        if archive is None:
            return 0
        restored = 0
        for snap_dict in archive.snapshots:
            snap = Snapshot(
                snapshot_uuid=snap_dict.get("snapshot_uuid", str(uuid4())),
                snapshot_name=snap_dict.get("snapshot_name", "Restored"),
                snapshot_type=snap_dict.get("snapshot_type", "CHECKPOINT"),
                project_uuid=snap_dict.get("project_uuid", "unknown"),
                timestamp=snap_dict.get("timestamp", datetime.now(timezone.utc).isoformat()),
                description=snap_dict.get("description", ""),
                ccm_state=snap_dict.get("ccm_state", {}),
                boq_state=snap_dict.get("boq_state"),
                rab_state=snap_dict.get("rab_state"),
                schedule_state=snap_dict.get("schedule_state"),
                metadata=snap_dict.get("metadata", {}),
            )
            self.db.save_snapshot(snap)
            restored += 1
        for asb_dict in archive.as_built_records:
            rec = AsBuiltRecord(
                project_uuid=asb_dict.get("project_uuid", "unknown"),
                entity_uuid=asb_dict.get("entity_uuid", ""),
                planned_state=asb_dict.get("planned_state", {}),
                as_built_state=asb_dict.get("as_built_state", {}),
                record_uuid=asb_dict.get("record_uuid", str(uuid4())),
            )
            self.db.save_as_built_record(rec)
            restored += 1
        return restored
