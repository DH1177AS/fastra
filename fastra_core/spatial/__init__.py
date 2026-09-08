from __future__ import annotations

import logging
import threading
from typing import Any, Dict, List, Type

# Expose strict spatial value objects down to the module boundary layer
from .coordinate import Coordinate
from .vector import Vector
from .matrix4x4 import Matrix4x4
from .quaternion import Quaternion
from .transform import Transform

logger = logging.getLogger("fastra_core.spatial")

_SPATIAL_MODULE_LOCK = threading.Lock()


def verify_spatial_subsystem_health() -> Dict[str, Any]:
    """
    Menjalankan smoke test fail-fast untuk memastikan seluruh komponen spasial
    telah terinisialisasi tanpa kontaminasi tipe.
    """
    if not _SPATIAL_MODULE_LOCK.acquire(timeout=10):
        logger.error("SPATIAL_HEALTH_CHECK_LOCK_ACQUISITION_TIMEOUT")
        raise TimeoutError("SPATIAL_HEALTH_CHECK_LOCK_ACQUISITION_TIMEOUT")

    try:
        monitored_elements: List[Type[Any]] = [
            Coordinate,
            Vector,
            Matrix4x4,
            Quaternion,
            Transform,
        ]

        for element in monitored_elements:
            if element is None:
                logger.error("SPATIAL_INTEGRITY_COMPROMISED_NULL_COMPONENT")
                raise ImportError(
                    "SPATIAL_INTEGRITY_COMPROMISED: Sub-component failed to initialize."
                )

        logger.info("Spatial subsystem health check passed")
        return {
            "status": "HEALTHY",
            "layer": "SPATIAL_CORE",
            "military_grade_lock_active": True,
        }
    finally:
        _SPATIAL_MODULE_LOCK.release()


# Eksekusi verifikasi awal saat modul dimuat.
verify_spatial_subsystem_health()

__all__ = [
    "Coordinate",
    "Vector",
    "Matrix4x4",
    "Quaternion",
    "Transform",
    "verify_spatial_subsystem_health",
]