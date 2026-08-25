"""
Compliance tests untuk ACES-600 Fase 2:
ACTS-600-006, 007, 008, 009, 010
"""
import pytest
from fastra_core.digital_twin import (
    ProgressEntry, EntityProgress, ProgressStore,
    ChangeOrder, ChangeOrderStore,
    AsBuiltRecord, AsBuiltStore,
)


# ACTS-600-006: Progress: perhitungan persentase benar
def test_progress_percentage_calculation():
    entry = ProgressEntry(
        project_uuid="proj-001",
        report_date="2026-08-15",
        report_type="WEEKLY",
        entity_progress=[
            EntityProgress(entity_uuid="wall-001", entity_name="Dinding Kamar", work_item_code="PEK.DIND.001",
                           planned_quantity=100.0, completed_quantity=60.0, unit="m²"),
            EntityProgress(entity_uuid="col-001", entity_name="Kolom K1", work_item_code="PEK.STR.003",
                           planned_quantity=10.0, completed_quantity=10.0, unit="m³"),
        ],
    )
    store = ProgressStore()
    # bobot: PEK.DIND.001=0.7, PEK.STR.003=0.3
    overall = store.calculate_overall_progress(entry, weight_map={"PEK.DIND.001": 0.7, "PEK.STR.003": 0.3})
    # (60*0.7 + 10*0.3) / (100*0.7 + 10*0.3) = (42+3)/(70+3) = 45/73 = 61.64
    assert overall == 61.64


# ACTS-600-007: Progress: planned vs actual comparison
def test_planned_vs_actual():
    store = ProgressStore()
    result = store.planned_vs_actual(
        planned_quantity=150.0,
        actual_quantity=120.0,
        planned_duration=15,
        actual_duration=18,
        planned_cost=20_332_350,
        actual_cost=22_500_000,
    )
    assert result["quantity_variance"] == -30.0
    assert result["duration_variance_days"] == 3
    assert result["cost_variance"] == 2_167_650
    assert result["cost_variance_percentage"] == 10.66
    assert result["status"] == "OVER_BUDGET"
    assert result["schedule_status"] == "BEHIND_SCHEDULE"


# ACTS-600-008: VO: dampak biaya terhitung
def test_vo_cost_impact():
    vo = ChangeOrder(
        project_uuid="proj-001",
        vo_number="VO-003",
        description="Penambahan kanopi carport",
        reason="Permintaan owner",
        request_date="2026-09-01",
        requested_by="Owner",
        cost_impact={"additional_cost": 18_500_000.0, "deduction_cost": 0.0},
    )
    net = vo.calculate_cost_impact()
    assert net == 18_500_000.0
    assert vo.cost_impact["net_change"] == 18_500_000.0


# ACTS-600-009: VO: approval chain tercatat
def test_vo_approval_chain():
    store = ChangeOrderStore()
    vo = ChangeOrder(
        project_uuid="proj-001",
        vo_number="VO-004",
        description="Penambahan railing balkon",
        reason="Keamanan",
        request_date="2026-09-02",
        requested_by="MK",
    )
    store.add_vo(vo)
    assert store.add_approval(vo.vo_uuid, "Kontraktor", "Budi", "2026-09-03", "APPROVED")
    assert store.add_approval(vo.vo_uuid, "Konsultan MK", "Ani", "2026-09-04", "APPROVED")
    assert store.add_approval(vo.vo_uuid, "Owner", "Joko", "2026-09-05", "APPROVED")
    retrieved = store.get_vo(vo.vo_uuid)
    assert retrieved is not None
    assert len(retrieved.approval_chain) == 3
    assert retrieved.approval_chain[0].role == "Kontraktor"


# ACTS-600-010: As-Built: perbedaan terdeteksi
def test_as_built_difference_detection():
    store = AsBuiltStore()
    record = AsBuiltRecord(
        project_uuid="proj-001",
        entity_uuid="wall-007",
        planned_state={"length": 5.0, "material": "Bata Merah"},
        as_built_state={"length": 5.1, "material": "Bata Merah"},
    )
    store.add_record(record)
    retrieved = store.get_record(record.record_uuid)
    assert retrieved is not None
    assert len(retrieved.differences) == 1
    diff = retrieved.differences[0]
    assert diff.field == "length"
    assert diff.planned_value == 5.0
    assert diff.as_built_value == 5.1
