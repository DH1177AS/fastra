# fastra_core\knowledge\integrasi_relasi_sni.py

from __future__ import annotations

import enum
import logging
import os
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from fastra_core.knowledge.edges import MaterialRequirement, LaborRequirement, EquipmentRequirement
from fastra_core.knowledge.graph import KnowledgeGraph

logger = logging.getLogger("fastra.knowledge")

SNI_RELATION_PATH = os.environ.get(
    "FASTRA_SNI_RELATION_PATH",
    r"D:\fastra_projects\Database_Relasi_SNI.xlsx"
)


class SNIComponentType(str, enum.Enum):
  
    BAHAN = "BAHAN"
    TENAGA = "TENAGA"
    ALAT = "ALAT"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Gateway & Sanitization (Fail-Fast)
# ---------------------------------------------------------------------------

class SNIRelationRowDTO(BaseModel):
   
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    work_item_id: str = Field(..., min_length=5, max_length=64, pattern=r"^wi_[a-z0-9_]+$")
    sni_code: str = Field(..., min_length=2, max_length=64, pattern=r"^[A-Z0-9_\-\.\:\s\/]+$")
    component_type: SNIComponentType = Field(...)
    resource_id: str = Field(..., min_length=5, max_length=64, pattern=r"^(mat|lab|eqp)_[a-z0-9_]+$")
    coefficient: float = Field(..., gt=0.0, le=100000.0, allow_inf_nan=False)
    waste_factor: float = Field(default=1.0, ge=1.0, le=2.0, allow_inf_nan=False)
    source: str = Field(default="SNI_PUPR_GENERIC", max_length=256)


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
# Core Internal Spreadsheet Reader & Mapping Logic – Pure AHSP (QS-Safe)
# ---------------------------------------------------------------------------

def _load_sni_data() -> Optional[List[Dict[str, Any]]]:
   
    if not os.path.exists(SNI_RELATION_PATH):
        logger.warning("Berkas fisik relasi indeks SNI tidak ditemukan di jalur: %s", SNI_RELATION_PATH)
        return None

    try:
        df = pd.read_excel(SNI_RELATION_PATH, sheet_name="Relasi SNI", header=0)
        cleaned_records: List[Dict[str, Any]] = []
        
        for _, row in df.iterrows():
            wi_id_raw = row.get("work_item_id")
            sni_code_raw = row.get("sni_code")
            comp_type_raw = row.get("component_type")
            res_id_raw = row.get("resource_id")
            coef_raw = row.get("coefficient")
            
            if pd.isna(wi_id_raw) or pd.isna(sni_code_raw) or pd.isna(comp_type_raw) or pd.isna(res_id_raw) or pd.isna(coef_raw):
                continue

            waste_raw = row.get("waste_factor", 1.0)
            
            row_payload = {
                "work_item_id": str(wi_id_raw).strip(),
                "sni_code": str(sni_code_raw).strip(),
                "component_type": str(comp_type_raw).strip().upper(),
                "resource_id": str(res_id_raw).strip(),
                "coefficient": float(coef_raw) if isinstance(coef_raw, (int, float)) else 0.0,
                "waste_factor": float(waste_raw) if isinstance(waste_raw, (int, float)) else 1.0,
                "source": str(row.get("source", "SNI_PUPR_EXCEL")).strip()
            }

            try:
               
                validated_row = SNIRelationRowDTO.model_validate(row_payload)
                cleaned_records.append(validated_row.model_dump())
            except Exception as exc:
                logger.warning("Baris relasi SNI tidak valid dilewati: %s", exc)
                continue

        return cleaned_records
    except Exception as e:
        logger.error("Gagal melakukan pembacaan dokumen spreadsheet SNI: %s", str(e))
        return None


def integrasikan_relasi_sni(kg: KnowledgeGraph) -> KnowledgeGraph:
   
    if not isinstance(kg, KnowledgeGraph):
        raise TypeError("Parameter masukan 'kg' wajib berupa instance orisinil dari kelas KnowledgeGraph.")

    sni_data = _load_sni_data()

    if not sni_data:
        logger.warning("Tidak ditemukan data relasi SNI yang valid untuk diintegrasikan ke jaringan.")
        return kg
    
    if not hasattr(kg, "sni_relations"):
        kg.sni_relations = []
   
    for item in sni_data:
       
        dto = SNIRelationRowDTO.model_validate(item)
        
        wi_id_str = dto.work_item_id
        coef_dec = _to_decimal(dto.coefficient, "sni.coefficient")
        waste_dec = _to_decimal(dto.waste_factor, "sni.waste_factor")
       
        if dto.component_type == SNIComponentType.BAHAN:
            mat_req = MaterialRequirement(
                material_id=dto.resource_id,
                coefficient=float(coef_dec),
                waste_factor=float(waste_dec),
                source=f"Juknis SNI ({dto.sni_code})"
            )
            kg.add_material_requirement(wi_id_str, mat_req)

        elif dto.component_type == SNIComponentType.TENAGA:
            lab_req = LaborRequirement(
                labor_id=dto.resource_id,
                coefficient=float(coef_dec),
                source=f"Juknis SNI ({dto.sni_code})"
            )
            kg.add_labor_requirement(wi_id_str, lab_req)

        elif dto.component_type == SNIComponentType.ALAT:
            eqp_req = EquipmentRequirement(
                equipment_id=dto.resource_id,
                coefficient=float(coef_dec),
                source=f"Juknis SNI ({dto.sni_code})"
            )
            kg.add_equipment_requirement(wi_id_str, eqp_req)

        # Simpan jejak audit manifes mentah relasi ke dalam ledger log
        kg.sni_relations.append(dto.model_dump())

    logger.info("Relasi indeks juknis SNI nasional sukses dirajut: %d entri aktif dikunci.", len(sni_data))
    return kg
