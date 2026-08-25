"""
ACES-700 Content Safety Filter untuk LLM Assistant.
"""
from __future__ import annotations

from typing import List, Tuple

FORBIDDEN_WORDS = [
    "runtuh",
    "keruntuhan",
    "bahaya",
    "membahayakan",
    "melanggar building code",
    "tidak sesuai snsi",
]

class SafetyFilter:
    """Filter keamanan konten untuk output LLM."""

    def __init__(self, forbidden_words: List[str] | None = None) -> None:
        self.forbidden_words = forbidden_words or FORBIDDEN_WORDS

    def check(self, text: str) -> Tuple[bool, str]:
        """Mengembalikan (aman, alasan)."""
        lowered = text.lower()
        for word in self.forbidden_words:
            if word in lowered:
                return False, f"Konten mengandung kata terlarang: {word}"
        return True, ""

    def filter(self, text: str) -> str:
        """Menghapus kata-kata terlarang dari teks (redact)."""
        filtered = text
        for word in self.forbidden_words:
            filtered = filtered.replace(word, "[REDACTED]")
        return filtered
