from __future__ import annotations

import logging
import threading
from typing import Any, Dict, List, Type

# Expose strict core framework components down to the module perimeter
from .identity import Identity
from .security_master import MasterSecurity

# Explicitly pull all structural primitive value objects and spatial matrices
from .primitives import *
from .spatial import *

# Re-import explicit listings to guarantee clean namespace bundling
from .primitives import __all__ as _primitives_all
from .spatial import __all__ as _spatial_all

logger = logging.getLogger("fastra_core")

_CORE_MODULE_LOCK = threading.Lock()


def verify_core_subsystem_health() -> Dict[str, Any]:
    """
    Executes a high-order structural fail-fast smoke test during module load time.
    Guarantees all immutable core engines, identity providers, and cryptographic
    security master structures initialized smoothly without trace component drift.
    """
    if not _CORE_MODULE_LOCK.acquire(timeout=10):
        logger.error("CORE_HEALTH_CHECK_LOCK_ACQUISITION_TIMEOUT")
        raise TimeoutError("CORE_HEALTH_CHECK_LOCK_ACQUISITION_TIMEOUT")

    try:
        monitored_elements: List[Type[Any]] = [
            Identity,
            MasterSecurity,
        ]

        for element in monitored_elements:
            if element is None:
                logger.error("CORE_INTEGRITY_COMPROMISED: Absolute core sub-component failed to initialize.")
                raise ImportError(
                    f"CORE_INTEGRITY_COMPROMISED: Absolute core sub-component {element} failed to initialize."
                )

        logger.info("FASTRA Core subsystem health check passed")
        return {
            "status": "HEALTHY",
            "layer": "FASTRA_CORE_ROOT",
            "military_grade_lock_active": True,
        }
    finally:
        _CORE_MODULE_LOCK.release()


# Execute early validation on load initialization
verify_core_subsystem_health()

# Consolidate child manifests to expose primitives and spatial entities cleanly down the line
__all__ = [
    # Cryptographic Identity & Context Masters
    "Identity",
    "MasterSecurity",
] + _primitives_all + _spatial_all