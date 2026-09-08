# fastra_core\knowledge\edges.py

from __future__ import annotations

import enum
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Gateway & Sanitization (Fail-Fast)
# ---------------------------------------------------------------------------

class MaterialRequirementInboundDTO(BaseModel):
   
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    material_id: str = Field(..., min_length=5, max_length=64, pattern=r"^mat_[a-z0-9_]+$")
    coefficient: float = Field(..., gt=0.0, le=100000.0, allow_inf_nan=False)
    waste_factor: float = Field(default=1.0, ge=1.0, le=2.0, allow_inf_nan=False)
    source: str = Field(default="", max_length=256)


class LaborRequirementInboundDTO(BaseModel):
   
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    labor_id: str = Field(..., min_length=5, max_length=64, pattern=r"^lab_[a-z0-9_]+$")
    coefficient: float = Field(..., gt=0.0, le=1000.0, allow_inf_nan=False)
    source: str = Field(default="", max_length=256)


class EquipmentRequirementInboundDTO(BaseModel):
   
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    equipment_id: str = Field(..., min_length=5, max_length=64, pattern=r"^eqp_[a-z0-9_]+$")
    coefficient: float = Field(..., gt=0.0, le=1000.0, allow_inf_nan=False)
    source: str = Field(default="", max_length=256)


class PriceRecordInboundDTO(BaseModel):
   
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    material_id: str = Field(..., min_length=5, max_length=64, pattern=r"^mat_[a-z0-9_]+$")
    price: float = Field(..., gt=0.0, le=1e12, allow_inf_nan=False)
    region: str = Field(..., min_length=2, max_length=64, pattern=r"^[A-Z0-9_\-\s]+$")
    valid_from: str = Field(..., min_length=10, max_length=10, pattern=r"^\d{4}-\d{2}-\d{2}$")
    valid_until: Optional[str] = Field(default=None, min_length=10, max_length=10, pattern=r"^\d{4}-\d{2}-\d{2}$")
    supplier_id: Optional[str] = Field(default=None, min_length=5, max_length=64, pattern=r"^spl_[a-z0-9_]+$")
    source: str = Field(default="", max_length=256)

    @field_validator("valid_until", mode="after")
    @classmethod
    def validate_date_sequence(cls, value: Optional[str], info: Any) -> Optional[str]:
        if value is not None:
            valid_from = info.data.get("valid_from")
            if valid_from and valid_from > value:
                raise ValueError("Kronologi salah: Batas tanggal valid_from dilarang melewati batas tanggal valid_until.")
        return value


# ---------------------------------------------------------------------------
# Core Utilities – Jaminan Keamanan Type Casting
# ---------------------------------------------------------------------------

def _to_decimal(value: float | int, field_name: str) -> Decimal:
    
    if not isinstance(value, (int, float)):
        raise TypeError(f"Field '{field_name}' wajib bertipe numerik dasar (int/float).")
    try:
        return Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"Field '{field_name}' gagal dikonversi ke representasi Decimal.") from exc

# ---------------------------------------------------------------------------
# Domain Models – Pure Business & AHSP Index Logical Invariants
# ---------------------------------------------------------------------------

class MaterialRequirement:
   
    def __init__(
        self,
        material_id: str,
        coefficient: float,
        waste_factor: float = 1.0,
        source: str = ""
    ) -> None:
        if not material_id.strip():
            raise ValueError("Parameter material_id tidak boleh kosong.")
        if coefficient <= 0.0:
            raise ValueError("Nilai indeks koefisien kebutuhan material harus positif (> 0).")
        if waste_factor < 1.0 or waste_factor > 2.0:
            raise ValueError("Parameter batas waste_factor melanggar toleransi sisa material sipil (1.0 - 2.0).")

        self._material_id = material_id.strip()
        self._coefficient = _to_decimal(coefficient, "coefficient")
        self._waste_factor = _to_decimal(waste_factor, "waste_factor")
        self._source = source.strip()

    @property
    def material_id(self) -> str:
        return self._material_id

    @property
    def coefficient(self) -> Decimal:
        return self._coefficient

    @property
    def waste_factor(self) -> Decimal:
        return self._waste_factor

    def calculate_gross_requirement(self, net_volume: Decimal) -> Decimal:
       
        if net_volume < Decimal("0"):
            raise ValueError("Kuantitas volume bersih penampang (net_volume) dilarang bernilai negatif.")
        gross_req = net_volume * self._coefficient * self._waste_factor
        return gross_req.quantize(Decimal("0.0001"))

    def to_domain_state(self) -> Dict[str, Any]:
        return {
            "material_id": self._material_id,
            "coefficient": float(self._coefficient),
            "waste_factor": float(self._waste_factor),
            "source": self._source
        }


class LaborRequirement:
   
    def __init__(
        self,
        labor_id: str,
        coefficient: float,
        source: str = ""
    ) -> None:
        if not labor_id.strip():
            raise ValueError("Parameter labor_id wajib terisi.")
        if coefficient < 0.0:
            raise ValueError("Nilai indeks indeks produktivitas tenaga kerja tidak boleh negatif.")

        self._labor_id = labor_id.strip()
        self._coefficient = _to_decimal(coefficient, "coefficient")
        self._source = source.strip()

    @property
    def labor_id(self) -> str:
        return self._labor_id

    @property
    def coefficient(self) -> Decimal:
        return self._coefficient

    def calculate_total_man_hours(self, total_volume: Decimal) -> Decimal:
       
        if total_volume < Decimal("0"):
            raise ValueError("Kuantitas volume pekerjaan dilarang bernilai negatif.")
        return (total_volume * self._coefficient).quantize(Decimal("0.01"))

    def to_domain_state(self) -> Dict[str, Any]:
        return {
            "labor_id": self._labor_id,
            "coefficient": float(self._coefficient),
            "source": self._source
        }


class EquipmentRequirement:
  
    def __init__(
        self,
        equipment_id: str,
        coefficient: float,
        source: str = ""
    ) -> None:
        if not equipment_id.strip():
            raise ValueError("Parameter equipment_id tidak boleh kosong.")
        if coefficient < 0.0:
            raise ValueError("Nilai indeks koefisien durasi alat berat tidak boleh negatif.")

        self._equipment_id = equipment_id.strip()
        self._coefficient = _to_decimal(coefficient, "coefficient")
        self._source = source.strip()

    @property
    def equipment_id(self) -> str:
        return self._equipment_id

    @property
    def coefficient(self) -> Decimal:
        return self._coefficient

    def calculate_total_machine_hours(self, total_volume: Decimal) -> Decimal:
       
        if total_volume < Decimal("0"):
            raise ValueError("Kuantitas volume elemen penampang dilarang bernilai negatif.")
        return (total_volume * self._coefficient).quantize(Decimal("0.01"))

    def to_domain_state(self) -> Dict[str, Any]:
        return {
            "equipment_id": self._equipment_id,
            "coefficient": float(self._coefficient),
            "source": self._source
        }


class PriceRecord:
   
    def __init__(
        self,
        material_id: str,
        price: float,
        region: str,
        valid_from: str,
        valid_until: Optional[str] = None,
        supplier_id: Optional[str] = None,
        source: str = ""
    ) -> None:
        if not material_id.strip() or not region.strip() or not valid_from.strip():
            raise ValueError("Parameter material_id, region, dan batas tanggal valid_from wajib terisi.")
        if price <= 0.0:
            raise ValueError("Nilai nominal harga satuan komoditas pasar wajib bernilai positif (> 0).")
        if valid_until is not None and valid_from > valid_until:
            raise ValueError("Kronologi tanggal salah: batas awal valid_from melampaui batas akhir valid_until.")

        self._material_id = material_id.strip()
        self._price = _to_decimal(price, "price")
        self._region = region.strip().upper()
        self._valid_from = valid_from.strip()
        self._valid_until = valid_until.strip() if valid_until is not None else None
        self._supplier_id = supplier_id.strip() if supplier_id is not None else None
        self._source = source.strip()

    @property
    def material_id(self) -> str:
        return self._material_id

    @property
    def price(self) -> Decimal:
        return self._price

    @property
    def region(self) -> str:
        return self._region

    def is_valid_at_date(self, check_date: str) -> bool:
       
        cleaned_date = check_date.strip()
        if not cleaned_date:
            return False
        if cleaned_date < self._valid_from:
            return False
        if self._valid_until is not None and cleaned_date > self._valid_until:
            return False
        return True

    def to_domain_state(self) -> Dict[str, Any]:
        return {
            "material_id": self._material_id,
            "price": float(self._price),
            "region": self._region,
            "valid_from": self._valid_from,
            "valid_until": self._valid_until,
            "supplier_id": self._supplier_id,
            "source": self._source
        }
