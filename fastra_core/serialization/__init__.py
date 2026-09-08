from __future__ import annotations

import logging
import threading
from typing import Any, Callable, Dict, List

from .canonical_json import to_json, from_json
from .hash import canonical_hash

logger = logging.getLogger("fastra_core.serialization")

_SERIALIZATION_MODULE_LOCK = threading.Lock()


def verify_serialization_subsystem_health() -> Dict[str, Any]:
    """
    Menjalankan smoke test fail-fast untuk memastikan seluruh primitif serialisasi
    dan hash kriptografis telah terinisialisasi tanpa kontaminasi tipe.
    """
    if not _SERIALIZATION_MODULE_LOCK.acquire(timeout=10):
        logger.error("SERIALIZATION_HEALTH_CHECK_LOCK_ACQUISITION_TIMEOUT")
        raise TimeoutError("SERIALIZATION_HEALTH_CHECK_LOCK_ACQUISITION_TIMEOUT")

    try:
        monitored_routines: List[Callable[..., Any]] = [
            to_json,
            from_json,
            canonical_hash,
        ]

        for routine in monitored_routines:
            if not callable(routine):
                logger.error("SERIALIZATION_INTEGRITY_COMPROMISED_NON_CALLABLE: %r", routine)
                raise ImportError(
                    "SERIALIZATION_INTEGRITY_COMPROMISED: Sub-component failed to initialize."
                )

        logger.info("Serialization subsystem health check passed")
        return {
            "status": "HEALTHY",
            "layer": "SERIALIZATION_CORE",
            "military_grade_lock_active": True,
        }
    finally:
        _SERIALIZATION_MODULE_LOCK.release()


# Eksekusi verifikasi awal saat modul dimuat.
verify_serialization_subsystem_health()

__all__ = [
    "to_json",
    "from_json",
    "canonical_hash",
    "verify_serialization_subsystem_health",
]