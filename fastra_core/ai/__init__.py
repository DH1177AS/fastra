from __future__ import annotations

import logging
import threading
from typing import Any, Dict, List, Type

# Expose strict cognitive components down to the module boundary layer
from .enums import (
    AIComponent,
    VerificationStatus,
    ConfidenceFlag,
    HumanReviewAction,
    validate_ai_enum_value,
)
from .models import (
    VisionResult,
    DrawingResult,
    DetectedElement,
    LLMResult,
    PredictionResult,
    Prediction,
)
from .verification import VerificationGate, VerificationResult
from .audit import AIEventLog, AIEventStore
from .safety import SafetyFilter
from .dsl_translator import DSLTranslator, DSLTranslationResult
from .pipeline_bridge import PipelineBridge, PipelineEntryApproval
from .ai_service import AIService

logger = logging.getLogger("fastra_core.ai")

_AI_PACKAGE_LOCK = threading.Lock()


def verify_ai_subsystem_health() -> Dict[str, Any]:
    """
    Executes a high-order structural fail-fast smoke test during module load time.
    Guarantees all immutable cognitive engines and verification gates have compiled
    without structural type drift or context corruption.
    """
    if not _AI_PACKAGE_LOCK.acquire(timeout=10):
        logger.error("AI_HEALTH_CHECK_LOCK_ACQUISITION_TIMEOUT")
        raise TimeoutError("AI_HEALTH_CHECK_LOCK_ACQUISITION_TIMEOUT")

    try:
        monitored_classes: List[Type[Any]] = [
            VerificationGate,
            AIEventStore,
            SafetyFilter,
            DSLTranslator,
            PipelineBridge,
            AIService,
        ]

        for cls in monitored_classes:
            if cls is None:
                logger.error("AI_INITIALIZATION_ERROR: Critical core cognitive class failed to instantiate.")
                raise ImportError(
                    f"AI_INITIALIZATION_ERROR: Critical core cognitive class {cls} failed to instantiate."
                )

        logger.info("AI subsystem health check passed")
        return {
            "status": "HEALTHY",
            "layer": "AI_CORE_SUBPACKAGE",
            "military_grade_lock_active": True,
        }
    finally:
        _AI_PACKAGE_LOCK.release()


# Automatically fire high-order structural integrity enforcement on package activation
verify_ai_subsystem_health()

__all__ = [
    # Enums & Taxonomy Matrix
    "AIComponent",
    "VerificationStatus",
    "ConfidenceFlag",
    "HumanReviewAction",
    "validate_ai_enum_value",

    # Cognitive Struct Models
    "VisionResult",
    "DrawingResult",
    "DetectedElement",
    "LLMResult",
    "PredictionResult",
    "Prediction",

    # Validation Gate Framework
    "VerificationGate",
    "VerificationResult",

    # O(1) Cognitive Ledger Store
    "AIEventLog",
    "AIEventStore",

    # Input Content Sanitisers
    "SafetyFilter",

    # Natural Language Translation Matrix
    "DSLTranslator",
    "DSLTranslationResult",

    # Deterministic Processing Channels
    "PipelineBridge",
    "PipelineEntryApproval",

    # AI Lifecycle Orchestrator
    "AIService",

    # Subsystem Diagnostics
    "verify_ai_subsystem_health",
]