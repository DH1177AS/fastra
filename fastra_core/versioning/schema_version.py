# fastra_core\versioning\schema_version.py

from __future__ import annotations

import logging
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra_core.versioning.schema_version")


class VersionCompatibility(str, Enum):
    """Taksonomi formal untuk status kompatibilitas transisi skema data."""
    COMPATIBLE = "compatible"
    NEEDS_MIGRATION = "needs_migration"
    INCOMPATIBLE = "incompatible"


class SchemaVersion(BaseModel):
    """
    Primitive Value Object untuk mengelola versi tata letak skema data (Schema Versioning).
    Menjamin penolakan manipulasi paksa (coercion hacks) di level penomoran integer hulu.
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    def __init__(self, *args, **kwargs):
        if args:
            if len(args) > 3:
                raise TypeError("SchemaVersion only accepts up to three positional arguments (major, minor, patch)")
            names = ['major', 'minor', 'patch']
            for i, val in enumerate(args):
                kwargs.setdefault(names[i], val)
        super().__init__(**kwargs)

    major: int = Field(..., ge=0, description="Perubahan skema destruktif skala besar (Breaking Changes)")
    minor: int = Field(..., ge=0, description="Penambahan tabel/kolom non-destruktif berskala aditif")
    patch: int = Field(..., ge=0, description="Penyelarasan indeks minor atau dokumentasi internal")

    @field_validator("major", "minor", "patch", mode="before")
    @classmethod
    def validate_integers_no_coercion(cls, value: Any) -> int:
        if isinstance(value, bool):
            logger.error("SCHEMA_VERSION_COMPONENT_BOOLEAN_REJECTED: %r", value)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(value, int):
            logger.error("SCHEMA_VERSION_COMPONENT_NON_INTEGER_REJECTED: %r", value)
            raise TypeError("SCHEMA_VERSION_COMPONENT_MUST_BE_A_PURE_INTEGER")
        if value < 0:
            logger.error("SCHEMA_VERSION_COMPONENT_NEGATIVE_REJECTED: %s", value)
            raise ValueError("SCHEMA_VERSION_COMPONENT_MUST_BE_NON_NEGATIVE")
        return value

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def parse(cls, s: Any) -> "SchemaVersion":
        """
        Mengurai token string (misal '2.1.0') menjadi objek SchemaVersion terkompilasi.
        Mengeksekusi penapisan whitespace dan filter fail-fast secara atomik.
        """
        if not isinstance(s, str) or not s.strip():
            logger.error("SCHEMA_VERSION_PARSING_INVALID_INPUT: %r", s)
            raise ValueError("SCHEMA_VERSION_PARSING_ERROR_INPUT_MUST_BE_A_PURE_NON_EMPTY_STRING")

        clean_str = s.strip()
        parts = clean_str.split(".")
        if len(parts) != 3:
            logger.error("SCHEMA_VERSION_PARSING_TOKEN_COUNT_VIOLATION: %s", clean_str)
            raise ValueError(
                f"SEMANTIC_SCHEMA_VERSION_FORMAT_VIOLATION_MUST_CONTAIN_THREE_TOKENS: '{clean_str}'"
            )

        try:
            # Pydantic v2 otomatis mengevaluasi rentang integer fisis saat instansiasi
            return cls(major=int(parts[0]), minor=int(parts[1]), patch=int(parts[2]))
        except (ValueError, TypeError) as e:
            logger.error("SCHEMA_VERSION_PARSING_INVALID_INTEGER_TOKENS: %s", clean_str)
            raise ValueError(
                f"SCHEMA_VERSION_PARSING_ERROR_INVALID_INTEGER_TOKENS_FOUND: {clean_str}"
            ) from e

    def is_compatible_with(self, other: "SchemaVersion") -> VersionCompatibility:
        """
        Mengevaluasi matriks kompatibilitas skema (Schema Compatibility Matrix Resolver).
        Menentukan jalur migrasi data hulu-ke-hilir untuk mencegah data corruption.
        """
        if not isinstance(other, SchemaVersion):
            logger.error("COMPATIBILITY_CHECK_INVALID_TYPE: %r", other)
            raise TypeError("COMPATIBILITY_CHECK_REQUIRES_A_VALID_SCHEMAVERSION_INSTANCE")

        if self.major != other.major:
            result = VersionCompatibility.INCOMPATIBLE
        elif self.minor != other.minor:
            result = VersionCompatibility.NEEDS_MIGRATION
        else:
            result = VersionCompatibility.COMPATIBLE

        logger.debug(
            "Schema compatibility check: %s vs %s -> %s",
            self,
            other,
            result.value,
        )
        return result