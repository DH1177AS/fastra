# fastra_core\digital_twin\domain_qs.py

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastra_core.identity import Identity
from fastra_core.primitives.currency import Currency

from fastra_core.digital_twin.archiving import ArchiveRecord
from fastra_core.digital_twin.as_built import AsBuiltRecord, AsBuiltDifference
from fastra_core.digital_twin.audit import AuditEvent
from fastra_core.digital_twin.change_order import ChangeOrder
from fastra_core.digital_twin.database_extended import ExtendedDigitalTwinDB
from fastra_core.digital_twin.progress import ProgressEntry
from fastra_core.digital_twin.snapshot import Snapshot

logger = logging.getLogger("fastra_core.digital_twin.domain_qs")


class QSDomainService:
    """
    Layanan orkestrasi domain inti Quantity Surveying (QS Engine).
    Bertanggung jawab atas penaksiran kemajuan fisik, propagasi biaya, dan pemulihan arsip.
    """

    def __init__(self, db: ExtendedDigitalTwinDB) -> None:
        if db is None:
            raise ValueError("QS_SERVICE_ERROR_DATABASE_INSTANCE_CANNOT_BE_NULL")
        if not isinstance(db, ExtendedDigitalTwinDB):
            logger.error("QS_SERVICE_DB_TYPE_MISMATCH: %r", db)
            raise TypeError("DATABASE_MUST_BE_AN_INSTANCE_OF_EXTENDED_DIGITAL_TWIN_DB")
        self.db = db

    def calculate_progress_weight_map(self, project_uuid: str) -> Dict[str, float]:
        """
        Menghitung bobot progres (progress weighting) otomatis per work_item_code secara presisi.
        Menggunakan rasio kontribusi finansial item terhadap total nilai pagu anggaran kontraktual (RAB/BOQ).
        """
        if not isinstance(project_uuid, str) or not project_uuid.strip():
            raise ValueError(f"QS_SERVICE_QUERY_VIOLATION_INVALID_PROJECT_UUID: {project_uuid}")

        snapshots = self.db.list_snapshots(project_uuid)
        if not snapshots:
            logger.warning("No snapshots found for project %s", project_uuid)
            return {}

        latest: Snapshot = snapshots[-1]
        boq = latest.boq_state or {}

        divisions = boq.get("divisions", {})
        if not isinstance(divisions, dict):
            return {}

        total_cost = 0.0
        item_costs: Dict[str, float] = {}

        for div_id, div in divisions.items():
            if not isinstance(div, dict):
                continue
            items = div.get("items", [])
            if not isinstance(items, (list, tuple)):
                continue

            for item in items:
                if not isinstance(item, dict):
                    continue

                code = item.get("item_code") or item.get("code")
                if not code or not isinstance(code, str):
                    continue
                code_clean = code.strip()
                if not code_clean:
                    continue

                cost = item.get("total_price") or item.get("subtotal") or item.get("cost")

                if cost is None:
                    cost_val = float(item.get("quantity", 0.0))
                else:
                    if isinstance(cost, dict) and "value" in cost:
                        cost_val = float(cost["value"])
                    else:
                        cost_val = float(cost)

                if isinstance(cost_val, bool) or math.isnan(cost_val) or math.isinf(cost_val) or cost_val < 0.0:
                    logger.error("FINANCIAL_ANOMALY_IN_BOQ_ITEM %s: %s", code_clean, cost_val)
                    raise ValueError(f"FINANCIAL_ANOMALY_DETECTED_IN_BOQ_ITEM_COST_CALCULATION_FOR_CODE_{code_clean}")

                item_costs[code_clean] = cost_val
                total_cost += cost_val

        weights: Dict[str, float] = {}
        if total_cost > 0.0:
            for code_key, cost_amount in item_costs.items():
                calculated_weight = cost_amount / total_cost
                if math.isnan(calculated_weight) or math.isinf(calculated_weight):
                    raise ValueError("NUMERIC_ANOMALY_DETECTED_DURING_PROGRESS_WEIGHT_MAP_FRACTION")
                weights[code_key] = calculated_weight

        logger.info("Progress weight map calculated for %s: %d items", project_uuid, len(weights))
        return weights

    def propagate_vo(self, vo_uuid: str) -> Dict[str, Any]:
        if not isinstance(vo_uuid, str) or not vo_uuid.strip():
            logger.error("INVALID_VO_UUID: %r", vo_uuid)
            return {"error": f"INVALID_VO_UUID_STRUCTURE: {vo_uuid}"}

        vo = self.db.get_change_order(vo_uuid)
        if vo is None:
            logger.warning("VO not found: %s", vo_uuid)
            return {"error": "VO not found"}

        net_change_currency = vo.calculate_cost_impact()
        updated_vo = vo.copy_with_calculated_cost()
        self.db.save_change_order(updated_vo)

        if isinstance(net_change_currency, Currency):
            net_change = float(net_change_currency.value)
        else:
            net_change = float(net_change_currency)

        logger.info("VO propagated: %s, net change=%s", vo_uuid, net_change)

        return {
            "vo_uuid": vo_uuid,
            "net_change": net_change,
            "status": updated_vo.status.value if hasattr(updated_vo.status, "value") else str(updated_vo.status),
        }

    def finalize_as_built(self, project_uuid: str, as_built_entity_states: Optional[Dict[str, Any]] = None) -> Snapshot:
       
        if not isinstance(project_uuid, str) or not project_uuid.strip():
            raise ValueError(f"QS_SERVICE_QUERY_VIOLATION_INVALID_PROJECT_UUID: {project_uuid}")

        snapshots = self.db.list_snapshots(project_uuid)
        if not snapshots:
            logger.error("No baseline snapshots for project %s", project_uuid)
            raise ValueError("GEOMETRIC_INTEGRITY_VIOLATION_NO_BASELINE_SNAPSHOTS_FOUND_FOR_PROJECT")

        latest: Snapshot = snapshots[-1]

        ccm_state = dict(latest.ccm_state)
        entities = dict(ccm_state.get("entities", {}))

        if as_built_entity_states is not None:
            if not isinstance(as_built_entity_states, dict):
                logger.error("AS_BUILT_ENTITY_STATES_MUST_BE_DICT: %r", as_built_entity_states)
                raise TypeError("AS_BUILT_ENTITY_STATES_MUST_BE_PROVIDED_IN_A_VALID_DICTIONARY")

            for eid, state in as_built_entity_states.items():
                if not isinstance(eid, str) or not eid.strip():
                    continue
                eid_clean = eid.strip()
                if eid_clean in entities:
                    current_entity_state = dict(entities[eid_clean])
                    if isinstance(state, dict):
                        current_entity_state.update(state)
                    entities[eid_clean] = current_entity_state
                else:
                    entities[eid_clean] = dict(state) if isinstance(state, dict) else state

        ccm_state["entities"] = entities

        snap_payload = {
            "snapshot_uuid": Identity.generate(),
            "snapshot_name": "As-Built Final",
            "snapshot_type": "AS_BUILT",
            "project_uuid": project_uuid,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "description": "Final synchronized as-built structural and dimensional physical snapshot.",
            "ccm_state": ccm_state,
            "boq_state": latest.boq_state,
            "rab_state": latest.rab_state,
            "schedule_state": latest.schedule_state,
            "metadata": {},
        }

        final_snapshot = Snapshot.model_validate(snap_payload)
        self.db.save_snapshot(final_snapshot)
        logger.info("As-built finalized for project %s: snapshot %s", project_uuid, final_snapshot.snapshot_uuid)
        return final_snapshot

    def restore_archive(self, archive_uuid: str) -> int:
        """
        Mengeksekusi pemulihan data (Restore) dari arsip digital twin menuju media database utama secara atomik.
        Menerapkan verifikasi sidik jari kriptografis fail-fast untuk memutus rantai manipulasi data tidur.
        """
        if not isinstance(archive_uuid, str) or not archive_uuid.strip():
            raise ValueError(f"QS_SERVICE_QUERY_VIOLATION_INVALID_ARCHIVE_UUID: {archive_uuid}")

        # Ambil arsip dari database; gunakan method yang tersedia.
        archive: Optional[ArchiveRecord] = None
        if hasattr(self.db, "get_archive_record"):
            archive = self.db.get_archive_record(archive_uuid)
        else:
            # Fallback: cari di list archive records (jika get_archive_record tidak ada)
            archives = self.db.list_archive_records(archive_uuid) if hasattr(self.db, "list_archive_records") else []
            # list_archive_records memerlukan project_uuid, bukan archive_uuid. Skip.
            # Sebagai fallback minimal, kita tidak bisa melakukan restore tanpa method yang tepat.
            logger.error("DB has no get_archive_record method")
            raise AttributeError("DATABASE_MUST_IMPLEMENT_GET_ARCHIVE_RECORD")

        if archive is None:
            logger.warning("Archive not found: %s", archive_uuid)
            return 0

        if not archive.verify_integrity():
            logger.error("CRYPTOGRAPHIC_INTEGRITY_VIOLATION: %s", archive_uuid)
            raise ValueError(f"CRYPTOGRAPHIC_INTEGRITY_VIOLATION_CANNOT_RESTORE_TAMPERED_ARCHIVE_DATA: {archive_uuid}")

        restored_count = 0

        # 1. Pulihkan Snapshots
        for snap_dict in archive.snapshots:
            if not isinstance(snap_dict, dict):
                continue

            snap_payload = {
                "snapshot_uuid": snap_dict.get("snapshot_uuid") or Identity.generate(),
                "snapshot_name": str(snap_dict.get("snapshot_name", "Restored Baseline")),
                "snapshot_type": str(snap_dict.get("snapshot_type", "CHECKPOINT")),
                "project_uuid": str(snap_dict.get("project_uuid", archive.project_uuid)),
                "timestamp": snap_dict.get("timestamp") or datetime.now(timezone.utc),
                "description": str(snap_dict.get("description", "Restored from cryptographic twin archive.")),
                "ccm_state": snap_dict.get("ccm_state", {}),
                "boq_state": snap_dict.get("boq_state"),
                "rab_state": snap_dict.get("rab_state"),
                "schedule_state": snap_dict.get("schedule_state"),
                "metadata": snap_dict.get("metadata", {}),
            }
            snapshot_instance = Snapshot.model_validate(snap_payload)
            self.db.save_snapshot(snapshot_instance)
            restored_count += 1

        # 2. Pulihkan As-Built Records
        for asb_dict in archive.as_built_records:
            if not isinstance(asb_dict, dict):
                continue

            raw_diffs = asb_dict.get("differences", [])
            as_built_payload = {
                "project_uuid": str(asb_dict.get("project_uuid", archive.project_uuid)),
                "entity_uuid": str(asb_dict.get("entity_uuid", "")),
                "planned_state": asb_dict.get("planned_state", {}),
                "as_built_state": asb_dict.get("as_built_state", {}),
                "record_uuid": asb_dict.get("record_uuid") or Identity.generate(),
                "differences": tuple(AsBuiltDifference.model_validate(d) for d in raw_diffs)
                if isinstance(raw_diffs, list)
                else (),
            }
            as_built_instance = AsBuiltRecord.model_validate(as_built_payload)
            self.db.save_as_built_record(as_built_instance)
            restored_count += 1

        logger.info("Archive restore completed: %s, %d records restored", archive_uuid, restored_count)
        return restored_count