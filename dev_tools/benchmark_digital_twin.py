"""
Benchmark Digital Twin: 10.000 snapshot dan progress entry.
Gunakan PostgreSQL via env FASTRA_DATABASE_URL untuk hasil realistis.
"""
import os
import sys
import time
import uuid
from datetime import datetime, timezone

# Tambahkan root proyek ke sys.path agar import fastra_core berhasil
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastra_core.digital_twin.database_extended import ExtendedDigitalTwinDB
from fastra_core.digital_twin import Snapshot, ProgressEntry, EntityProgress

DATABASE_URL = os.getenv("FASTRA_DATABASE_URL", "sqlite:///:memory:")

def main():
    db = ExtendedDigitalTwinDB(DATABASE_URL)
    print(f"Database: {DATABASE_URL}")
    start = time.time()
    for i in range(10_000):
        snap = Snapshot(
            snapshot_uuid=str(uuid.uuid4()),
            snapshot_name=f"Benchmark Snapshot {i}",
            snapshot_type="CHECKPOINT",
            project_uuid="bench-project",
            timestamp=datetime.now(timezone.utc).isoformat(),
            ccm_state={"entities": {"wall-001": {"length": i % 100}}},
        )
        db.save_snapshot(snap)
    snapshot_duration = time.time() - start
    print(f"10,000 snapshots: {snapshot_duration:.2f}s ({10000/snapshot_duration:.0f}/s)")

    start = time.time()
    for i in range(10_000):
        entry = ProgressEntry(
            project_uuid="bench-project",
            report_date="2026-08-24",
            report_type="DAILY",
            progress_entry_uuid=str(uuid.uuid4()),
            entity_progress=[
                EntityProgress(
                    entity_uuid="wall-001",
                    entity_name="Dinding",
                    work_item_code="PEK.DIND.001",
                    planned_quantity=100.0,
                    completed_quantity=i % 100,
                    unit="m²",
                )
            ],
        )
        db.save_progress_entry(entry)
    progress_duration = time.time() - start
    print(f"10,000 progress entries: {progress_duration:.2f}s ({10000/progress_duration:.0f}/s)")
    db.close()

if __name__ == "__main__":
    main()
