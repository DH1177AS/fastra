# fastra_core\ccm\resource.py

from __future__ import annotations

import enum
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MaterialClass(str, enum.Enum):
    CONCRETE = "CONCRETE"
    STEEL = "STEEL"
    WOOD = "WOOD"
    MASONRY = "MASONRY"
    GLASS = "GLASS"
    PLASTIC = "PLASTIC"
    COMPOSITE = "COMPOSITE"
    FINISH = "FINISH"


class EquipmentType(str, enum.Enum):
    EXCAVATOR = "EXCAVATOR"
    CRANE = "CRANE"
    MIXER = "MIXER"
    VIBRATOR = "VIBRATOR"
    SCAFFOLDING = "SCAFFOLDING"
    PUMP = "PUMP"
    GENERATOR = "GENERATOR"
    TOWER_CRANE = "TOWER_CRANE"


class LaborType(str, enum.Enum):
    TUKANG_BATU = "TUKANG_BATU"
    TUKANG_KAYU = "TUKANG_KAYU"
    TUKANG_BESI = "TUKANG_BESI"
    PEKERJA = "PEKERJA"
    KEPALA_TUKANG = "KEPALA_TUKANG"
    MANDOR = "MANDOR"


class SkillLevel(str, enum.Enum):
    JUNIOR = "JUNIOR"
    SENIOR = "SENIOR"
    EXPERT = "EXPERT"


class EntityType(str, enum.Enum):
    RESOURCE = "RESOURCE"
    HUMAN = "HUMAN"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Gateway & Sanitization (Fail-Fast)
# ---------------------------------------------------------------------------
class MaterialInboundDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    material_class: MaterialClass = Field(default=MaterialClass.CONCRETE)
    material_type: str = Field(..., min_length=2, max_length=128)
    unit: str = Field(
        ...,
        min_length=1,
        max_length=16,
        pattern=r"^[A-Za-z0-9²³\/()\s\u00B3]+$",
        description="Satuan pengukuran material",
    )
    density: Optional[float] = Field(
        default=None, gt=0.0, le=50000.0, allow_inf_nan=False
    )
    strength_grade: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=32,
        pattern=r"^[A-Z0-9_\-\.\s]+$",
    )
    specifications: Dict[str, Any] = Field(default_factory=dict, max_length=100)

    @field_validator("specifications", mode="after")
    @classmethod
    def validate_specifications_keys(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        for k in value.keys():
            if not k.strip():
                raise ValueError(
                    "Kunci dalam spesifikasi material tidak boleh berupa spasi kosong."
                )
        return value


class EquipmentInboundDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    equipment_type: EquipmentType = Field(default=EquipmentType.EXCAVATOR)
    capacity: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_\-\.\s\/]+$",
    )
    unit: str = Field(
        ..., min_length=1, max_length=16, pattern=r"^[a-z0-9\s]+$"
    )
    hourly_rate: Optional[float] = Field(
        default=None, ge=0.0, le=1e12, allow_inf_nan=False
    )


class LaborInboundDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    labor_type: LaborType = Field(default=LaborType.PEKERJA)
    daily_rate: float = Field(default=120000.0, ge=0.0, le=1e11, allow_inf_nan=False)
    productivity: Dict[str, float] = Field(default_factory=dict, max_length=100)
    skill_level: SkillLevel = Field(default=SkillLevel.JUNIOR)

    @field_validator("productivity", mode="after")
    @classmethod
    def validate_productivity_metrics(
        cls, value: Dict[str, float]
    ) -> Dict[str, float]:
        for k, v in value.items():
            if not k.strip():
                raise ValueError(
                    "Identifikasi kode pekerjaan dalam kamus produktivitas tidak boleh kosong."
                )
            if not isinstance(v, (int, float)) or v <= 0.0:
                raise ValueError(
                    "Nilai indeks koefisien output produktivitas wajib bertipe numerik positif (> 0)."
                )
        return value


# ---------------------------------------------------------------------------
# Core Utilities – Jaminan Keamanan Type Casting
# ---------------------------------------------------------------------------
def _to_decimal(value: Any, field_name: str) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return Decimal(str(value))
    raise TypeError(f"Field '{field_name}' wajib bertipe numerik dasar (int/float/Decimal).")


# ---------------------------------------------------------------------------
# Domain Models – Pure Business & Construction Resource Invariants
# ---------------------------------------------------------------------------
class Material:
    def __init__(
        self,
        name: str = "",
        material_class: Any = MaterialClass.CONCRETE,
        material_type: str = "",
        unit: str = "",
        density: Optional[float] = None,
        strength_grade: Optional[str] = None,
        specifications: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not material_type.strip() or not unit.strip():
            raise ValueError(
                "Parameter identitas material_type dan spesifikasi unit wajib terisi."
            )
        if density is not None and density <= 0.0:
            raise ValueError("Kerapatan massa jenis material (density) wajib bernilai positif (> 0).")

        # Konversi material_class dari string ke enum jika perlu
        if isinstance(material_class, str):
            try:
                material_class = MaterialClass(material_class)
            except ValueError:
                raise ValueError(f"material_class '{material_class}' tidak valid.")

        self._name = name.strip()
        self._material_class = material_class
        self._material_type = material_type.strip()
        self._unit = unit.strip()
        self._density = _to_decimal(density, "density") if density is not None else None
        self._strength_grade = strength_grade.strip() if strength_grade is not None else None
        self._specifications = dict(specifications or {})
        self._entity_type = EntityType.RESOURCE

    @property
    def name(self) -> str:
        return self._name

    @property
    def material_class(self) -> MaterialClass:
        return self._material_class

    @property
    def material_type(self) -> str:
        return self._material_type

    @property
    def unit(self) -> str:
        return self._unit

    @property
    def density(self) -> Optional[Decimal]:
        return self._density

    @property
    def strength_grade(self) -> Optional[str]:
        return self._strength_grade

    @property
    def specifications(self) -> Dict[str, Any]:
        return dict(self._specifications)

    def to_domain_state(self) -> Dict[str, Any]:
        return {
            "name": self._name,
            "material_class": self._material_class.value,
            "material_type": self._material_type,
            "unit": self._unit,
            "density": float(self._density) if self._density is not None else None,
            "strength_grade": self._strength_grade,
            "specifications": dict(self._specifications),
            "entity_type": self._entity_type.value,
        }


class Equipment:
    def __init__(
        self,
        equipment_type: EquipmentType,
        unit: str,
        capacity: Optional[str] = None,
        hourly_rate: Optional[float] = None,
    ) -> None:
        if not unit.strip():
            raise ValueError(
                "Spesifikasi satuan waktu operasional unit (unit) tidak boleh kosong."
            )
        if capacity is not None and not capacity.strip():
            raise ValueError(
                "Deskripsi nilai batas kapasitas kerja alat (capacity) dilarang kosong."
            )
        if hourly_rate is not None and hourly_rate < 0.0:
            raise ValueError("Tarif sewa per jam (hourly_rate) tidak boleh negatif.")

        self._equipment_type = equipment_type
        self._unit = unit.strip()
        self._capacity = capacity.strip() if capacity is not None else None
        self._hourly_rate = (
            _to_decimal(hourly_rate, "hourly_rate") if hourly_rate is not None else None
        )
        self._entity_type = EntityType.RESOURCE

    @property
    def equipment_type(self) -> EquipmentType:
        return self._equipment_type

    @property
    def unit(self) -> str:
        return self._unit

    @property
    def capacity(self) -> Optional[str]:
        return self._capacity

    @property
    def hourly_rate(self) -> Optional[Decimal]:
        return self._hourly_rate

    def calculate_operational_cost(self, duration_hours: Decimal) -> Decimal:
        if self._hourly_rate is None:
            return Decimal("0.00")
        if duration_hours < Decimal("0"):
            raise ValueError("Durasi waktu pemakaian alat berat dilarang bernilai negatif.")
        return (duration_hours * self._hourly_rate).quantize(Decimal("0.01"))

    def to_domain_state(self) -> Dict[str, Any]:
        return {
            "equipment_type": self._equipment_type.value,
            "capacity": self._capacity,
            "unit": self._unit,
            "hourly_rate": float(self._hourly_rate) if self._hourly_rate is not None else None,
            "entity_type": self._entity_type.value,
        }


class Labor:
    def __init__(
        self,
        labor_type: LaborType,
        daily_rate: float,
        productivity: Dict[str, float],
        skill_level: SkillLevel,
    ) -> None:
        if daily_rate < 0.0:
            raise ValueError("Upah harian tenaga kerja (daily_rate) tidak boleh negatif.")
        if not productivity:
            raise ValueError("Tabel koefisien produktivitas tidak boleh kosong.")

        for k, v in productivity.items():
            if not k.strip():
                raise ValueError("Kode pekerjaan dalam tabel produktivitas tidak boleh kosong.")
            if not isinstance(v, (int, float)) or v <= 0.0:
                raise ValueError("Koefisien produktivitas harus bernilai positif.")

        self._labor_type = labor_type
        self._daily_rate = _to_decimal(daily_rate, "daily_rate")
        self._productivity = {
            k.strip(): _to_decimal(v, f"productivity.{k}")
            for k, v in productivity.items()
        }
        self._skill_level = skill_level
        self._entity_type = EntityType.HUMAN

    @property
    def labor_type(self) -> LaborType:
        return self._labor_type

    @property
    def daily_rate(self) -> Decimal:
        return self._daily_rate

    @property
    def productivity(self) -> Dict[str, Decimal]:
        return dict(self._productivity)

    @property
    def skill_level(self) -> SkillLevel:
        return self._skill_level

    def get_coefficient_for_task(self, task_code: str) -> Decimal:
        cleaned_code = task_code.strip()
        if cleaned_code not in self._productivity:
            raise KeyError(
                f"Kode aktivitas pekerjaan '{cleaned_code}' tidak terdaftar pada tabel upah produktivitas tenaga kerja."
            )
        return self._productivity[cleaned_code]

    def to_domain_state(self) -> Dict[str, Any]:
        return {
            "labor_type": self._labor_type.value,
            "daily_rate": float(self._daily_rate),
            "productivity": {k: float(v) for k, v in self._productivity.items()},
            "skill_level": self._skill_level.value,
            "entity_type": self._entity_type.value,
        }