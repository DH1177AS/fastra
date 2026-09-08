# fastra_core\errors\exceptions.py

from __future__ import annotations

import logging
import math
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from fastra_core.identity import Identity

logger = logging.getLogger("fastra_core.errors.exceptions")


class ErrorContextModel(BaseModel):
    """
    Model skema Pydantic v2 internal untuk memvalidasi dan mengunci struktur data
    kontekstual dari kesalahan sistem (Exception Context Storage).
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    code: str = Field(..., min_length=3, max_length=32, pattern=r"^[A-Z0-9\-]+$")
    message: str = Field(..., min_length=2, max_length=1024)
    error_uuid: str = Field(default_factory=Identity.generate)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    details: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("message", mode="before")
    @classmethod
    def sanitize_log_injection(cls, value: Any) -> str:
        """
        Menghapus total celah eksploitasi serangan Log Splitting / Log Injection.
        Karakter carriage return (\r) dan line feed (\n) dibersihkan secara paksa hulu.
        """
        if not isinstance(value, str):
            logger.error("ERROR_MESSAGE_MUST_BE_A_PURE_STRING: %r", value)
            raise TypeError("ERROR_MESSAGE_MUST_BE_A_PURE_STRING")
        # Mengganti baris baru menjadi karakter pemisah space pipelining datar
        cleaned = re.sub(r"[\r\n]", " | ", value).strip()
        if not cleaned:
            logger.error("ERROR_MESSAGE_CANNOT_BE_EMPTY_OR_WHITESPACE")
            raise ValueError("ERROR_MESSAGE_CANNOT_BE_EMPTY_OR_WHITESPACE")
        return cleaned

    @field_validator("error_uuid", mode="after")
    @classmethod
    def validate_uuid_integrity(cls, value: str) -> str:
        if not Identity.is_valid(value):
            logger.error("ERROR_CONTEXT_INVALID_UUID: %s", value)
            raise ValueError("UUID_INTEGRITY_COMPROMISED_INVALID_STRUCTURE")
        return value

    @field_validator("details", mode="before")
    @classmethod
    def validate_details_numeric(cls, value: Any) -> Dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            logger.error("ERROR_DETAILS_MUST_BE_A_VALID_DICTIONARY: %r", value)
            raise TypeError("ERROR_DETAILS_MUST_BE_A_VALID_DICTIONARY")
        clean_details: Dict[str, Any] = {}
        for k, v in value.items():
            if not isinstance(k, str) or not k.strip():
                logger.error("ERROR_DETAILS_INVALID_KEY: %r", k)
                raise ValueError("ERROR_DETAILS_KEYS_MUST_BE_NON_EMPTY_STRINGS")
            if isinstance(v, bool):
                logger.error("ERROR_DETAILS_BOOLEAN_REJECTED_AT_KEY_%s: %r", k, v)
                raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
            if isinstance(v, (int, float)):
                if math.isnan(v) or math.isinf(v):
                    logger.error("ERROR_DETAILS_NUMERIC_ANOMALY_AT_KEY_%s: %s", k, v)
                    raise ValueError(f"NUMERIC_ANOMALY_DETECTED_IN_ERROR_CONTEXT_AT_KEY_{k}")
            clean_details[k.strip()] = v
        return clean_details


class CESError(Exception):
    """
    Pengecualian Basis Asasi Platform FASTRA (Core System Exception Ledger Base).
    Mewarisi kelas Exception Python formal namun dievaluasi via strict validator Pydantic.
    """
    DEFAULT_CODE: str = "CES-000"

    def __init__(
        self,
        message: str = "",
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not isinstance(message, str):
            logger.error("CESError_MESSAGE_MUST_BE_STRING: %r", message)
            raise TypeError("ERROR_MESSAGE_MUST_BE_A_PURE_STRING")
        if code is not None and not isinstance(code, str):
            logger.error("CESError_CODE_MUST_BE_STRING_OR_NONE: %r", code)
            raise TypeError("ERROR_CODE_MUST_BE_A_PURE_STRING_OR_NONE")
        if details is not None and not isinstance(details, dict):
            logger.error("CESError_DETAILS_MUST_BE_DICT_OR_NONE: %r", details)
            raise TypeError("ERROR_DETAILS_MUST_BE_A_VALID_DICTIONARY_OR_NONE")

        target_code = (code or self.__class__.DEFAULT_CODE).strip().upper()
        target_message = (
            message.strip()
            if message.strip()
            else f"An unhandled execution error occurred in {self.__class__.__name__}"
        )

        # Validasi via Pydantic v2
        self._context = ErrorContextModel(
            code=target_code,
            message=target_message,
            details=details or {},
        )

        super().__init__(
            f"[{self._context.code}] (Trace-ID: {self._context.error_uuid}) {self._context.message}"
        )
        logger.error("CESError raised: code=%s trace=%s message=%s",
                     self._context.code, self._context.error_uuid, self._context.message)

    @property
    def code(self) -> str:
        return self._context.code

    @property
    def message(self) -> str:
        return self._context.message

    @property
    def error_uuid(self) -> str:
        return self._context.error_uuid

    @property
    def timestamp(self) -> datetime:
        return self._context.timestamp

    @property
    def details(self) -> Dict[str, Any]:
        return self._context.details

    def to_dict(self) -> Dict[str, Any]:
        """
        Mengekspor representasi komprehensif kegagalan sistem ke bentuk kamus primitif terikat JSON.
        """
        return {
            "error_uuid": self.error_uuid,
            "timestamp": self.timestamp.isoformat(),
            "code": self.code,
            "message": self.message,
            "details": dict(self.details),
        }


# ---------- DOMAIN ARCHITECTURE CORE EXCEPTIONS CLASS MATRICES ----------

class GeometryError(CESError):
    DEFAULT_CODE = "GEO-001"


class TopologyError(CESError):
    DEFAULT_CODE = "TOP-001"


class UnitError(CESError):
    DEFAULT_CODE = "UNIT-001"


class CostError(CESError):
    DEFAULT_CODE = "COST-001"


class ValidationError(CESError):
    DEFAULT_CODE = "VAL-001"


class CompilerError(CESError):
    DEFAULT_CODE = "COMP-001"


class SerializationError(CESError):
    DEFAULT_CODE = "SER-001"


class VersionError(CESError):
    DEFAULT_CODE = "VER-001"