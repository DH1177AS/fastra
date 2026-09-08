# historical.py - ACES-300 Layer 6: Historical Layer
# Template untuk data proyek historis

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

@dataclass
class HistoricalProject:
    """Data proyek yang telah selesai untuk analisis tren."""
    project_name: str = ""
    location: str = ""
    building_type: str = "HOUSE"
    total_area: float = 0.0
    contract_value: float = 0.0
    actual_cost: float = 0.0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    duration_planned_days: int = 0
    duration_actual_days: int = 0
    cost_overrun_percentage: float = 0.0
    material_cost_actual: Dict = field(default_factory=dict)
    labor_cost_actual: Dict = field(default_factory=dict)
    productivity_actual: Dict = field(default_factory=dict)

@dataclass
class HistoricalPriceTrend:
    """Data tren harga material per kuartal."""
    material_name: str = ""
    unit: str = ""
    q1_2024: float = 0.0
    q2_2024: float = 0.0
    q3_2024: float = 0.0
    q4_2024: float = 0.0
    q1_2025: float = 0.0
    q2_2025: float = 0.0

# Sample data tren harga sesuai ACES-300 Section 11.3
SAMPLE_PRICE_TRENDS = [
    HistoricalPriceTrend("Semen (sak)", "sak", 58000, 58500, 60000, 62000, 63000, 63500),
    HistoricalPriceTrend("Baja Ringan (batang)", "batang", 75000, 76000, 78000, 80000, 82000, 81000),
    HistoricalPriceTrend("Besi D10 (batang)", "batang", 110000, 112000, 115000, 118000, 120000, 119000),
    HistoricalPriceTrend("Genteng Beton (buah)", "buah", 6000, 6000, 6200, 6500, 6500, 6800),
]
# fastra_core\ccm\historical.py

from __future__ import annotations

import enum
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class BuildingType(str, enum.Enum):
   
    HOUSE = "HOUSE"
    OFFICE = "OFFICE"
    WAREHOUSE = "WAREHOUSE"
    HIGH_RISE = "HIGH_RISE"
    INFRASTRUCTURE = "INFRASTRUCTURE"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Gateway & Sanitization (Fail-Fast)
# ---------------------------------------------------------------------------
class HistoricalProjectInboundDTO(BaseModel):
  
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
    )

    project_name: str = Field(..., min_length=2, max_length=256)
    location: str = Field(..., min_length=2, max_length=256)
    building_type: BuildingType = Field(default=BuildingType.HOUSE)
    total_area: float = Field(..., gt=0.0, le=1e7, allow_inf_nan=False)
    contract_value: float = Field(..., ge=0.0, le=1e15, allow_inf_nan=False)
    actual_cost: float = Field(..., ge=0.0, le=1e15, allow_inf_nan=False)
    start_date: str = Field(
        ..., min_length=10, max_length=10, pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    end_date: str = Field(
        ..., min_length=10, max_length=10, pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    duration_planned_days: int = Field(..., gt=0, le=10000)
    duration_actual_days: int = Field(..., gt=0, le=10000)
    material_cost_actual: Dict[str, float] = Field(
        default_factory=dict, max_length=1000
    )
    labor_cost_actual: Dict[str, float] = Field(default_factory=dict, max_length=1000)
    productivity_actual: Dict[str, float] = Field(
        default_factory=dict, max_length=1000
    )

    @field_validator(
        "material_cost_actual", "labor_cost_actual", "productivity_actual",
        mode="after",
    )
    @classmethod
    def validate_metrics_dictionary(
        cls, value: Dict[str, float]
    ) -> Dict[str, float]:
       
        for k, v in value.items():
            if not k.strip():
                raise ValueError(
                    "Identifikasi kunci metrik dalam kamus tidak boleh berupa spasi kosong."
                )
            if not isinstance(v, (int, float)) or v < 0.0:
                raise ValueError(
                    "Nilai komponen analisis numerik tidak boleh bernilai negatif."
                )
        return value

    @model_validator(mode="after")
    def validate_date_order(self) -> "HistoricalProjectInboundDTO":
        
        if self.start_date > self.end_date:
            raise ValueError(
                "Urutan kronologis salah: tanggal mulai tidak boleh melewati tanggal selesai."
            )
        return self


class HistoricalPriceTrendInboundDTO(BaseModel):
    
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
    )

    material_name: str = Field(..., min_length=2, max_length=128)
    unit: str = Field(
        ..., min_length=1, max_length=16, pattern=r"^[A-Za-z0-9²³\/()\s]+$"
    )
    q1_2024: float = Field(..., gt=0.0, le=1e9, allow_inf_nan=False)
    q2_2024: float = Field(..., gt=0.0, le=1e9, allow_inf_nan=False)
    q3_2024: float = Field(..., gt=0.0, le=1e9, allow_inf_nan=False)
    q4_2024: float = Field(..., gt=0.0, le=1e9, allow_inf_nan=False)
    q1_2025: float = Field(..., gt=0.0, le=1e9, allow_inf_nan=False)
    q2_2025: float = Field(..., gt=0.0, le=1e9, allow_inf_nan=False)


# ---------------------------------------------------------------------------
# Core Utilities – Jaminan Keamanan Type Casting
# ---------------------------------------------------------------------------
def _to_decimal(value: float | int, field_name: str) -> Decimal:
    
    if not isinstance(value, (int, float)):
        raise TypeError(f"Field '{field_name}' wajib bertipe numerik dasar (int/float).")
    try:
        return Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(
            f"Field '{field_name}' gagal dikonversi ke representasi Decimal."
        ) from exc


# ---------------------------------------------------------------------------
# Domain Models – Pure Business & Historical Logical Invariants
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Data Sampel Validasi Tren – ACES-300 Seksi 11.3 Compliance
# ---------------------------------------------------------------------------
SAMPLE_PRICE_TRENDS: List[HistoricalPriceTrend] = [
    HistoricalPriceTrend(
        "Semen (sak)", "sak", 58000.0, 58500.0, 60000.0, 62000.0, 63000.0, 63500.0
    ),
    HistoricalPriceTrend(
        "Baja Ringan (batang)", "batang", 75000.0, 76000.0, 78000.0, 80000.0, 82000.0, 81000.0
    ),
    HistoricalPriceTrend(
        "Besi D10 (batang)", "batang", 110000.0, 112000.0, 115000.0, 118000.0, 120000.0, 119000.0
    ),
    HistoricalPriceTrend(
        "Genteng Beton (buah)", "buah", 6000.0, 6000.0, 6200.0, 6500.0, 6500.0, 6800.0
    ),
]
