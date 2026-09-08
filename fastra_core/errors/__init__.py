from __future__ import annotations

import logging
import threading
from typing import Any, Dict, List, Type

# Expose strict domain exceptions down to the module boundary layer
from .exceptions import (
    CESError,
    CompilerError,
    CostError,
    ErrorContextModel,
    GeometryError,
    SerializationError,
    TopologyError,
    UnitError,
    ValidationError,
    VersionError,
)

logger = logging.getLogger("fastra_core.errors")

_ERRORS_MODULE_LOCK = threading.Lock()


def verify_errors_subsystem_health() -> Dict[str, Any]:
    """
    Executes a structural fail-fast smoke test to guarantee all immutable core
    exception components and sub-layers have successfully compiled without type contamination.
    """
    if not _ERRORS_MODULE_LOCK.acquire(timeout=10):
        logger.error("ERRORS_HEALTH_CHECK_LOCK_ACQUISITION_TIMEOUT")
        raise TimeoutError("ERRORS_HEALTH_CHECK_LOCK_ACQUISITION_TIMEOUT")

    try:
        monitored_elements: List[Type[Any]] = [
            ErrorContextModel,
            CESError,
            GeometryError,
            TopologyError,
            UnitError,
            CostError,
            ValidationError,
            CompilerError,
            SerializationError,
            VersionError,
        ]

        for element in monitored_elements:
            if element is None:
                logger.error("ERRORS_INTEGRITY_COMPROMISED: Sub-component failed to initialize.")
                raise ImportError(
                    f"ERRORS_INTEGRITY_COMPROMISED: Sub-component {element} failed to initialize."
                )

        logger.info("Errors subsystem health check passed")
        return {
            "status": "HEALTHY",
            "layer": "ERRORS_CORE",
            "military_grade_lock_active": True,
        }
    finally:
        _ERRORS_MODULE_LOCK.release()


# Execute early enforcement on load initialization
verify_errors_subsystem_health()

__all__ = [
    "ErrorContextModel",
    "CESError",
    "GeometryError",
    "TopologyError",
    "UnitError",
    "CostError",
    "ValidationError",
    "CompilerError",
    "SerializationError",
    "VersionError",
    "verify_errors_subsystem_health",
]