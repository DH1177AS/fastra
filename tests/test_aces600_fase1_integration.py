"""
ACES-600 Fase 1 - Integrasi Snapshot ke Pipeline
Menguji method _capture_snapshot pada QuantityCompilerPipeline.
"""
import pytest
from unittest.mock import MagicMock
from fastra_core.compiler.compiler_pipeline import QuantityCompilerPipeline
from fastra_core.digital_twin import SnapshotStore


class TestPipelineSnapshot:
    def test_capture_snapshot_creates_snapshot(self):
        # Setup pipeline dengan kg dummy
        kg = MagicMock()
        pipeline = QuantityCompilerPipeline(kg, generated_at="2026-08-24T10:00:00Z")
        store = SnapshotStore()

        # Data entities palsu (dict biasa)
        entities = {
            "wall-001": {"id": "wall-001", "name": "Dinding Kamar", "length": 5.0},
            "column-001": {"id": "column-001", "name": "Kolom K1", "width": 0.3},
        }
        graph = {"relationships": [("wall-001", "column-001")]}
        boq = {"divisions": {"DIV-1": {"items": []}}, "total": 0.0}

        snapshot_uuid = pipeline._capture_snapshot(
            snapshot_store=store,
            snapshot_name="Integrasi Test",
            snapshot_type="CHECKPOINT",
            project_uuid="proj-test-001",
            entities=entities,
            graph=graph,
            boq=boq
        )

        assert snapshot_uuid is not None
        snap = store.get_snapshot(snapshot_uuid)
        assert snap is not None
        assert snap.snapshot_name == "Integrasi Test"
        assert snap.ccm_state["entities"]["wall-001"]["length"] == 5.0
        assert snap.ccm_state["entities"]["column-001"]["width"] == 0.3
        assert snap.boq_state == boq

    def test_capture_snapshot_uses_generated_at_timestamp(self):
        kg = MagicMock()
        pipeline = QuantityCompilerPipeline(kg, generated_at="2026-08-24T10:00:00Z")
        store = SnapshotStore()
        entities = {"wall-001": {"id": "wall-001", "length": 5.0}}
        graph = {}
        boq = {}

        snap_uuid = pipeline._capture_snapshot(
            snapshot_store=store,
            snapshot_name="Timestamp Test",
            snapshot_type="CHECKPOINT",
            project_uuid="proj-test-002",
            entities=entities,
            graph=graph,
            boq=boq
        )
        snap = store.get_snapshot(snap_uuid)
        assert snap.timestamp == "2026-08-24T10:00:00Z"
