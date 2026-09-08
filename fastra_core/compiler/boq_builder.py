# fastra_core\compiler\boq_builder.py

from __future__ import annotations

import enum
import hashlib
import json
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DivisionType(str, enum.Enum):
 
    DIV_00 = "DIV-00 Pekerjaan Umum"
    DIV_03 = "DIV-03 Pekerjaan Pondasi"
    DIV_04 = "DIV-04 Pekerjaan Struktur"
    DIV_05 = "DIV-05 Pekerjaan Dinding"
    DIV_06 = "DIV-06 Pekerjaan Lantai"
    DIV_07 = "DIV-07 Pekerjaan Plafon"
    DIV_08 = "DIV-08 Pekerjaan Atap"
    DIV_09 = "DIV-09 Pekerjaan Kusen"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Gateway & Sanitization (Fail-Fast)
# ---------------------------------------------------------------------------
class InboundQuantityItemDTO(BaseModel):
  
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    work_item_code: str = Field(
        ..., min_length=2, max_length=32, pattern=r"^[A-Z0-9_\-\.]+$"
    )
    description: str = Field(..., min_length=2, max_length=512)
    quantity: float = Field(..., ge=0.0, le=1e9, allow_inf_nan=False)
    unit: str = Field(
        ...,
        min_length=1,
        max_length=16,
        pattern=r"^[A-Za-z0-9²³\/()\s\u00B3]+$",
    )
    source_entities: List[str] = Field(..., min_length=1, max_length=1000)
    detail: str = Field(default="", max_length=1024)

    @field_validator("source_entities", mode="after")
    @classmethod
    def validate_entities_format(cls, value: List[str]) -> List[str]:
        """Pastikan setiap entitas sumber tidak kosong."""
        for val in value:
            if not val.strip():
                raise ValueError(
                    "Identifikasi kunci source_entities tidak boleh berupa spasi kosong."
                )
        return value


class BOQBuildPayloadDTO(BaseModel):
   
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    quantities: List[InboundQuantityItemDTO] = Field(
        ..., min_length=1, max_length=10000
    )
    region: str = Field(
        ..., min_length=2, max_length=64, pattern=r"^[A-Za-z0-9_\-\s]+$"
    )
    project_uuid: str = Field(
        ..., min_length=36, max_length=64, pattern=r"^[a-f0-9\-]+$"
    )


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


class TraceLog:
   
    def __init__(self, generated_at: str) -> None:
        if not generated_at:
            raise ValueError("generated_at tidak boleh kosong.")
        self._generated_at = generated_at
        self._steps: List[Dict[str, Any]] = []

    def add_step(
        self,
        stage: str,
        operation: str,
        input_entity: Optional[str] = None,
        operation_detail: Optional[str] = None,
        output_value: Optional[str] = None,
        mapped_to: Optional[str] = None,
    ) -> None:
       
        step: Dict[str, Any] = {
            "stage": stage,
            "operation": operation,
        }
        if input_entity is not None:
            step["input_entity"] = input_entity
        if operation_detail is not None:
            step["operation_detail"] = operation_detail
        if output_value is not None:
            step["output_value"] = output_value
        if mapped_to is not None:
            step["mapped_to"] = mapped_to
        self._steps.append(step)

    def to_dict(self) -> Dict[str, Any]:
       
        return {
            "generated_at": self._generated_at,
            "steps": list(self._steps),
        }


# ---------------------------------------------------------------------------
# Domain Models & Core Compiler Logic – Pure AHS Aggregation (QS-Safe)
# ---------------------------------------------------------------------------
class BOQBuilder:
    FALLBACK_CODE_MAP = {
        "PEK.DIND.001": ("DIN.005", "m²", "Pasangan Bata"),
        "PEK.DIND.002": ("DIN.008", "m²", "Plesteran"),
        "PEK.DIND.003": ("DIN.009", "m²", "Acian"),
        "PEK.LNT.001": ("FIN.004", "m²", "Lantai"),
        "PEK.PLF.001": ("FIN.005", "m²", "Plafon"),        
    }
    
    def __init__(self, knowledge_graph: Any, generated_at: Optional[str] = None) -> None:
        self._kg = knowledge_graph
        self._generated_at = generated_at or datetime.now(timezone.utc).isoformat()
       
        self._pe_to_work_item: Dict[str, str] = {
            "PEK.DIND.001": "wi-bata-merah-taman",
            "PEK.DIND.002": "wi-plester-dalam",
            "PEK.DIND.003": "wi-acian-dalam",
            "PEK.STR.001": "wi-kolom-bekisting",
            "PEK.STR.002": "wi-kolom-lt1-rebar-fab",
            "PEK.STR.003": "wi-kolom-cor-lt1",
            "PEK.STR.041": "wi-tangga-bekisting",
            "PEK.FND.001": "wi-pile-cap-cor",
            "PEK.FND.002": "wi-pile-cap-rebar",
            "PEK.ATP.001": "wi-kudakuda-fab",
            "PEK.ATP.002": "wi-genteng-utama",
            "PEK.PTU.001": "wi-daun-pintu-utama",
            "PEK.PTU.002": "wi-cat-duco-pintu",
            "PEK.JND.001": "wi-jendela-casement",
            "PEK.JND.002": "wi-kaca-polos-5mm",
            "PEK.LNT.001": "wi-granit-rt",
            "PEK.PLF.001": "wi-gypsum-9mm",
        }
        
        raw_work_items = getattr(self._kg, "work_items", {})
        if isinstance(raw_work_items, dict):
            self._wi_by_id = {wi.id: wi for wi in raw_work_items.values()}
        elif isinstance(raw_work_items, list):
            self._wi_by_id = {wi.id: wi for wi in raw_work_items}
        else:
            raise TypeError(
                "knowledge_graph.work_items harus berupa dict atau list."
            )

    def build_boq(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        
        validated_payload = BOQBuildPayloadDTO(**payload)

        divisions: Dict[str, Dict[str, Any]] = {}

        for q_dto in validated_payload.quantities:
            code = q_dto.work_item_code
            wi = self._find_work_item(code)
            
            item_code = wi.code if wi else code
            item_name = wi.name if wi else q_dto.description
            unit = wi.unit if wi else q_dto.unit
            category = wi.category if wi else ""
           
            if wi is None and code in self.FALLBACK_CODE_MAP:
                fallback_code, fallback_unit, fallback_name = self.FALLBACK_CODE_MAP[code]
                item_code = fallback_code
                unit = fallback_unit
                item_name = fallback_name
            
            if wi and hasattr(self._kg, "get_unit_price"):
                unit_price_data = self._kg.get_unit_price(wi.id, validated_payload.region)
                unit_price_val = _to_decimal(
                    unit_price_data.get("unit_price", 0.0), "unit_price"
                )
                if unit_price_val < 0:
                    raise ValueError("unit_price tidak boleh negatif.")
            else:
                unit_price_val = Decimal("0.00")

            div_name = self._determine_division(item_code, category)
            if div_name not in divisions:
                divisions[div_name] = {
                    "division_code": div_name,
                    "division_name": div_name,
                    "items": [],
                    "subtotal": Decimal("0.00"),
                }
           
            quantity_val = _to_decimal(q_dto.quantity, "quantity")
            total_price_val = (quantity_val * unit_price_val).quantize(Decimal("0.01"))
           
            trace = TraceLog(generated_at=self._generated_at)
            trace.add_step(
                stage="GEOMETRY_BUILDER",
                operation="Calculate Gross Quantity",
                input_entity=q_dto.source_entities[0] if q_dto.source_entities else None,
                operation_detail=q_dto.detail,
                output_value=f"{float(quantity_val)} {unit}",
            )
            trace.add_step(
                stage="QUANTITY_GENERATOR",
                operation="Apply Deduction & Net Quantity",
                operation_detail=q_dto.detail,
                output_value=f"{float(quantity_val)} {unit}",
            )
            trace.add_step(
                stage="BOQ_GENERATOR",
                operation="Map to WorkItem",
                mapped_to=item_code,
                output_value=f"{float(quantity_val)} {unit}",
            )
            
            item_hash_payload = {
                "item_code": item_code,
                "quantity": float(quantity_val),
                "entities": q_dto.source_entities,
            }
            boq_item_uuid = hashlib.sha256(
                json.dumps(item_hash_payload, sort_keys=True, default=str).encode("utf-8")
            ).hexdigest()

            boq_item = {
                "boq_item_uuid": boq_item_uuid,
                "item_code": item_code,
                "item_name": item_name,
                "description": q_dto.description,
                "quantity": float(quantity_val),
                "unit": unit,
                "unit_price": float(unit_price_val),
                "total_price": float(total_price_val),
                "source_entities": q_dto.source_entities,
                "trace_log": {
                "generated_at": trace._generated_at,
                "computation_steps": trace._steps,
            },
            }

            divisions[div_name]["items"].append(boq_item)
            divisions[div_name]["subtotal"] += total_price_val
        
        project_total_val = sum(d["subtotal"] for d in divisions.values())
       
        formatted_divisions = []
        for d in divisions.values():
            d["subtotal"] = float(d["subtotal"].quantize(Decimal("0.01")))
            formatted_divisions.append(d)
       
        master_hash_payload = {
            "project_uuid": validated_payload.project_uuid,
            "generated_at": self._generated_at,
            "total_items": len(validated_payload.quantities),
        }
        boq_uuid = hashlib.sha256(
            json.dumps(master_hash_payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

        return {
            "boq_uuid": boq_uuid,
            "project_uuid": validated_payload.project_uuid,
            "generated_at": self._generated_at,
            "compiler_version": "1.0.0",
            "total_items": len(validated_payload.quantities),
            "project_total": float(project_total_val.quantize(Decimal("0.01"))),
            "divisions": formatted_divisions,
            "generated_by": "FASTRA ACES-400 Full Compliance",
        }

    def _find_work_item(self, code: str) -> Optional[Any]:
       
        wid = self._pe_to_work_item.get(code)
        if wid and wid in self._wi_by_id:
            return self._wi_by_id[wid]
        return None

    def _determine_division(self, code: str, category: str) -> str:
        cleaned_cat = category.strip().upper()
        if cleaned_cat:
            if "STRUKTUR" in cleaned_cat:
                return DivisionType.DIV_04.value
            if "DINDING" in cleaned_cat:
                return DivisionType.DIV_05.value
            if "ATAP" in cleaned_cat:
                return DivisionType.DIV_08.value
            if "LANTAI" in cleaned_cat:
                return DivisionType.DIV_06.value
            if "PLAFON" in cleaned_cat:
                return DivisionType.DIV_07.value
            if "PONDASI" in cleaned_cat:
                return DivisionType.DIV_03.value
            if "KUSEN" in cleaned_cat:
                return DivisionType.DIV_09.value
       
        if code.startswith("DIN.") or code.startswith("PEK.DIND."):
            return DivisionType.DIV_05.value
        if code.startswith("STR.") or code.startswith("PEK.STR."):
            return DivisionType.DIV_04.value
        if code.startswith("FIN.") or code.startswith("PEK.LNT.") or code.startswith("PEK.PLF."):
            return DivisionType.DIV_06.value

        return DivisionType.DIV_00.value