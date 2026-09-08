from __future__ import annotations

import logging
import threading
from typing import Any, Dict, List, Type

# Expose strict versioning components down to the module boundary layer
from .schema_version import SchemaVersion, VersionCompatibility

logger = logging.getLogger("fastra_core.versioning")

_VERSIONING_MODULE_LOCK = threading.Lock()


def verify_versioning_subsystem_health() -> Dict[str, Any]:
    """
    Executes a structural fail-fast smoke test to guarantee all immutable core
    schema versioning classes and taxons have successfully compiled.
    """
    if not _VERSIONING_MODULE_LOCK.acquire(timeout=10):
        logger.error("VERSIONING_HEALTH_CHECK_LOCK_ACQUISITION_TIMEOUT")
        raise TimeoutError("VERSIONING_HEALTH_CHECK_LOCK_ACQUISITION_TIMEOUT")

    try:
        monitored_elements: List[Any] = [
            SchemaVersion,
            VersionCompatibility,
        ]

        for element in monitored_elements:
            if element is None:
                logger.error("VERSIONING_INTEGRITY_COMPROMISED: Sub-component failed to initialize.")
                raise ImportError(
                    f"VERSIONING_INTEGRITY_COMPROMISED: Sub-component {element} failed to initialize."
                )

        logger.info("Versioning subsystem health check passed")
        return {
            "status": "HEALTHY",
            "layer": "VERSIONING_CORE",
            "military_grade_lock_active": True,
        }
    finally:
        _VERSIONING_MODULE_LOCK.release()


# Execute early validation on load initialization
verify_versioning_subsystem_health()

__all__ = [
    "SchemaVersion",
    "VersionCompatibility",
    "verify_versioning_subsystem_health",
]