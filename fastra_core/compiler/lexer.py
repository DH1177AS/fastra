# fastra_core\compiler\lexer.py

from __future__ import annotations

import enum
import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from fastra_core.compiler.ccm_envelope import CCMEnvelope, ErrorCode


class LexerErrorCode(str, enum.Enum):
    
    LEX_001 = "LEX-001"  # Malformed JSON payload / structural error


# ---------------------------------------------------------------------------
# Inbound & Outbound DTOs – Pydantic Strict Gateway (Fail-Fast)
# ---------------------------------------------------------------------------

class LexerErrorLogDTO(BaseModel):
  
    model_config = ConfigDict(extra="forbid", strict=True)

    error_code: str = Field(..., min_length=7, max_length=7, pattern=r"^LEX-[0-9]{3}$")
    message: str = Field(..., min_length=5, max_length=4096)


# ---------------------------------------------------------------------------
# Domain Models & Compiler Component – Pure Lexical Gatekeeper (QS-Safe)
# ---------------------------------------------------------------------------

class Lexer:
    
    def __init__(self) -> None:
        self._errors: List[Dict[str, Any]] = []
        self._warnings: List[Dict[str, Any]] = []

    @property
    def errors(self) -> List[Dict[str, Any]]:
       
        return list(self._errors)

    @property
    def warnings(self) -> List[Dict[str, Any]]:
        
        return list(self._warnings)

    def load(self, source: Any) -> Optional[CCMEnvelope]:
        
        self._errors.clear()
        self._warnings.clear()
       
        if isinstance(source, str):
            try:
                data = json.loads(source)
            except json.JSONDecodeError as e:
                self._add_error(
                    code=LexerErrorCode.LEX_001.value,
                    msg=f"Kegagalan fatal penguraian string JSON: {str(e)}"
                )
                return None
        elif isinstance(source, dict):
            data = source
        else:
            self._add_error(
                code=LexerErrorCode.LEX_001.value,
                msg=f"Tipe data masukan ilegal '{type(source).__name__}'. Root dokumen wajib berupa JSON string atau Python dictionary."
            )
            return None
        
        if not isinstance(data, dict):
            self._add_error(
                code=LexerErrorCode.LEX_001.value,
                msg="Pelanggaran struktur dokumen hulu: Objek root utama wajib bertipe fungsional map/dictionary."
            )
            return None
       
        env = CCMEnvelope(
            ccm_version=str(data.get("ccm_version", "")),
            project_uuid=str(data.get("project_uuid", "")),
            entities=list(data.get("entities", []) or []),
            relationships=list(data.get("relationships", []) or [])
        )
       
        envelope_errors = env.validate()
        for err in envelope_errors:
            self._add_error(
                code=err.get("error_code", LexerErrorCode.LEX_001.value),
                msg=err.get("message", "Kesalahan validasi amplop dokumen tidak teridentifikasi.")
            )

        return env if not self._errors else None

    def _add_error(self, code: str, msg: str) -> None:
        
        error_payload = {
            "error_code": code,
            "message": msg
        }
                
        validated_error = LexerErrorLogDTO(**error_payload)
        self._errors.append(validated_error.model_dump())