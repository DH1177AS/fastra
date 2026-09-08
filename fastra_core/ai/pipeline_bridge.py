# fastra_core\ai\pipeline_bridge.py

from __future__ import annotations

import logging
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from fastra_core.ai.dsl_translator import DSLTranslationResult
from fastra_core.ai.verification import VerificationResult

logger = logging.getLogger("fastra_core.ai.pipeline_bridge")


class PipelineEntryApproval(BaseModel):
    """
    Model Value Object laporan kelayakan entri peluncuran pipa data (Pipeline Guard Report).
    Menjamin kedaulatan data orkestrasi lewat imutabilitas murni (frozen=True).
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    approved: bool = Field(..., description="Flag kelayakan peluncuran data kognitif AI")
    reason: str = Field(default="", max_length=512, description="Justifikasi landasan otorisasi keputusan")

    @field_validator("approved", mode="before")
    @classmethod
    def validate_approved_strict_bool(cls, value: Any) -> bool:
        if not isinstance(value, bool):
            logger.error("APPROVED_FLAG_MUST_BE_STRICT_BOOLEAN: %r", value)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_APPROVED_FLAG_MUST_BE_PURE_BOOLEAN")
        return value

    @field_validator("reason", mode="before")
    @classmethod
    def sanitize_reason_string(cls, value: Any) -> str:
        if value is None:
            return ""
        if not isinstance(value, str):
            logger.error("REASON_STRING_COERCION_REJECTED: %r", value)
            raise TypeError("VALUE_MUST_BE_A_PURE_STRING_COERCION_FORBIDDEN")
        stripped = value.strip()
        if not stripped and value:
            logger.error("REASON_WHITESPACE_ONLY_REJECTED")
            raise ValueError("STRING_CANNOT_CONSIST_OF_WHITESPACE_ONLY")
        return stripped


class PipelineBridge(BaseModel):
    """
    Gerbang Jembatan Kendali Aliran Kognitif (AI Cognitive-to-Deterministic Pipeline Bridge).
    Memutus tuntas risiko kebocoran otomatisasi inferensi AI liar ke dalam pipeline kompilasi
    grafik pengetahuan utama tanpa gerbang tinjauan ganda (Human-In-The-Loop Enforcer).
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
    )

    def submit(
        self,
        translation: DSLTranslationResult,
        human_approved: bool,
        verification: Optional[VerificationResult] = None,
    ) -> PipelineEntryApproval:
        """
        Mengevaluasi prasyarat kelayakan sebelum meneruskan kode Construction DSL
        menuju unit kompilasi mesin Parser deterministik hulu.
        """
        if not isinstance(translation, DSLTranslationResult):
            logger.error("SUBMIT_INVALID_TRANSLATION_TYPE: %r", translation)
            raise TypeError("BRIDGE_ERROR_TRANSLATION_MUST_BE_AN_INSTANCE_OF_DSL_TRANSLATION_RESULT")

        if not isinstance(human_approved, bool):
            logger.error("SUBMIT_HUMAN_APPROVED_MUST_BE_BOOL: %r", human_approved)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED_IN_HUMAN_APPROVED")

        # 1. Gerbang Otorisasi Manual (Human Approval Cross-Check)
        if not human_approved:
            logger.info("PIPELINE_ENTRY_BLOCKED_HUMAN_DISAPPROVAL")
            return PipelineEntryApproval(
                approved=False,
                reason="SECURITY_BLOCK_HUMAN_REVIEW_DISAPPROVAL: Manual review engineer authorization required.",
            )

        # 2. Gerbang Integritas Kode Sumber (DSL Syntax Presence Check)
        if not translation.dsl_text or not translation.dsl_text.strip():
            logger.info("PIPELINE_ENTRY_BLOCKED_EMPTY_DSL")
            return PipelineEntryApproval(
                approved=False,
                reason="INTEGRITY_BLOCK_EMPTY_DSL_TEXT: Empty code blocks are restricted from entering compilation lanes.",
            )

        # 3. Gerbang Otorisasi Verifikasi Kognitif (Verification Gate Cross-Check)
        if verification is not None:
            if not isinstance(verification, VerificationResult):
                logger.error("SUBMIT_INVALID_VERIFICATION_TYPE: %r", verification)
                raise TypeError("BRIDGE_ERROR_VERIFICATION_MUST_BE_AN_INSTANCE_OF_VERIFICATION_RESULT")

            if not verification.passed:
                status_str = (
                    verification.status.value
                    if hasattr(verification.status, "value")
                    else str(verification.status)
                )
                logger.info("PIPELINE_ENTRY_BLOCKED_VERIFICATION_FAILED: %s", status_str)
                return PipelineEntryApproval(
                    approved=False,
                    reason=f"AUTOMATION_GATE_BLOCK_VERIFICATION_FAILED: State code criteria drop. Gate Status: {status_str}",
                )

        # Seluruh kriteria terpenuhi
        logger.info("PIPELINE_ENTRY_GRANTED")
        return PipelineEntryApproval(
            approved=True,
            reason="PIPELINE_AUTHORIZATION_GRANTED: Artifact validated and successfully delegated to the deterministic parsing lane.",
        )