# fastra_core\units\exceptions.py

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastra_core.errors.exceptions import CESError

logger = logging.getLogger("fastra_core.units.exceptions")


class UnitError(CESError):
    """
    Base structural exception class for all dimension and unit measurement anomalies.
    Aligns directly with the central system exception blueprint.
    """
    DEFAULT_CODE: str = "UNIT-001"


class UnitMismatchError(UnitError):
    """
    Raised when an algebraic or dimensional check fails due to unit incompatibility
    across cross-primitive boundary calculations (e.g., trying to add Length to Mass).
    """
    DEFAULT_CODE: str = "UNIT-MISMATCH-002"

    def __init__(
        self,
        unit1: str,
        unit2: str,
        operation: str = "",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not isinstance(unit1, str) or not isinstance(unit2, str):
            logger.error(
                "UnitMismatchError initialization failed due to invalid token types: %r, %r",
                unit1,
                unit2,
            )
            raise TypeError("UNIT_TOKEN_PARAMETERS_MUST_BE_PURE_STRINGS")

        clean_u1 = unit1.strip()
        clean_u2 = unit2.strip()
        if not clean_u1 or not clean_u2:
            logger.error("UnitMismatchError received empty unit token: %r, %r", unit1, unit2)
            raise ValueError("UNIT_TOKENS_CANNOT_BE_EMPTY_OR_WHITESPACE")

        clean_op = str(operation).strip() if operation else ""
        if clean_op and (not isinstance(operation, str)):
            logger.error("Operation token must be string or empty: %r", operation)
            raise TypeError("OPERATION_TOKEN_MUST_BE_A_PURE_STRING")

        message_str = f"Satuan tidak kompatibel: '{clean_u1}' dan '{clean_u2}'"
        if clean_op:
            message_str += f" dalam operasi '{clean_op}'"

        extended_details = details or {}
        if not isinstance(extended_details, dict):
            logger.error("Details must be a dictionary: %r", details)
            raise TypeError("DETAILS_PARAMETER_MUST_BE_A_DICTIONARY")

        extended_details.update({
            "unit_alpha": clean_u1,
            "unit_beta": clean_u2,
            "attempted_operation": clean_op if clean_op else None,
        })

        super().__init__(
            message=message_str,
            code=self.__class__.DEFAULT_CODE,
            details=extended_details,
        )


class MissingUnitError(UnitError):
    """
    Raised when an atomic primitive math operation or persistence hydrator
    detects a completely null or empty unit token assignment.
    """
    DEFAULT_CODE: str = "UNIT-MISSING-003"


class ConversionError(UnitError):
    """
    Raised when a physical layout converter engine fails to calculate
    ratios across incompatible measurement systems.
    """
    DEFAULT_CODE: str = "UNIT-CONVERSION-004"

    def __init__(
        self,
        from_unit: str,
        to_unit: str,
        rationale: str = "",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not isinstance(from_unit, str) or not isinstance(to_unit, str):
            logger.error(
                "ConversionError initialization failed due to non-string parameters: %r, %r",
                from_unit,
                to_unit,
            )
            raise TypeError("CONVERSION_UNIT_TOKENS_MUST_BE_PURE_STRINGS")

        clean_from = from_unit.strip()
        clean_to = to_unit.strip()
        if not clean_from or not clean_to:
            logger.error("ConversionError received empty unit token: %r, %r", from_unit, to_unit)
            raise ValueError("CONVERSION_UNIT_TOKENS_CANNOT_BE_EMPTY_OR_WHITESPACE")

        clean_rationale = str(rationale).strip() if rationale else "Konversi tidak valid"
        if rationale and not isinstance(rationale, str):
            logger.error("Rationale must be string or empty: %r", rationale)
            raise TypeError("RATIONALES_PARAMETER_MUST_BE_A_PURE_STRING")

        message_str = f"Gagal mengonversi '{clean_from}' ke '{clean_to}': {clean_rationale}"

        extended_details = details or {}
        if not isinstance(extended_details, dict):
            logger.error("Details must be a dictionary: %r", details)
            raise TypeError("DETAILS_PARAMETER_MUST_BE_A_DICTIONARY")

        extended_details.update({
            "source_unit": clean_from,
            "target_unit": clean_to,
            "failure_rationale": clean_rationale,
        })

        super().__init__(
            message=message_str,
            code=self.__class__.DEFAULT_CODE,
            details=extended_details,
        )