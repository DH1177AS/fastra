# fastra_core\ai\safety.py

from __future__ import annotations

import logging
import re
from typing import Any, List, Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("fastra_core.ai.safety")

# Immutable Global Configuration Whitelist Matrix
FORBIDDEN_WORDS: List[str] = [
    "runtuh",
    "keruntuhan",
    "bahaya",
    "membahayakan",
    "melanggar building code",
    "tidak sesuai sni",  # FIXED: Koreksi typo dari 'snsi' menjadi 'sni'
]


class SafetyFilter(BaseModel):
    """
    Filter Sensor Keamanan Konten Kognitif (Cognitive & Structural Safety Filter Engine).
    Melindungi integritas keputusan AI dari upaya sabotase istilah atau parameter tak aman
    sesuai kepatuhan arsitektur militer ACES-700.
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    forbidden_words: Tuple[str, ...] = Field(
        default_factory=lambda: tuple(FORBIDDEN_WORDS),
        description="Daftar kata terlarang yang diimutabilkan menjadi tuple",
    )

    @field_validator("forbidden_words", mode="before")
    @classmethod
    def validate_and_sanitize_keywords(cls, value: Any) -> Tuple[str, ...]:
        if isinstance(value, bool):
            logger.error("FORBIDDEN_WORDS_BOOLEAN_REJECTED: %r", value)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(value, (list, tuple)):
            logger.error("FORBIDDEN_WORDS_MUST_BE_LIST_OR_TUPLE: %r", value)
            raise TypeError("FORBIDDEN_WORDS_MUST_BE_A_VALID_COLLECTION_CONTAINER")

        clean_words: List[str] = []
        for idx, word in enumerate(value):
            if not isinstance(word, str):
                logger.error("KEYWORD_ELEMENT_NOT_STRING_AT_INDEX_%d: %r", idx, word)
                raise TypeError(f"KEYWORD_ELEMENT_MUST_BE_A_PURE_STRING_AT_INDEX_{idx}")
            stripped = word.strip().lower()
            if not stripped:
                logger.error("EMPTY_KEYWORD_TOKEN_AT_INDEX_%d", idx)
                raise ValueError(f"EMPTY_KEYWORD_TOKENS_FORBIDDEN_AT_INDEX_{idx}")
            clean_words.append(stripped)

        return tuple(clean_words)

    def check(self, text: str) -> Tuple[bool, str]:
        """
        Memverifikasi keabsahan konten teks secara fail-fast dan deterministik.
        Menggunakan pencocokan batas kata (Word Boundary Compilation) untuk mencegah deteksi False-Positive.
        """
        if not isinstance(text, str):
            logger.error("SAFETY_CHECK_INPUT_MUST_BE_STRING: %r", text)
            raise TypeError("SAFETY_CHECK_ERROR_INPUT_MUST_BE_A_PURE_STRING")

        clean_text = text.strip()
        if not clean_text:
            return True, ""

        lowered_text = clean_text.lower()
        for word in self.forbidden_words:
            # Gunakan boundary \b dan escape untuk memblokir bypass modifikasi imbuhan
            pattern = rf"\b{re.escape(word)}\b"
            if re.search(pattern, lowered_text):
                logger.warning("COGNITIVE_SAFETY_VIOLATION_DETECTED: token=%s", word)
                return False, f"COGNITIVE_SAFETY_VIOLATION: Content identified containing restricted token '{word}'."

        return True, ""

    def filter(self, text: str) -> str:
        """
        Mengeksekusi penyuntingan paksa (Redaction Engine) terhadap kata terlarang secara non-destruktif.
        Menghasilkan representasi string terisolasi baru murni di level memori runtime.
        """
        if not isinstance(text, str):
            logger.error("SAFETY_FILTER_INPUT_MUST_BE_STRING: %r", text)
            raise TypeError("SAFETY_FILTER_ERROR_INPUT_MUST_BE_A_PURE_STRING")

        clean_text = text.strip()
        if not clean_text:
            return ""

        filtered_result = clean_text
        for word in self.forbidden_words:
            pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
            filtered_result = pattern.sub("[REDACTED]", filtered_result)

        if filtered_result != clean_text:
            logger.info("SAFETY_FILTER_REDACTED_TERMS")
        return filtered_result