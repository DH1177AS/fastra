# fastra_core\knowledge\segment_calibration.py

from __future__ import annotations

import enum
import logging
import os
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("fastra.knowledge")

SEGMENT_FILE = r"D:\fastra_projects\Segment_Calibration.xlsx"


class CalibrationErrorCode(str, enum.Enum):
   
    CAL_001 = "CAL-001"  
    CAL_002 = "CAL-002" 


# ---------------------------------------------------------------------------
# Inbound & Outbound DTOs – Pydantic Strict Gateway (Fail-Fast)
# ---------------------------------------------------------------------------
class InboundSegmentRowDTO(BaseModel):
   
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    Segment: str = Field(..., min_length=2, max_length=64, pattern=r"^[A-Za-z0-9_\-\s]+$")
    WorkItem_Code: str = Field(..., min_length=2, max_length=32, pattern=r"^[A-Z0-9_\-\.]+$")
    Material_ID: Optional[str] = Field(default=None, max_length=64)
    Labor_ID: Optional[str] = Field(default=None, max_length=64)
    Equipment_ID: Optional[str] = Field(default=None, max_length=64)
    Coefficient_Override: Optional[float] = Field(default=None, gt=0.0, le=100000.0, allow_inf_nan=False)
    Price_Override: Optional[float] = Field(default=None, ge=0.0, le=1e12, allow_inf_nan=False)
    Waste_Override: float = Field(default=0.0, ge=0.0, le=1.0, allow_inf_nan=False)
    Source: str = Field(default="", max_length=256)


class OverrideItemDTO(BaseModel):
   
    model_config = ConfigDict(extra="forbid", strict=True)

    id: str = Field(..., min_length=5, max_length=64)
    coefficient: float = Field(..., gt=0.0, allow_inf_nan=False)
    price: float = Field(..., ge=0.0, allow_inf_nan=False)
    waste_factor: float = Field(default=1.0, ge=1.0, allow_inf_nan=False)
    source: str = Field(default="", max_length=256)


class SegmentOverrideContainerDTO(BaseModel):
   
    model_config = ConfigDict(extra="forbid", strict=True)

    materials: List[OverrideItemDTO] = Field(default_factory=list, max_length=100)
    labors: List[OverrideItemDTO] = Field(default_factory=list, max_length=100)
    equipments: List[OverrideItemDTO] = Field(default_factory=list, max_length=100)
    audit_check_price: Optional[float] = Field(default=None, ge=0.0, allow_inf_nan=False)


# ---------------------------------------------------------------------------
# Core Utilities – Jaminan Keamanan Type Casting
# ---------------------------------------------------------------------------
def _to_decimal(value: float | int | Decimal, field_name: str) -> Decimal:
    
    if isinstance(value, Decimal):
        return value
    if not isinstance(value, (int, float)):
        raise TypeError(f"Field '{field_name}' wajib bertipe numerik dasar (int/float/Decimal).")
    try:
        return Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"Field '{field_name}' gagal dikonversi ke representasi Decimal imutabel.") from exc


# ---------------------------------------------------------------------------
# Core Internal Calibration Reader & Calculations – Pure AHS (QS-Safe)
# ---------------------------------------------------------------------------
def load_segment_calibration(kg: Any) -> None:
   
    if not kg:
        logger.warning("KnowledgeGraph tidak valid untuk segment calibration.")
        return

    if not os.path.exists(SEGMENT_FILE):
        logger.info("File segment calibration tidak ditemukan, menggunakan override kosong.")
        kg.segment_overrides = {}
        return

    try:
        df = pd.read_excel(SEGMENT_FILE, sheet_name="Segment_Calibration")
    except Exception as exc:
        logger.warning("Gagal membaca file segment calibration: %s", exc)
        kg.segment_overrides = {}
        return
   
    raw_overrides: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(
        lambda: defaultdict(
            lambda: {
                "materials": [],
                "labors": [],
                "equipments": [],
                "audit_check_price": None,
            }
        )
    )

    for _, row in df.iterrows():
        segment_raw = row.get("Segment")
        wi_code_raw = row.get("WorkItem_Code")

        if pd.isna(segment_raw) or pd.isna(wi_code_raw):
            continue

        segment_str = str(segment_raw).strip()
        wi_code_str = str(wi_code_raw).strip()
        if not segment_str or not wi_code_str:
            continue
       
        coeff_raw = row.get("Coefficient_Override")
        price_raw = row.get("Price_Override")
        waste_raw = row.get("Waste_Override")

        row_payload = {
            "Segment": segment_str,
            "WorkItem_Code": wi_code_str,
            "Material_ID": str(row.get("Material_ID")).strip() if pd.notna(row.get("Material_ID")) else None,
            "Labor_ID": str(row.get("Labor_ID")).strip() if pd.notna(row.get("Labor_ID")) else None,
            "Equipment_ID": str(row.get("Equipment_ID")).strip() if pd.notna(row.get("Equipment_ID")) else None,
            "Coefficient_Override": float(coeff_raw) if pd.notna(coeff_raw) else None,
            "Price_Override": float(price_raw) if pd.notna(price_raw) else None,
            "Waste_Override": float(waste_raw) if pd.notna(waste_raw) else 0.0,
            "Source": str(row.get("Source", "")).strip(),
        }
       
        try:
            validated_row = InboundSegmentRowDTO.model_validate(row_payload)
        except Exception as exc:
            logger.debug("Baris segment calibration tidak valid, dilewati: %s", exc)
            continue

        target_node = raw_overrides[validated_row.Segment][validated_row.WorkItem_Code]
        
        if validated_row.Material_ID and validated_row.Material_ID.upper() == "AUDIT-CHECK":
            if validated_row.Price_Override is not None:
                price_dec = _to_decimal(validated_row.Price_Override, "audit_check_price")
                target_node["audit_check_price"] = float(price_dec)
            continue

        if validated_row.Coefficient_Override is None or validated_row.Price_Override is None:
            continue

        coeff_dec = _to_decimal(validated_row.Coefficient_Override, "coeff")
        price_dec = _to_decimal(validated_row.Price_Override, "price")
        
        waste_extra_dec = _to_decimal(validated_row.Waste_Override, "waste_extra")
        waste_factor_dec = Decimal("1.0000") + waste_extra_dec
       
        if validated_row.Material_ID:
            mat_item = {
                "id": validated_row.Material_ID,
                "coefficient": float(coeff_dec),
                "price": float(price_dec),
                "waste_factor": float(waste_factor_dec),
                "source": validated_row.Source,
            }
            try:
                target_node["materials"].append(OverrideItemDTO.model_validate(mat_item).model_dump())
            except Exception as exc:
                logger.warning("Material override tidak valid untuk %s: %s", wi_code_str, exc)

        elif validated_row.Labor_ID:
            lab_item = {
                "id": validated_row.Labor_ID,
                "coefficient": float(coeff_dec),
                "price": float(price_dec),
                "source": validated_row.Source,
            }
            try:
                target_node["labors"].append(OverrideItemDTO.model_validate(lab_item).model_dump())
            except Exception as exc:
                logger.warning("Labor override tidak valid untuk %s: %s", wi_code_str, exc)

        elif validated_row.Equipment_ID:
            eqp_item = {
                "id": validated_row.Equipment_ID,
                "coefficient": float(coeff_dec),
                "price": float(price_dec),
                "source": validated_row.Source,
            }
            try:
                target_node["equipments"].append(OverrideItemDTO.model_validate(eqp_item).model_dump())
            except Exception as exc:
                logger.warning("Equipment override tidak valid untuk %s: %s", wi_code_str, exc)
   
    final_overrides: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for seg_key, wi_dict in raw_overrides.items():
        final_overrides[seg_key] = {}
        for wi_key, raw_node in wi_dict.items():
            try:
                validated_container = SegmentOverrideContainerDTO.model_validate(raw_node)
                final_overrides[seg_key][wi_key] = validated_container.model_dump()
            except Exception as exc:
                logger.warning("Container override tidak valid untuk %s/%s: %s", seg_key, wi_key, exc)

    kg.segment_overrides = final_overrides
    logger.info(
        "Segment calibration berhasil dimuat: %d segmen, %d work item.",
        len(final_overrides),
        sum(len(v) for v in final_overrides.values()),
    )


def calculate_unit_price_from_override(override: Dict[str, Any]) -> Dict[str, Any]:
    
    try:
        validated_override = SegmentOverrideContainerDTO.model_validate(override)
    except Exception as exc:
        raise ValueError(f"Override container tidak valid: {exc}") from exc

    material_cost = Decimal("0.0000")
    labor_cost = Decimal("0.0000")
    equipment_cost = Decimal("0.0000")

    material_breakdown: List[Dict[str, Any]] = []
    labor_breakdown: List[Dict[str, Any]] = []
    equipment_breakdown: List[Dict[str, Any]] = []

    # ---------------------------------------------------------------------------
    # KOMPONEN OVERRIDE MATERIAL PIPELINE
    # ---------------------------------------------------------------------------
    for m in validated_override.materials:
        coef_dec = _to_decimal(m.coefficient, "material.coefficient")
        price_dec = _to_decimal(m.price, "material.price")
        waste_dec = _to_decimal(m.waste_factor, "material.waste_factor")

        # Rumus Komponen Bahan: Koefisien * Harga Satuan * Faktor Pemborosan
        cost_val = coef_dec * price_dec * waste_dec
        material_cost += cost_val

        material_breakdown.append({
            "material_id": m.id,
            "coefficient": float(coef_dec),
            "waste_factor": float(waste_dec),
            "unit_price": float(price_dec),
            "cost": float(cost_val.quantize(Decimal("0.0001"))),
            "price_source": m.source,
        })

    # ---------------------------------------------------------------------------
    # KOMPONEN OVERRIDE UPAH TENAGA KERJA PIPELINE
    # ---------------------------------------------------------------------------
    for l in validated_override.labors:
        coef_dec = _to_decimal(l.coefficient, "labor.coefficient")
        price_dec = _to_decimal(l.price, "labor.price")

        # Rumus Komponen Upah: Koefisien * Tarif Harian Orang Hari
        cost_val = coef_dec * price_dec
        labor_cost += cost_val

        labor_breakdown.append({
            "labor_id": l.id,
            "coefficient": float(coef_dec),
            "daily_rate": float(price_dec),
            "cost": float(cost_val.quantize(Decimal("0.0001"))),
            "wage_source": l.source,
        })

    # ---------------------------------------------------------------------------
    # KOMPONEN OVERRIDE SEWA PERALATAN MEKANIKAL PIPELINE
    # ---------------------------------------------------------------------------
    for e in validated_override.equipments:
        coef_dec = _to_decimal(e.coefficient, "equipment.coefficient")
        price_dec = _to_decimal(e.price, "equipment.price")

        # Rumus Komponen Alat: Koefisien * Tarif Sewa Alat per Jam/Hari
        cost_val = coef_dec * price_dec
        equipment_cost += cost_val

        equipment_breakdown.append({
            "equipment_id": e.id,
            "coefficient": float(coef_dec),
            "rate": float(price_dec),
            "cost": float(cost_val.quantize(Decimal("0.0001"))),
            "equipment_source": e.source,
        })

    total_sum_val = material_cost + labor_cost + equipment_cost

    return {
        "unit_price": float(total_sum_val.quantize(Decimal("0.01"))),
        "material_cost": float(material_cost.quantize(Decimal("0.01"))),
        "labor_cost": float(labor_cost.quantize(Decimal("0.01"))),
        "equipment_cost": float(equipment_cost.quantize(Decimal("0.01"))),
        "material_breakdown": material_breakdown,
        "labor_breakdown": labor_breakdown,
        "equipment_breakdown": equipment_breakdown,
        "errors": [],
    }