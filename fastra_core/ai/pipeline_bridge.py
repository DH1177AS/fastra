"""
ACES-700 AI Pipeline Bridge (hardened)
Hanya meneruskan output AI ke pipeline deterministik setelah verifikasi dan human approval.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastra_core.ai.dsl_translator import DSLTranslationResult
from fastra_core.ai.verification import VerificationResult


@dataclass
class PipelineEntryApproval:
    approved: bool
    reason: str = ""


class PipelineBridge:
    """Bridge untuk meneruskan DSL ke pipeline setelah verifikasi & approval."""

    def submit(
        self,
        translation: DSLTranslationResult,
        human_approved: bool,
        verification: Optional[VerificationResult] = None,
    ) -> PipelineEntryApproval:
        if not human_approved:
            return PipelineEntryApproval(approved=False, reason="Human review belum menyetujui")
        if not translation.dsl_text:
            return PipelineEntryApproval(approved=False, reason="DSL kosong")
        if verification is not None and not verification.passed:
            return PipelineEntryApproval(approved=False, reason=f"Verification gate gagal: {verification.status.value}")
        # Di sini nantinya akan dipanggil Parser. Simulasi:
        return PipelineEntryApproval(approved=True, reason="Siap diproses ke Parser")
