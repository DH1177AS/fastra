# fastra_core\ccm\economic.py

from __future__ import annotations

import enum
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from fastra_core.units import validate_unit_not_unknown


class CostType(str, enum.Enum):
    
    MATERIAL = "MATERIAL"
    LABOR = "LABOR"
    EQUIPMENT = "EQUIPMENT"
    OVERHEAD = "OVERHEAD"
    PROFIT = "PROFIT"
    TAX = "TAX"
    CONTINGENCY = "CONTINGENCY"


class EntityType(str, enum.Enum):
    
    ECONOMIC = "ECONOMIC"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Gateway & Sanitization (Fail-Fast)
# ---------------------------------------------------------------------------
class WorkItemInboundDTO(BaseModel):
   
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
    )

    work_item_code: str = Field(
        ...,
        min_length=2,
        max_length=32,
        pattern=r"^[A-Z0-9_\-\.]+$",
        description="Kode item pekerjaan (huruf besar, angka, underscore, strip, titik)",
    )
    work_item_name: str = Field(..., min_length=2, max_length=256)
    unit: str = Field(
        ...,
        min_length=1,
        max_length=16,
        pattern=r"^[A-Za-z0-9²³\/]+$",
        description="Satuan pengukuran (contoh: m², m³, kg)",
    )
    quantity: float = Field(..., ge=0.0, le=1e9, allow_inf_nan=False)
    source_entity_id: Optional[str] = Field(
        default=None,
        min_length=5,
        max_length=64,
        pattern=r"^[a-z0-9_]+$",
    )
    ahs_ref: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=64,
        pattern=r"^[A-Z0-9_\-\.\s\/]+$",
    )
    sni_ref: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=64,
        pattern=r"^[A-Z0-9_\-\.\s\/]+$",
    )


class BOQItemInboundDTO(BaseModel):
   
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
    )

    boq_section: str = Field(..., min_length=2, max_length=128)
    work_items: List[str] = Field(default_factory=list, max_length=10000)
    total_quantity: float = Field(..., ge=0.0, le=1e9, allow_inf_nan=False)
    unit: str = Field(
        ...,
        min_length=1,
        max_length=16,
        pattern=r"^[A-Za-z0-9²³\/]+$",
    )

    @field_validator("work_items", mode="after")
    @classmethod
    def validate_work_items_codes(cls, values: List[str]) -> List[str]:
        """Pastikan setiap kode work item tidak kosong/whitespace."""
        for val in values:
            if not val.strip():
                raise ValueError(
                    "Kode referensi elemen work_items tidak boleh kosong atau spasi."
                )
        return values


class CostItemInboundDTO(BaseModel):
   
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
    )

    cost_type: CostType = Field(default=CostType.MATERIAL)
    amount: float = Field(..., ge=0.0, le=1e14, allow_inf_nan=False)
    work_item_ref: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=32,
        pattern=r"^[A-Z0-9_\-\.]+$",
    )
    resource_ref: Optional[str] = Field(
        default=None,
        min_length=5,
        max_length=64,
        pattern=r"^res_[a-z0-9_]+$",
    )
    coefficient: float = Field(..., gt=0.0, le=100000.0, allow_inf_nan=False)
    unit_price: float = Field(..., ge=0.0, le=1e12, allow_inf_nan=False)
    price_source: str = Field(..., min_length=2, max_length=128)
    price_date: str = Field(
        ...,
        min_length=10,
        max_length=10,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Format tanggal YYYY-MM-DD",
    )


class RABItemInboundDTO(BaseModel):
   
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
    )

    rab_section: str = Field(..., min_length=2, max_length=128)
    cost_items: List[str] = Field(default_factory=list, max_length=10000)
    subtotal: float = Field(..., ge=0.0, le=1e14, allow_inf_nan=False)
    total: float = Field(..., ge=0.0, le=1e14, allow_inf_nan=False)
    location_factor: float = Field(..., gt=0.0, le=10.0, allow_inf_nan=False)


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
            f"Field '{field_name}' gagal dikonversi ke representasi Decimal imutabel."
        ) from exc


# ---------------------------------------------------------------------------
# Domain Models – Pure Business & Financial Logical Invariants (QS-Safe)
# ---------------------------------------------------------------------------
class WorkItem:
    def __init__(
        self,
        work_item_code: str,
        work_item_name: str = "",
        unit: str = "",
        quantity: float = 0.0,
        name: str = "",
        source_entity_id: Optional[str] = None,
        ahs_ref: Optional[str] = None,
        sni_ref: Optional[str] = None,
    ) -> None:
        if not work_item_code.strip() or not unit.strip():
            raise ValueError("Parameter identitas work_item_code dan unit wajib memiliki isi.")
        if quantity < 0:
            raise ValueError("quantity tidak boleh negatif.")

        self._work_item_code = work_item_code.strip()
        # Gunakan name jika diberikan, jika tidak gunakan work_item_name
        self._work_item_name = (name or work_item_name).strip()
        self._unit = unit.strip()
        validate_unit_not_unknown(self._unit)
        self._quantity = _to_decimal(quantity, "quantity")
        self._source_entity_id = source_entity_id
        self._ahs_ref = ahs_ref
        self._sni_ref = sni_ref
        self._entity_type = EntityType.ECONOMIC

    @property
    def name(self) -> str:
        return self._work_item_name

    @property
    def work_item_code(self) -> str:
        return self._work_item_code

    @property
    def work_item_name(self) -> str:
        return self._work_item_name

    @property
    def unit(self) -> str:
        return self._unit

    @property
    def quantity(self) -> Decimal:
        return self._quantity

    @property
    def source_entity_id(self) -> Optional[str]:
        return self._source_entity_id

    @property
    def ahs_ref(self) -> Optional[str]:
        return self._ahs_ref

    @property
    def sni_ref(self) -> Optional[str]:
        return self._sni_ref

    @property
    def entity_type(self) -> EntityType:
        return self._entity_type

    def to_domain_state(self) -> Dict[str, Any]:
        return {
            "work_item_code": self._work_item_code,
            "work_item_name": self._work_item_name,
            "unit": self._unit,
            "quantity": float(self._quantity),
            "source_entity_id": self._source_entity_id,
            "ahs_ref": self._ahs_ref,
            "sni_ref": self._sni_ref,
            "entity_type": self._entity_type.value,
        }


class BOQItem:
   
    def __init__(
        self,
        boq_section: str,
        work_items: List[str],
        total_quantity: float,
        unit: str,
    ) -> None:
        if not boq_section.strip() or not unit.strip():
            raise ValueError("Nama boq_section dan spesifikasi unit tidak boleh kosong.")
        if total_quantity < 0:
            raise ValueError("total_quantity tidak boleh negatif.")

        self._boq_section = boq_section.strip()
        self._work_items = [item.strip() for item in work_items if item.strip()]
        self._total_quantity = _to_decimal(total_quantity, "total_quantity")
        self._unit = unit.strip()
        self._entity_type = EntityType.ECONOMIC

    @property
    def boq_section(self) -> str:
        return self._boq_section

    @property
    def work_items(self) -> List[str]:
        return list(self._work_items)

    @property
    def total_quantity(self) -> Decimal:
        return self._total_quantity

    @property
    def unit(self) -> str:
        return self._unit

    @property
    def entity_type(self) -> EntityType:
        return self._entity_type

    def to_domain_state(self) -> Dict[str, Any]:
        """Serialisasi ke dictionary snake_case."""
        return {
            "boq_section": self._boq_section,
            "work_items": list(self._work_items),
            "total_quantity": float(self._total_quantity),
            "unit": self._unit,
            "entity_type": self._entity_type.value,
        }


class CostItem:
    
    def __init__(
        self,
        cost_type: CostType,
        amount: float,
        coefficient: float,
        unit_price: float,
        price_source: str,
        price_date: str,
        work_item_ref: Optional[str] = None,
        resource_ref: Optional[str] = None,
    ) -> None:
        if coefficient <= 0.0:
            raise ValueError("Nilai koefisien indeks analisis harga satuan wajib bernilai positif (> 0).")
        if amount < 0.0:
            raise ValueError("amount tidak boleh negatif.")
        if unit_price < 0.0:
            raise ValueError("unit_price tidak boleh negatif.")

        self._cost_type = cost_type
        self._amount = _to_decimal(amount, "amount")
        self._coefficient = _to_decimal(coefficient, "coefficient")
        self._unit_price = _to_decimal(unit_price, "unit_price")
        self._price_source = price_source.strip()
        self._price_date = price_date.strip()
        self._work_item_ref = work_item_ref
        self._resource_ref = resource_ref
        self._entity_type = EntityType.ECONOMIC

    @property
    def cost_type(self) -> CostType:
        return self._cost_type

    @property
    def amount(self) -> Decimal:
        return self._amount

    @property
    def coefficient(self) -> Decimal:
        return self._coefficient

    @property
    def unit_price(self) -> Decimal:
        return self._unit_price

    @property
    def price_source(self) -> str:
        return self._price_source

    @property
    def price_date(self) -> str:
        return self._price_date

    @property
    def work_item_ref(self) -> Optional[str]:
        return self._work_item_ref

    @property
    def resource_ref(self) -> Optional[str]:
        return self._resource_ref

    @property
    def entity_type(self) -> EntityType:
        return self._entity_type

    def verify_and_recalculate_amount(self, target_quantity: Decimal) -> Decimal:
       
        computed = target_quantity * self._coefficient * self._unit_price
        self._amount = computed.quantize(Decimal("0.01"))
        return self._amount

    def to_domain_state(self) -> Dict[str, Any]:
        
        return {
            "cost_type": self._cost_type.value,
            "amount": float(self._amount),
            "work_item_ref": self._work_item_ref,
            "resource_ref": self._resource_ref,
            "coefficient": float(self._coefficient),
            "unit_price": float(self._unit_price),
            "price_source": self._price_source,
            "price_date": self._price_date,
            "entity_type": self._entity_type.value,
        }


class RABItem:
   
    def __init__(
        self,
        rab_section: str,
        cost_items: List[str],
        subtotal: float,
        total: float,
        location_factor: float,
    ) -> None:
        if not rab_section.strip():
            raise ValueError("Nama klaster rab_section wajib ditentukan.")
        if location_factor <= 0.0:
            raise ValueError("Faktor indeks penyesuaian lokasi geografi wajib bernilai positif (> 0).")
        if subtotal < 0.0 or total < 0.0:
            raise ValueError("subtotal dan total tidak boleh negatif.")

        self._rab_section = rab_section.strip()
        self._cost_items = [item.strip() for item in cost_items if item.strip()]
        self._subtotal = _to_decimal(subtotal, "subtotal")
        self._total = _to_decimal(total, "total")
        self._location_factor = _to_decimal(location_factor, "location_factor")
        self._entity_type = EntityType.ECONOMIC

    @property
    def rab_section(self) -> str:
        return self._rab_section

    @property
    def cost_items(self) -> List[str]:
        return list(self._cost_items)

    @property
    def subtotal(self) -> Decimal:
        return self._subtotal

    @property
    def total(self) -> Decimal:
        return self._total

    @property
    def location_factor(self) -> Decimal:
        return self._location_factor

    @property
    def entity_type(self) -> EntityType:
        return self._entity_type

    def recalculate_totals_from_items(self, derived_amounts: List[Decimal]) -> None:
        
        summed_subtotal = sum(derived_amounts)
        self._subtotal = summed_subtotal.quantize(Decimal("0.01"))
        raw_total = self._subtotal * self._location_factor
        self._total = raw_total.quantize(Decimal("0.01"))

    def to_domain_state(self) -> Dict[str, Any]:
        
        return {
            "rab_section": self._rab_section,
            "cost_items": list(self._cost_items),
            "subtotal": float(self._subtotal),
            "total": float(self._total),
            "location_factor": float(self._location_factor),
            "entity_type": self._entity_type.value,
        }