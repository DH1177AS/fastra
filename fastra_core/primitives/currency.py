# fastra_core\primitives\currency.py

from __future__ import annotations

import logging
import math
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from enum import Enum
from typing import Any, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra.primitives.currency")


class CurrencyUnit(str, Enum):
    """
    Strict Enum untuk mengunci mata uang sah proyek konstruksi nasional & internasional.
    Menghilangkan manipulasi paksa (coercion hack) tipe string bebas.
    """
    IDR = "IDR"
    USD = "USD"


class Currency(BaseModel):
    """
    Primitive Value Object untuk merepresentasikan Nilai Finansial (Currency).
    Menggunakan Pydantic sebagai validator tunggal dengan mode strict fail-fast.
    Nilai otomatis dibulatkan secara bank (Bankers' Rounding / ROUND_HALF_EVEN) ke presisi 2 desimal.
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    value: Decimal = Field(..., description="Besaran nilai finansial dengan presisi tetap")
    unit: CurrencyUnit = Field(default=CurrencyUnit.IDR, description="Satuan mata uang sah")

    def __init__(self, *args, **kwargs):
        if args:
            if len(args) > 1:
                raise TypeError("Currency only accepts a single positional argument for value")
            kwargs.setdefault("value", args[0])
        super().__init__(**kwargs)

    @field_validator("value", mode="before")
    @classmethod
    def validate_and_quantize_financial_value(cls, value: Any) -> Decimal:
        if isinstance(value, bool):
            logger.error("CURRENCY_VALUE_REJECTED_BOOLEAN: %r", value)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")

        # Melarang keras instansiasi mentah dari tipe float murni demi menghindari precision bleeding
        if isinstance(value, float):
            logger.error("CURRENCY_VALUE_REJECTED_FLOAT: %r", value)
            raise TypeError("DIRECT_FLOAT_INITIALIZATION_FORBIDDEN_USE_STRING_INT_OR_DECIMAL")

        if not isinstance(value, (int, str, Decimal)):
            logger.error("CURRENCY_VALUE_REJECTED_INVALID_TYPE: %r", value)
            raise TypeError("CURRENCY_VALUE_MUST_BE_INT_STR_OR_DECIMAL")

        try:
            decimal_val = Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            logger.error("CURRENCY_VALUE_INVALID_DECIMAL_REPRESENTATION: %r", value)
            raise ValueError(f"INVALID_FINANCIAL_DECIMAL_REPRESENTATION: {value}") from exc

        if decimal_val.is_nan() or decimal_val.is_infinite():
            logger.error("CURRENCY_VALUE_NAN_OR_INF: %s", decimal_val)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_FINANCIAL_VALUE_CANNOT_BE_NAN_OR_INFINITE")

        # Eksekusi Bankers' Rounding secara aman di level inisialisasi hulu data
        return decimal_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)

    @classmethod
    def from_numeric_safe(
        cls, amount: Union[int, str, Decimal], unit: CurrencyUnit = CurrencyUnit.IDR
    ) -> "Currency":
        """
        Named constructor aman untuk instansiasi objek finansial baru
        tanpa mengekspos tipe data float yang rawan presisi.
        """
        return cls(value=amount, unit=unit)

    def to_formatted_string(self) -> str:
        """
        Fungsi eksternal formal untuk mencetak representasi keuangan standard QS.
        Memisahkan domain model dari polusi aturan tampilan antarmuka (UI).
        """
        if self.unit == CurrencyUnit.IDR:
            return f"Rp {self.value:,.2f}"
        return f"$ {self.value:,.2f}"

    def approximately_equal(
        self,
        other: Any,
        epsilon: Union[int, float, str, Decimal] = "0.50",
    ) -> bool:
        """
        Memverifikasi kesamaan nilai keuangan berdasarkan batas toleransi selisih Decimal absolut.
        """
        if not isinstance(other, Currency) or self.unit != other.unit:
            return False
        try:
            epsilon_dec = Decimal(str(epsilon))
        except (InvalidOperation, ValueError) as exc:
            logger.error("CURRENCY_APPROX_EPSILON_INVALID: %r", epsilon)
            raise ValueError("INVALID_EPSILON_DECIMAL_VALUE") from exc
        return abs(self.value - other.value) <= epsilon_dec

    def __add__(self, other: Any) -> "Currency":
        if not isinstance(other, Currency):
            logger.error("CURRENCY_ADD_REJECTED_NON_CURRENCY: %r", other)
            raise TypeError("OPERAND_MUST_BE_AN_INSTANCE_OF_CURRENCY_CLASS")
        if self.unit != other.unit:
            logger.error(
                "CURRENCY_ADD_UNIT_MISMATCH: %s vs %s",
                self.unit.value,
                other.unit.value,
            )
            raise ValueError("CURRENCY_UNIT_MISMATCH_CANNOT_PERFORM_ARITHMETIC_OPERATIONS")
        return Currency(value=self.value + other.value, unit=self.unit)

    def __sub__(self, other: Any) -> "Currency":
        if not isinstance(other, Currency):
            logger.error("CURRENCY_SUB_REJECTED_NON_CURRENCY: %r", other)
            raise TypeError("OPERAND_MUST_BE_AN_INSTANCE_OF_CURRENCY_CLASS")
        if self.unit != other.unit:
            logger.error(
                "CURRENCY_SUB_UNIT_MISMATCH: %s vs %s",
                self.unit.value,
                other.unit.value,
            )
            raise ValueError("CURRENCY_UNIT_MISMATCH_CANNOT_PERFORM_ARITHMETIC_OPERATIONS")
        return Currency(value=self.value - other.value, unit=self.unit)

    def __mul__(self, scalar: Any) -> "Currency":
        if isinstance(scalar, bool):
            logger.error("CURRENCY_MUL_REJECTED_BOOLEAN: %r", scalar)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(scalar, (int, float, str, Decimal)):
            logger.error("CURRENCY_MUL_REJECTED_INVALID_TYPE: %r", scalar)
            raise TypeError("SCALAR_MULTIPLIER_MUST_BE_INT_FLOAT_STR_OR_DECIMAL")
        try:
            decimal_scalar = Decimal(str(scalar))
        except (InvalidOperation, ValueError) as exc:
            logger.error("CURRENCY_MUL_INVALID_SCALAR: %r", scalar)
            raise ValueError("INVALID_SCALAR_DECIMAL_CONVERSION") from exc

        if decimal_scalar.is_nan() or decimal_scalar.is_infinite():
            logger.error("CURRENCY_MUL_SCALAR_NAN_OR_INF: %s", decimal_scalar)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_SCALAR_CANNOT_BE_NAN_OR_INFINITE")

        return Currency(value=self.value * decimal_scalar, unit=self.unit)

    def __rmul__(self, scalar: Any) -> "Currency":
        return self.__mul__(scalar)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Currency):
            return False
        return self.value == other.value and self.unit == other.unit

    def __str__(self) -> str:
        return f"{self.value} {self.unit.value}"

    def __repr__(self) -> str:
        return f"Currency({self.value} {self.unit.value})"