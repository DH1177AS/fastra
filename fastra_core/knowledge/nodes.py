# fastra_core\knowledge\nodes.py

from __future__ import annotations

import enum
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional
from fastra_core.primitives.currency import Currency
from pydantic import BaseModel, ConfigDict, Field, field_validator


class NodeLaborRole(str, enum.Enum):
   
    PEKERJA = "PEKERJA"
    TUKANG = "TUKANG"
    KEPALA_TUKANG = "KEPALA_TUKANG"
    MANDOR = "MANDOR"
    AHLI = "AHLI"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Gateway & Sanitization (Fail-Fast)
# ---------------------------------------------------------------------------

class MaterialNodeInboundDTO(BaseModel):
  
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    id: str = Field(..., min_length=5, max_length=64, pattern=r"^mat_[a-z0-9_]+$")
    name: str = Field(..., min_length=2, max_length=256)
    unit: str = Field(..., min_length=1, max_length=16, pattern=r"^[A-Za-z0-9²³\/()\s\u00B3]+$")
    category: str = Field(default="", max_length=128)
    specifications: Dict[str, Any] = Field(default_factory=dict, max_length=100)
    volatility_factor: float = Field(default=0.0, ge=0.0, le=1.0, allow_inf_nan=False)


class LaborNodeInboundDTO(BaseModel):
  
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    id: str = Field(..., min_length=5, max_length=64, pattern=r"^lab_[a-z0-9_]+$")
    name: str = Field(..., min_length=2, max_length=256)
    role: NodeLaborRole = Field(...)
    daily_rate: float = Field(..., ge=0.0, le=1e11, allow_inf_nan=False)
    region: str = Field(default="", max_length=64)


class EquipmentNodeInboundDTO(BaseModel):
  
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    id: str = Field(..., min_length=5, max_length=64, pattern=r"^eqp_[a-z0-9_]+$")
    name: str = Field(..., min_length=2, max_length=256)
    unit: str = Field(..., min_length=1, max_length=16)
    rate_per_day: Optional[float] = Field(default=None, gt=0.0, le=1e12, allow_inf_nan=False)
    rate_per_hour: Optional[float] = Field(default=None, gt=0.0, le=1e11, allow_inf_nan=False)
    rate_per_month: Optional[float] = Field(default=None, gt=0.0, le=1e13, allow_inf_nan=False)
    category: str = Field(default="", max_length=128)
    specifications: Dict[str, Any] = Field(default_factory=dict, max_length=100)
    mobilization_cost: float = Field(default=0.0, ge=0.0, le=1e12, allow_inf_nan=False)
    operator_cost_per_day: float = Field(default=0.0, ge=0.0, le=1e10, allow_inf_nan=False)
    fuel_cost_per_hour: float = Field(default=0.0, ge=0.0, le=1e10, allow_inf_nan=False)


class WorkItemNodeInboundDTO(BaseModel):
 
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    id: str = Field(..., min_length=5, max_length=64, pattern=r"^wi_[a-z0-9_]+$")
    code: str = Field(..., min_length=2, max_length=32, pattern=r"^[A-Z0-9_\-\.]+$")
    name: str = Field(..., min_length=2, max_length=512)
    unit: str = Field(..., min_length=1, max_length=16, pattern=r"^[A-Za-z0-9²³\/()\s\u00B3]+$")
    sni_ref: str = Field(default="", max_length=128)
    category: str = Field(default="", max_length=128)


class SupplierNodeInboundDTO(BaseModel):
 
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    id: str = Field(..., min_length=5, max_length=64, pattern=r"^spl_[a-z0-9_]+$")
    name: str = Field(..., min_length=2, max_length=256)
    region: str = Field(..., min_length=2, max_length=64, pattern=r"^[A-Z0-9_\-\s]+$")
    delivery_radius_km: float = Field(default=20.0, gt=0.0, le=1000.0, allow_inf_nan=False)


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
        raise ValueError(f"Field '{field_name}' gagal dikonversi ke representasi Decimal.") from exc

# ---------------------------------------------------------------------------
# Domain Models – Pure Business & Knowledge Graph Invariants (QS-Safe)
# ---------------------------------------------------------------------------

class MaterialNode:
   
    def __init__(
        self,
        id: str,
        name: str,
        unit: str,
        category: str = "",
        specifications: Dict[str, Any] = None,
        volatility_factor: float = 0.0
    ) -> None:
        if not id.strip() or not name.strip() or not unit.strip():
            raise ValueError("Parameter identitas id, name, dan unit material wajib diisi.")
        if volatility_factor < 0.0 or volatility_factor > 1.0:
            raise ValueError("Parameter volatility_factor berada di luar batas interval rasional (0.0 - 1.0).")

        self._id = id.strip()
        self._name = name.strip()
        self._unit = unit.strip()
        self._category = category.strip()
        self._specifications = dict(specifications or {})
        self._volatility_factor = _to_decimal(volatility_factor, "volatility_factor")

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def volatility_factor(self) -> Decimal:
        return self._volatility_factor

    def to_domain_state(self) -> Dict[str, Any]:
        return {
            "id": self._id,
            "name": self._name,
            "unit": self._unit,
            "category": self._category,
            "specifications": dict(self._specifications),
            "volatility_factor": float(self._volatility_factor)
        }


class LaborNode:
   
    def __init__(
        self,
        id: str,
        name: str,
        role: NodeLaborRole,
        daily_rate: float,
        region: str = ""
    ) -> None:
        if not id.strip() or not name.strip():
            raise ValueError("Parameter identitas id dan name untuk LaborNode dilarang kosong.")
        if isinstance(daily_rate, Currency):
            daily_rate_value = daily_rate.value
        else:
            daily_rate_value = daily_rate
        if daily_rate_value < 0:
            raise ValueError("Nilai nominal tarif upah harian kerja dilarang bernilai negatif.")

        self._id = id.strip()
        self._name = name.strip()
        self._role = role
        self._daily_rate = _to_decimal(daily_rate_value, "daily_rate")
        self._region = region.strip().upper()

    @property
    def id(self) -> str:
        return self._id

    @property
    def region(self) -> str:
        return self._region

    @property
    def daily_rate(self) -> Decimal:
        return self._daily_rate

    def to_domain_state(self) -> Dict[str, Any]:
        return {
            "id": self._id,
            "name": self._name,
            "role": self._role.value,
            "daily_rate": float(self._daily_rate),
            "region": self._region
        }


class EquipmentNode:
   
    def __init__(
        self,
        id: str,
        name: str,
        unit: str,
        rate_per_day: Optional[float] = None,
        rate_per_hour: Optional[float] = None,
        rate_per_month: Optional[float] = None,
        category: str = "",
        specifications: Dict[str, Any] = None,
        mobilization_cost: float = 0.0,
        operator_cost_per_day: float = 0.0,
        fuel_cost_per_hour: float = 0.0
    ) -> None:
        if not id.strip() or not name.strip() or not unit.strip():
            raise ValueError("Parameter identitas id, name, dan unit peralatan mekanikal wajib diisi.")
        if mobilization_cost < 0.0 or operator_cost_per_day < 0.0 or fuel_cost_per_hour < 0.0:
            raise ValueError("Komponen restriksi biaya atribusi fungsional alat dilarang bernilai negatif.")

        self._id = id.strip()
        self._name = name.strip()
        self._unit = unit.strip()
        self._rate_per_day = _to_decimal(rate_per_day, "rate_per_day") if rate_per_day is not None else None
        self._rate_per_hour = _to_decimal(rate_per_hour, "rate_per_hour") if rate_per_hour is not None else None
        self._rate_per_month = _to_decimal(rate_per_month, "rate_per_month") if rate_per_month is not None else None
        self._category = category.strip()
        self._specifications = dict(specifications or {})
        self._mobilization_cost = _to_decimal(mobilization_cost, "mobilization_cost")
        self._operator_cost_per_day = _to_decimal(operator_cost_per_day, "operator_cost_per_day")
        self._fuel_cost_per_hour = _to_decimal(fuel_cost_per_hour, "fuel_cost_per_hour")

    @property
    def id(self) -> str:
        return self._id

    @property
    def rate_per_hour(self) -> Optional[Decimal]:
        return self._rate_per_hour

    @property
    def rate_per_day(self) -> Optional[Decimal]:
        return self._rate_per_day

    @property
    def mobilization_cost(self) -> Decimal:
        return self._mobilization_cost

    @property
    def operator_cost_per_day(self) -> Decimal:
        return self._operator_cost_per_day

    @property
    def fuel_cost_per_hour(self) -> Decimal:
        return self._fuel_cost_per_hour

    def to_domain_state(self) -> Dict[str, Any]:
        return {
            "id": self._id,
            "name": self._name,
            "unit": self._unit,
            "rate_per_day": float(self._rate_per_day) if self._rate_per_day is not None else None,
            "rate_per_hour": float(self._rate_per_hour) if self._rate_per_hour is not None else None,
            "rate_per_month": float(self._rate_per_month) if self._rate_per_month is not None else None,
            "category": self._category,
            "specifications": dict(self._specifications),
            "mobilization_cost": float(self._mobilization_cost),
            "operator_cost_per_day": float(self._operator_cost_per_day),
            "fuel_cost_per_hour": float(self._fuel_cost_per_hour)
        }


class WorkItemNode:
    
    def __init__(
        self,
        id: str,
        code: str,
        name: str,
        unit: str,
        sni_ref: str = "",
        category: str = ""
    ) -> None:
        if not id.strip() or not code.strip() or not name.strip() or not unit.strip():
            raise ValueError("Parameter penentu identitas mutlak fungsional WorkItemNode wajib terisi sempurna.")

        self._id = id.strip()
        self._code = code.strip().upper()
        self._name = name.strip()
        self._unit = unit.strip()
        self._sni_ref = sni_ref.strip()
        self._category = category.strip()

    @property
    def id(self) -> str:
        return self._id

    @property
    def code(self) -> str:
        return self._code

    @property
    def name(self) -> str:
        return self._name

    def to_domain_state(self) -> Dict[str, Any]:
        return {
            "id": self._id,
            "code": self._code,
            "name": self._name,
            "unit": self._unit,
            "sni_ref": self._sni_ref,
            "category": self._category
        }

    @property
    def sni_ref(self) -> Optional[str]:
        return getattr(self, "_sni_ref", None)

class SupplierNode:
   
    def __init__(
        self,
        id: str,
        name: str,
        region: str,
        delivery_radius_km: float = 20.0
    ) -> None:
        if not id.strip() or not name.strip() or not region.strip():
            raise ValueError("Parameter identitas id, name, dan regional pangkalan penyedia dilarang kosong.")
        if delivery_radius_km <= 0.0:
            raise ValueError("Jangkauan batasan radius pengiriman logistik (delivery_radius_km) harus positif.")

        self._id = id.strip()
        self._name = name.strip()
        self._region = region.strip().upper()
        self._delivery_radius_km = _to_decimal(delivery_radius_km, "delivery_radius_km")

    @property
    def id(self) -> str:
        return self._id

    def to_domain_state(self) -> Dict[str, Any]:
        return {
            "id": self._id,
            "name": self._name,
            "region": self._region,
            "delivery_radius_km": float(self._delivery_radius_km)
        }
