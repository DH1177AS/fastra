# fastra_core\ccm\ai_layer.py

from __future__ import annotations

import enum
import hashlib
import hmac
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RiskProbability(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CompatibilityLevel(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNVERIFIED = "unverified"


class PricePredictionInputDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    material_id: str = Field(
        ...,
        min_length=5,
        max_length=64,
        pattern=r"^mat_[a-z0-9_]+$",
        description="ID material dengan format mat_xxxxx",
    )
    months_ahead: int = Field(
        default=3,
        gt=0,
        le=24,
        description="Jumlah bulan ke depan untuk prediksi (1-24)",
    )


class AlternativeRecommendationInputDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    material_id: str = Field(
        ...,
        min_length=5,
        max_length=64,
        pattern=r"^mat_[a-z0-9_]+$",
    )
    budget_constraint: Optional[float] = Field(
        default=None,
        gt=0.0,
        le=1e12,
        description="Batasan anggaran opsional dalam satuan mata uang",
    )


class CostRisksInputDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    project_id: str = Field(
        ...,
        min_length=5,
        max_length=64,
        pattern=r"^prj_[a-z0-9_]+$",
    )
    total_budget: float = Field(..., gt=0.0, le=1e12)
    items_count: int = Field(..., gt=0, le=1_000_000)


class PricePredictionDomainModel:
    def __init__(
        self,
        material_id: str,
        predicted_price: Optional[float],
        confidence: float,
        rationale: str,
        generated_at: str,
    ) -> None:
        if not generated_at:
            raise ValueError("generated_at tidak boleh kosong.")
        self._material_id = material_id
        self._predicted_price = predicted_price
        self._confidence = confidence
        self._rationale = rationale
        self._requires_verification = True
        self._generated_at = generated_at

    @property
    def material_id(self) -> str:
        return self._material_id

    @property
    def predicted_price(self) -> Optional[float]:
        return self._predicted_price

    def generate_integrity_hash(self, secret_key: bytes) -> str:
        price_str = (
            str(round(self._predicted_price, 2))
            if self._predicted_price is not None
            else "none"
        )
        payload_bytes = f"{self._material_id}:{price_str}:{self._generated_at}".encode(
            "utf-8"
        )
        return hmac.new(secret_key, payload_bytes, hashlib.sha256).hexdigest()

    def to_output_format(self, secret_key: bytes) -> Dict[str, Any]:       
        return {
            "material_id": self._material_id,
            "predicted_price": (
                round(self._predicted_price, 2)
                if self._predicted_price is not None
                else None
            ),
            "confidence": round(self._confidence, 4),
            "rationale": self._rationale,
            "requires_verification": self._requires_verification,
            "generated_at": self._generated_at,
            "integrity_signature": self.generate_integrity_hash(secret_key),
        }


class AlternativeMaterialDomainModel:
    def __init__(
        self,
        alternative_material_id: Optional[str],
        cost_saving_pct: float,
        rationale: str,
        compatibility: CompatibilityLevel,
    ) -> None:
        self._alternative_material_id = alternative_material_id
        self._cost_saving_pct = cost_saving_pct
        self._rationale = rationale
        self._compatibility = compatibility

    def to_output_format(self) -> Dict[str, Any]:
        return {
            "alternative_material_id": self._alternative_material_id,
            "cost_saving_pct": round(self._cost_saving_pct, 4),
            "rationale": self._rationale,
            "compatibility": self._compatibility.value,
        }


class CostRiskDomainModel:
    def __init__(
        self,
        risk_type: str,
        probability: RiskProbability,
        impact: float,
        rationale: str,
    ) -> None:
        self._risk_type = risk_type
        self._probability = probability
        self._impact = impact
        self._rationale = rationale

    def to_output_format(self) -> Dict[str, Any]:
        return {
            "risk_type": self._risk_type,
            "probability": self._probability.value,
            "impact": round(self._impact, 2),
            "rationale": self._rationale,
        }


class AILayer:
    def __init__(
        self,
        secret_key: bytes,
        clock: Optional[Callable[[], datetime]] = None,
    ) -> None:
        if len(secret_key) < 32:
            raise ValueError(
                "Kunci rahasia kriptografi minimal harus berukuran 32 bytes."
            )
        self._read_only: bool = True
        self._secret_key: bytes = secret_key
        self._clock: Callable[[], datetime] = clock or (
            lambda: datetime.now(timezone.utc)
        )

    @property
    def is_read_only(self) -> bool:
        return self._read_only

    def predict_material_price(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        validated_dto = PricePredictionInputDTO(**payload)
        generated_at = self._clock().isoformat()

        domain_prediction = PricePredictionDomainModel(
            material_id=validated_dto.material_id,
            predicted_price=None,
            confidence=0.0,
            rationale="Model prediksi belum dilatih dengan data historis yang cukup.",
            generated_at=generated_at,
        )

        return domain_prediction.to_output_format(self._secret_key)

    def recommend_alternatives(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:        
        validated_dto = AlternativeRecommendationInputDTO(**payload)
        recommendations_pool: List[AlternativeMaterialDomainModel] = []
       
        domain_recommendation = AlternativeMaterialDomainModel(
            alternative_material_id=None,
            cost_saving_pct=0.0,
            rationale="Fitur rekomendasi akan diaktifkan setelah data supplier lengkap.",
            compatibility=CompatibilityLevel.UNVERIFIED,
        )
        recommendations_pool.append(domain_recommendation)

        return [item.to_output_format() for item in recommendations_pool]

    def identify_cost_risks(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:       
        validated_dto = CostRisksInputDTO(**payload)
        risks_pool: List[CostRiskDomainModel] = []
        
        domain_risk = CostRiskDomainModel(
            risk_type="DATA_INSUFFICIENT",
            probability=RiskProbability.LOW,
            impact=0.0,
            rationale="Belum cukup data proyek historis untuk analisis risiko.",
        )
        risks_pool.append(domain_risk)

        return [item.to_output_format() for item in risks_pool]