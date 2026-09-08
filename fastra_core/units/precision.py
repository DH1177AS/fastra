# fastra_core\units\precision.py

from __future__ import annotations

import logging
import math
from decimal import (
    Decimal,
    ROUND_HALF_EVEN,
    ROUND_UP,
    ROUND_DOWN,
    ROUND_FLOOR,
    InvalidOperation,
)
from enum import Enum
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra_core.units.precision")


class RoundingPolicy(str, Enum):
    """
    Taksonomi kebijakan pembulatan formal (Rounding Policy) arsitektur penalas.
    Mengekspos metode pemetaan murni ke konstanta mode standard `decimal` Python.
    """
    BANKER = "banker"
    UP = "up"
    DOWN = "down"
    TRUNCATE = "truncate"

    def get_decimal_mode(self) -> str:
        """
        Memetakan tipe Enum taksonomi langsung menuju bendera internal modul decimal murni.
        """
        return {
            RoundingPolicy.BANKER: ROUND_HALF_EVEN,
            RoundingPolicy.UP: ROUND_UP,
            RoundingPolicy.DOWN: ROUND_DOWN,
            RoundingPolicy.TRUNCATE: ROUND_FLOOR,
        }[self]


class PrecisionProfile(BaseModel):
    """
    Primitive Value Object untuk mengonfigurasi profil akurasi desimal (Precision Profile).
    Mengunci angka penting (significant digits) dan jumlah digit desimal tetap secara kaku.
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    significant_digits: int = Field(
        default=6,
        ge=1,
        le=16,
        description="Batas atas jumlah angka penting total",
    )
    decimal_places: int = Field(
        default=2,
        ge=0,
        le=9,
        description="Jumlah digit pasca tanda desimal (koma)",
    )
    policy: RoundingPolicy = Field(
        default=RoundingPolicy.BANKER,
        description="Aturan pembulatan formal",
    )

    @field_validator("significant_digits", "decimal_places", mode="before")
    @classmethod
    def validate_integers_no_coercion(cls, value: Any) -> int:
        if isinstance(value, bool):
            logger.error("PRECISION_METRIC_BOOLEAN_REJECTED: %r", value)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(value, int):
            logger.error("PRECISION_METRIC_NON_INTEGER_REJECTED: %r", value)
            raise TypeError("PRECISION_METRIC_MUST_BE_A_PURE_INTEGER")
        if value < 0:
            logger.error("PRECISION_METRIC_NEGATIVE_REJECTED: %s", value)
            raise ValueError("PRECISION_METRIC_MUST_BE_NON_NEGATIVE")
        return value

    def round_decimal(self, value: Any) -> Decimal:
        """
        Mengeksekusi pembulatan kuantisasi nilai secara mutlak dan deterministik hulu-ke-hilir.
        Menghilangkan total galat biner floating-point (*binary truncation inaccuracies*).
        """
        if isinstance(value, bool):
            logger.error("ROUND_DECIMAL_BOOLEAN_REJECTED: %r", value)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED_IN_ROUNDING")

        if isinstance(value, float):
            # Melarang keras akomodasi tipe float mentah tanpa deteksi anomali
            if math.isnan(value) or math.isinf(value):
                logger.error("ROUND_DECIMAL_NAN_OR_INF_REJECTED: %s", value)
                raise ValueError("NUMERIC_ANOMALY_DETECTED_CANNOT_ROUND_NAN_OR_INFINITE_VALUE")
            # Konversi float murni via perantara representasi string untuk menghentikan bleeding presisi
            decimal_source = Decimal(str(value))
        elif isinstance(value, (int, str, Decimal)):
            try:
                decimal_source = Decimal(str(value))
            except (InvalidOperation, ValueError) as exc:
                logger.error("INVALID_FINANCIAL_OR_SPATIAL_DECIMAL_REPRESENTATION: %r", value)
                raise ValueError(f"INVALID_FINANCIAL_OR_SPATIAL_DECIMAL_REPRESENTATION: {value}") from exc
        else:
            logger.error("ROUND_DECIMAL_UNSUPPORTED_TYPE: %r", type(value).__name__)
            raise TypeError("VALUE_MUST_BE_INT_STR_FLOAT_OR_DECIMAL")

        if decimal_source.is_nan() or decimal_source.is_infinite():
            logger.error("DECIMAL_NAN_OR_INF_REJECTED: %s", decimal_source)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_DECIMAL_CANNOT_BE_NAN_OR_INFINITE")

        # Membuat eksponen kuantisasi berbasis jumlah desimal target secara dinamis
        quantize_exponent = Decimal("1") / (Decimal("10") ** self.decimal_places)
        rounding_mode = self.policy.get_decimal_mode()

        try:
            result = decimal_source.quantize(quantize_exponent, rounding=rounding_mode)
            logger.debug(
                "Decimal rounding: input=%s, places=%s, mode=%s, output=%s",
                decimal_source,
                self.decimal_places,
                rounding_mode,
                result,
            )
            return result
        except (InvalidOperation, ValueError) as quantize_err:
            logger.error("QUANTIZATION_EXECUTION_FAILED_CHECK_BOUNDARIES: %s", quantize_err)
            raise ValueError(f"QUANTIZATION_EXECUTION_FAILED_CHECK_BOUNDARIES: {str(quantize_err)}") from quantize_err