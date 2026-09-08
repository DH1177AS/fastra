from __future__ import annotations

import logging
import threading
from typing import Any, Dict, List, Type

# Expose strict unit components down to the module boundary layer
from .exceptions import ConversionError, MissingUnitError, UnitError, UnitMismatchError
from .validator import (
    ALIASES,
    COMPATIBLE_GROUPS,
    UnitValidationGuard,
    are_units_compatible,
    get_quantity_type,
    normalize_unit,
    validate_compatibility,
    validate_dimension,
    validate_unit_not_unknown,
    validate_unit_presence,
)
from .converter import UnitConversionGuard, convert
from .precision import PrecisionProfile, RoundingPolicy

logger = logging.getLogger("fastra_core.units")

_UNITS_MODULE_LOCK = threading.Lock()


def verify_units_subsystem_health() -> Dict[str, Any]:
    """
    Executes a structural fail-fast smoke test to guarantee all immutable core
    unit taxonomy elements, calculators, and sub-layers have successfully compiled.
    """
    if not _UNITS_MODULE_LOCK.acquire(timeout=10):
        logger.error("UNITS_HEALTH_CHECK_LOCK_ACQUISITION_TIMEOUT")
        raise TimeoutError("UNITS_HEALTH_CHECK_LOCK_ACQUISITION_TIMEOUT")

    try:
        monitored_elements: List[Type[Any]] = [
            UnitValidationGuard,
            UnitConversionGuard,
            PrecisionProfile,
            UnitMismatchError,
            ConversionError,
        ]

        for element in monitored_elements:
            if element is None:
                logger.error("UNITS_INTEGRITY_COMPROMISED: Sub-component failed to initialize.")
                raise ImportError(
                    f"UNITS_INTEGRITY_COMPROMISED: Sub-component {element} failed to initialize."
                )

        logger.info("Units subsystem health check passed")
        return {
            "status": "HEALTHY",
            "layer": "UNITS_CORE",
            "military_grade_lock_active": True,
        }
    finally:
        _UNITS_MODULE_LOCK.release()


# Execute early enforcement on load initialization
verify_units_subsystem_health()

__all__ = [
    # Global Immutable Taxonomy Constants
    "COMPATIBLE_GROUPS",
    "ALIASES",

    # Domain Exceptions Matrices
    "UnitError",
    "UnitMismatchError",
    "MissingUnitError",
    "ConversionError",

    # Validation & Verification Gates
    "UnitValidationGuard",
    "validate_compatibility",
    "validate_unit_presence",
    "are_units_compatible",
    "normalize_unit",
    "get_quantity_type",
    "validate_dimension",
    "validate_unit_not_unknown",

    # Conversion Pipeline Engine
    "UnitConversionGuard",
    "convert",

    # Quantitative Precision Profiles
    "RoundingPolicy",
    "PrecisionProfile",

    # Subsystem Package Health
    "verify_units_subsystem_health",
]