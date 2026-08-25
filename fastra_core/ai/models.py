"""
ACES-700 AI Layer Models
Model data untuk output Vision AI, Drawing AI, LLM Assistant, dan Prediction AI.
Setiap output AI wajib menyertakan confidence, asumsi, dan batasan.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


def _hash_json(data: Any) -> str:
    """Menghitung SHA-256 dari data JSON."""
    canonical = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class VisionResult:
    """Output Vision AI (estimasi awal dari foto)."""
    model_version: str
    input_photos: List[str]
    estimations: Dict[str, Any]
    timestamp: str = field(default_factory=_utc_now)
    result_uuid: str = field(default_factory=lambda: str(uuid4()))
    assumptions: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    suggested_actions: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Validasi setiap estimation memiliki 'confidence'
        for key, value in self.estimations.items():
            if not isinstance(value, dict) or "confidence" not in value:
                raise ValueError(f"Estimation '{key}' harus memiliki 'confidence'")
            confidence = value["confidence"]
            if not (0.0 <= float(confidence) <= 1.0):
                raise ValueError(f"Confidence untuk '{key}' harus antara 0 dan 1")

    def input_hash(self) -> str:
        return _hash_json(self.input_photos)

    def output_hash(self) -> str:
        return _hash_json(self.estimations)


@dataclass
class DetectedElement:
    proposed_uuid: str
    type: str
    confidence: float
    source: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("Confidence harus antara 0 dan 1")


@dataclass
class DrawingResult:
    """Output Drawing Reader AI (CCM proposal dari denah/PDF/CAD)."""
    model_version: str
    input_files: List[str]
    detected_elements: Dict[str, List[DetectedElement]]
    detected_dimensions: Dict[str, Any]
    generated_ccm: Dict[str, Any] = field(default_factory=dict)
    uncertainties: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: str = field(default_factory=_utc_now)
    result_uuid: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        # Validasi generated_ccm sesuai ACES-200? Untuk fase 1 cukup pastikan detected_elements tidak kosong
        if not self.detected_elements:
            raise ValueError("detected_elements tidak boleh kosong")

    def input_hash(self) -> str:
        return _hash_json(self.input_files)

    def output_hash(self) -> str:
        return _hash_json(self.detected_elements)


@dataclass
class LLMResult:
    """Output LLM Assistant (DSL, penjelasan, rekomendasi)."""
    model_version: str
    input_text: str
    output_dsl: Optional[str] = None
    explanation: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    contains_direct_boq: bool = False
    content_safe: bool = True
    timestamp: str = field(default_factory=_utc_now)
    result_uuid: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        # LLM tidak boleh menghasilkan BOQ langsung
        if self.contains_direct_boq:
            raise ValueError("LLM output tidak boleh mengandung BOQ langsung")
        # Deteksi otomatis indikator BOQ/RAB dalam output
        boq_indicators = ["BOQ", "BILL OF QUANTITY", "RAB"]
        combined = ((self.output_dsl or "") + " " + (self.explanation or "")).upper()
        for indicator in boq_indicators:
            if indicator in combined:
                self.contains_direct_boq = True
                raise ValueError("LLM output tidak boleh mengandung BOQ/RAB langsung")
        # Safety filter sederhana: kata-kata berbahaya dilarang
        forbidden_words = ["runtuh", "keruntuhan", "bahaya", "melanggar building code", "membahayakan"]
        lowered = (self.output_dsl or "").lower() + (self.explanation or "").lower()
        for word in forbidden_words:
            if word in lowered:
                self.content_safe = False
                break
        if not self.content_safe:
            raise ValueError("LLM output mengandung konten berbahaya dan ditolak")

    def input_hash(self) -> str:
        return _hash_json(self.input_text)

    def output_hash(self) -> str:
        return _hash_json({
            "output_dsl": self.output_dsl,
            "explanation": self.explanation,
            "recommendations": self.recommendations,
        })


@dataclass
class Prediction:
    """Satu item prediksi dari Prediction AI."""
    type: str
    data: Dict[str, Any]
    confidence_interval: Optional[List[float]] = None
    confidence_level: Optional[float] = None

    def __post_init__(self) -> None:
        # Setiap prediksi harus memiliki interval atau level confidence
        if self.confidence_interval is None and self.confidence_level is None:
            raise ValueError("Prediction harus memiliki confidence_interval atau confidence_level")


@dataclass
class PredictionResult:
    """Output Prediction AI (forecast, risiko, optimasi)."""
    model_version: str
    predictions: List[Prediction]
    recommendations: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=_utc_now)
    result_uuid: str = field(default_factory=lambda: str(uuid4()))

    def input_hash(self) -> str:
        return _hash_json([p.type for p in self.predictions])

    def output_hash(self) -> str:
        return _hash_json(self.predictions)

