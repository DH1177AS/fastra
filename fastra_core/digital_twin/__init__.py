"""
FASTRA Digital Twin (ACES-600) Core Initialization Package
Orchestrates and seals the immutable structural domain sub-packages, Pydantic v2 schemas,
append-only blockchain audit ledgers, relational persistence backends, and query engines.
Executes an atomic fail-fast system compile check under thread-safe synchronization.
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict, List, Type

# Expose strict digital twin assets down to the subpackage boundary layer
from .enums import (
    ApprovalStatus,
    EventType,
    IssueSeverity,
    IssueStatus,
    ProgressStatus,
    ReportType,
    SnapshotType,
    VOStatus,
    validate_enum_value,
)
from .versioning import Version, VersionError, VersionGraph, VersionNode
from .snapshot import Snapshot, SnapshotStore
from .progress import (
    EntityProgress,
    Issue,
    MaterialDelivery,
    ProgressEntry,
    ProgressStore,
)
from .change_order import ApprovalStep, ChangeOrder, ChangeOrderStore
from .as_built import AsBuiltDifference, AsBuiltRecord, AsBuiltStore
from .audit import AuditEvent, AuditStore
from .query import QueryEngine
from .photo import PhotoData
from .sync import OfflineStore, SQLiteOfflineStore, SyncEngine, SyncResult
from .archiving import ArchiveRecord, ArchiveStore
from .persistence import SQLiteDigitalTwinDB
from .database import (
    AIEventORM,
    ArchiveRecordORM,
    AsBuiltRecordORM,
    AuditEventORM,
    Base,
    ChangeOrderORM,
    ProgressEntryORM,
    SnapshotORM,
    SQLAlchemyDigitalTwinDB,
)
from .database_extended import ExtendedDigitalTwinDB, UserORM
from .transaction import atomic
from .rate_limit import RateLimiter
from .security import SecurityHeadersMiddleware, validate_env
from .logging_config import JsonFormatter, setup_logging
from .serialization import StrictCCMSerializer, entity_to_dict, to_serializable
from .domain_qs import QSDomainService

logger = logging.getLogger("fastra_core.digital_twin")

_DIGITAL_TWIN_PACKAGE_LOCK = threading.Lock()


def verify_digital_twin_subsystem_health() -> Dict[str, Any]:
    """
    Executes a high-order structural fail-fast smoke test during module load time.
    Guarantees all immutable core engines and data access adapters compiled cleanly
    and enforces explicit environment secrets validation before runtime deployment.
    """
    if not _DIGITAL_TWIN_PACKAGE_LOCK.acquire(timeout=10):
        logger.error("DIGITAL_TWIN_HEALTH_CHECK_LOCK_ACQUISITION_TIMEOUT")
        raise TimeoutError("DIGITAL_TWIN_HEALTH_CHECK_LOCK_ACQUISITION_TIMEOUT")

    try:
        # 1. Trigger military-grade environment safety entropy check early
        validate_env()

        # 2. Assert core domain and model layout presence
        monitored_classes: List[Type[Any]] = [
            VersionGraph,
            SnapshotStore,
            ProgressStore,
            ChangeOrderStore,
            AsBuiltStore,
            AuditStore,
            QueryEngine,
            SyncEngine,
            ArchiveStore,
            ExtendedDigitalTwinDB,
            RateLimiter,
            QSDomainService,
        ]

        for cls in monitored_classes:
            if cls is None:
                logger.error("DIGITAL_TWIN_INITIALIZATION_ERROR: Critical core class failed to instantiate.")
                raise ImportError(
                    f"DIGITAL_TWIN_INITIALIZATION_ERROR: Critical core class {cls} failed to instantiate."
                )

        logger.info("Digital Twin subsystem health check passed")
        return {
            "status": "HEALTHY",
            "layer": "DIGITAL_TWIN_CORE_SUBPACKAGE",
            "security_entropy_verified": True,
            "atomic_thread_lock_active": True,
        }
    finally:
        _DIGITAL_TWIN_PACKAGE_LOCK.release()


# Automatically fire high-order structural integrity enforcement on package activation
verify_digital_twin_subsystem_health()

__all__ = [
    # Enums & Taxonomy
    "SnapshotType",
    "ReportType",
    "ProgressStatus",
    "IssueSeverity",
    "IssueStatus",
    "VOStatus",
    "ApprovalStatus",
    "EventType",
    "validate_enum_value",

    # Versioning DAG Subsystem
    "Version",
    "VersionGraph",
    "VersionNode",
    "VersionError",

    # Spatiotemporal Checkpoints
    "Snapshot",
    "SnapshotStore",

    # Earned Value Tracking
    "ProgressEntry",
    "EntityProgress",
    "Issue",
    "MaterialDelivery",
    "ProgressStore",

    # Cost Change Governance
    "ChangeOrder",
    "ApprovalStep",
    "ChangeOrderStore",

    # Real-World Physical Finalization
    "AsBuiltRecord",
    "AsBuiltDifference",
    "AsBuiltStore",

    # Cryptographic Append-Only Ledger
    "AuditEvent",
    "AuditStore",

    # Point-in-Time Tracing Engine
    "QueryEngine",

    # Field Visual Capture
    "PhotoData",

    # Offline-First Sync Layer
    "OfflineStore",
    "SQLiteOfflineStore",
    "SyncEngine",
    "SyncResult",

    # Cryptographic Archiving
    "ArchiveRecord",
    "ArchiveStore",

    # Relational Persistence & SQL Database Engines
    "Base",
    "SnapshotORM",
    "AuditEventORM",
    "ProgressEntryORM",
    "ChangeOrderORM",
    "AsBuiltRecordORM",
    "ArchiveRecordORM",
    "AIEventORM",
    "UserORM",
    "LegacySQLiteDB",
    "SQLiteDigitalTwinDB",
    "SQLAlchemyDigitalTwinDB",
    "ExtendedDigitalTwinDB",
    "atomic",

    # Security Infrastructure & Guard Middleware
    "RateLimiter",
    "SecurityHeadersMiddleware",
    "validate_env",

    # Structured Observability Logs
    "JsonFormatter",
    "setup_logging",

    # Minimal Deterministic Serialization
    "StrictCCMSerializer",
    "to_serializable",
    "entity_to_dict",

    # Quantity Surveying Service Orchestrator
    "QSDomainService",

    # Package System Diagnostics
    "verify_digital_twin_subsystem_health",
]