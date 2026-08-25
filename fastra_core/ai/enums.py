"""
ACES-700 AI Layer Enums
Menstandarkan komponen AI, status verifikasi, dan flag.
"""
from enum import Enum


class AIComponent(str, Enum):
    VISION_AI = "VISION_AI"
    DRAWING_AI = "DRAWING_AI"
    LLM_ASSISTANT = "LLM_ASSISTANT"
    PREDICTION_AI = "PREDICTION_AI"


class VerificationStatus(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"
    FLAGGED_HIGH_UNCERTAINTY = "FLAGGED_HIGH_UNCERTAINTY"
    FLAGGED_INCOMPLETE = "FLAGGED_INCOMPLETE"
    FLAGGED_INCONSISTENT = "FLAGGED_INCONSISTENT"


class ConfidenceFlag(str, Enum):
    OK = "OK"
    HIGH_UNCERTAINTY = "HIGH_UNCERTAINTY"


class HumanReviewAction(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MODIFIED = "MODIFIED"
