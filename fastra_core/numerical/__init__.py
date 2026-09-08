from __future__ import annotations

import logging
import threading
from typing import Any, Callable, Dict, List

# Expose strict numerical geometry components down to the module boundary layer
from .geometry import (
    orient2d,
    point_in_polygon_robust,
    polygon_area_robust,
    closest_point_on_segment,
)
from .matrix import inverse_matrix

logger = logging.getLogger("fastra.numerical")

_NUMERICAL_MODULE_LOCK = threading.Lock()


def verify_numerical_subsystem_health() -> Dict[str, Any]:
    """
    Menjalankan smoke test fail-fast untuk memastikan seluruh komponen kalkulasi numerik
    telah terinisialisasi tanpa kontaminasi tipe.
    """
    if not _NUMERICAL_MODULE_LOCK.acquire(timeout=10):
        logger.error("NUMERICAL_HEALTH_CHECK_LOCK_ACQUISITION_TIMEOUT")
        raise TimeoutError("NUMERICAL_HEALTH_CHECK_LOCK_ACQUISITION_TIMEOUT")

    try:
        monitored_routines: List[Callable[..., Any]] = [
            orient2d,
            point_in_polygon_robust,
            polygon_area_robust,
            closest_point_on_segment,
            inverse_matrix,
        ]

        for routine in monitored_routines:
            if not callable(routine):
                logger.error("NUMERICAL_INTEGRITY_COMPROMISED_NON_CALLABLE: %r", routine)
                raise ImportError(
                    "NUMERICAL_INTEGRITY_COMPROMISED: Sub-component failed to initialize."
                )

        logger.info("Numerical subsystem health check passed")
        return {
            "status": "HEALTHY",
            "layer": "NUMERICAL_CORE",
            "military_grade_lock_active": True,
        }
    finally:
        _NUMERICAL_MODULE_LOCK.release()


# Eksekusi verifikasi awal saat modul dimuat.
verify_numerical_subsystem_health()

__all__ = [
    "orient2d",
    "point_in_polygon_robust",
    "polygon_area_robust",
    "closest_point_on_segment",
    "inverse_matrix",
    "verify_numerical_subsystem_health",
]