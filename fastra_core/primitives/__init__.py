from __future__ import annotations

import logging
import threading
from typing import Any, Dict, List, Type

# Expose strict primitive value objects down to the module boundary layer
from .length import Length, LengthUnit
from .area import Area, AreaUnit
from .volume import Volume, VolumeUnit
from .mass import Mass, MassUnit
from .angle import Angle, AngleUnit
from .time import Time, TimeUnit
from .currency import Currency, CurrencyUnit
from .temperature import Temperature, TemperatureUnit
from .density import Density, DensityUnit

logger = logging.getLogger("fastra.primitives")

_PRIMITIVES_MODULE_LOCK = threading.Lock()


def verify_primitives_subsystem_health() -> Dict[str, Any]:
    """
    Menjalankan smoke test fail-fast untuk memastikan seluruh komponen primitif
    telah terinisialisasi tanpa kontaminasi tipe.
    """
    if not _PRIMITIVES_MODULE_LOCK.acquire(timeout=10):
        logger.error("PRIMITIVES_HEALTH_CHECK_LOCK_ACQUISITION_TIMEOUT")
        raise TimeoutError("PRIMITIVES_HEALTH_CHECK_LOCK_ACQUISITION_TIMEOUT")

    try:
        monitored_elements: List[Type[Any]] = [
            Length,
            Area,
            Volume,
            Mass,
            Angle,
            Time,
            Currency,
            Temperature,
            Density,
        ]

        for element in monitored_elements:
            if element is None:
                logger.error("PRIMITIVES_INTEGRITY_COMPROMISED_NULL_COMPONENT")
                raise ImportError(
                    "PRIMITIVES_INTEGRITY_COMPROMISED: Sub-component failed to initialize."
                )

        logger.info("Primitives subsystem health check passed")
        return {
            "status": "HEALTHY",
            "layer": "PRIMITIVES_CORE",
            "military_grade_lock_active": True,
        }
    finally:
        _PRIMITIVES_MODULE_LOCK.release()


# Eksekusi verifikasi awal saat modul dimuat.
verify_primitives_subsystem_health()

__all__ = [
    "Length",
    "LengthUnit",
    "Area",
    "AreaUnit",
    "Volume",
    "VolumeUnit",
    "Mass",
    "MassUnit",
    "Angle",
    "AngleUnit",
    "Time",
    "TimeUnit",
    "Currency",
    "CurrencyUnit",
    "Temperature",
    "TemperatureUnit",
    "Density",
    "DensityUnit",
    "verify_primitives_subsystem_health",
]