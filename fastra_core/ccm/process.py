# fastra_core/ccm/process.py

from __future__ import annotations

import enum
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskType(str, enum.Enum):
    GALIAN = "GALIAN"
    BEKISTING = "BEKISTING"
    PEMBESIAN = "PEMBESIAN"
    PENGECORAN = "PENGECORAN"
    PASANGAN_BATA = "PASANGAN_BATA"
    PLESTERAN = "PLESTERAN"
    PENGECATAN = "PENGECATAN"
    INSTALASI = "INSTALASI"


class InspectionType(str, enum.Enum):
    VISUAL = "VISUAL"
    TEST = "TEST"
    VERIFICATION = "VERIFICATION"


class InspectionFrequency(str, enum.Enum):
    HARIAN = "HARIAN"
    MINGGUAN = "MINGGUAN"
    BULANAN = "BULANAN"
    PER_BATCH = "PER_BATCH"
    PER_ZONA = "PER_ZONA"
    TAHUNAN = "TAHUNAN"


class EntityType(str, enum.Enum):
    PROCESS = "PROCESS"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Gateway & Sanitization (Fail-Fast)
# ---------------------------------------------------------------------------
class ResourceAllocationInboundDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    resource_uuid: str = Field(
        ...,
        min_length=5,
        max_length=64,
        pattern=r"^res_[a-z0-9_\-]+$",
        description="UUID sumber daya (format res_xxxxx)",
    )
    quantity: float = Field(..., gt=0.0, le=1e7, allow_inf_nan=False)
    unit: str = Field(
        ...,
        min_length=1,
        max_length=16,
        pattern=r"^[A-Za-z0-9²³\/()\s]+$",
        description="Satuan alokasi sumber daya",
    )
    duration_hours: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=87600.0,
        allow_inf_nan=False,
        description="Durasi penggunaan dalam jam",
    )


class ConstructionTaskInboundDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    task_type: TaskType = Field(default=TaskType.GALIAN)
    work_item_ref: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=32,
        pattern=r"^[A-Z0-9_\-\.]+$",
    )
    inputs: List[str] = Field(..., min_length=1, max_length=100)
    outputs: List[str] = Field(..., min_length=1, max_length=100)
    resources: List[ResourceAllocationInboundDTO] = Field(
        default_factory=list, max_length=500
    )
    duration_hours: Optional[float] = Field(
        default=None, ge=0.0, le=87600.0, allow_inf_nan=False
    )
    predecessors: List[str] = Field(default_factory=list, max_length=100)

    @field_validator("inputs", "outputs", "predecessors", mode="after")
    @classmethod
    def validate_reference_arrays(cls, values: List[str]) -> List[str]:
        """Pastikan setiap string referensi tidak kosong atau hanya spasi."""
        for val in values:
            if not val.strip():
                raise ValueError(
                    "Item referensi string di dalam koleksi tidak boleh kosong."
                )
        return values


class InspectionTaskInboundDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    inspection_type: InspectionType = Field(default=InspectionType.VISUAL)
    standard: str = Field(
        default="SNI",
        min_length=2,
        max_length=64,
        pattern=r"^[A-Z0-9\s\-]+$",
        description="Referensi standar (contoh: SNI, ASTM)",
    )
    checklist: List[str] = Field(
        default_factory=lambda: ["Check point 1"],
        min_length=1,
        max_length=100,
    )
    frequency: InspectionFrequency = Field(default=InspectionFrequency.HARIAN)
    assigned_to: Optional[str] = Field(
        default=None,
        min_length=5,
        max_length=64,
        pattern=r"^usr_[a-z0-9_]+$",
        description="ID pengguna yang ditugaskan (format usr_xxxxx)",
    )

    @field_validator("checklist", mode="after")
    @classmethod
    def validate_checklist_items(cls, values: List[str]) -> List[str]:
        for val in values:
            if not val.strip():
                raise ValueError(
                    "Item teks di dalam checklist pemeriksaan tidak boleh kosong."
                )
        return values


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
# Domain Models – Pure Business & Construction Process Invariants
# ---------------------------------------------------------------------------
class ResourceAllocation:
    def __init__(
        self,
        resource_uuid: str,
        quantity: float,
        unit: str,
        duration_hours: Optional[float] = None,
    ) -> None:
        if not resource_uuid.strip() or not unit.strip():
            raise ValueError("Parameter resource_uuid dan unit alokasi wajib diisi.")
        if quantity <= 0.0:
            raise ValueError(
                "Kuantitas alokasi pemakaian sumber daya konstruksi wajib positif (> 0)."
            )
        if duration_hours is not None and duration_hours < 0.0:
            raise ValueError(
                "Durasi waktu penggunaan alokasi sumber daya tidak boleh bernilai negatif."
            )

        self._resource_uuid = resource_uuid.strip()
        self._quantity = _to_decimal(quantity, "quantity")
        self._unit = unit.strip()
        self._duration_hours = (
            _to_decimal(duration_hours, "duration_hours")
            if duration_hours is not None
            else None
        )

    @property
    def resource_uuid(self) -> str:
        return self._resource_uuid

    @property
    def quantity(self) -> Decimal:
        return self._quantity

    @property
    def unit(self) -> str:
        return self._unit

    @property
    def duration_hours(self) -> Optional[Decimal]:
        return self._duration_hours

    def to_domain_state(self) -> Dict[str, Any]:
        """Serialisasi ke dictionary snake_case."""
        return {
            "resource_uuid": self._resource_uuid,
            "quantity": float(self._quantity),
            "unit": self._unit,
            "duration_hours": (
                float(self._duration_hours) if self._duration_hours is not None else None
            ),
        }


class ConstructionTask:
    def __init__(
        self,
        task_type: TaskType,
        inputs: List[str],
        outputs: List[str],
        resources: List[ResourceAllocation],
        work_item_ref: Optional[str] = None,
        duration_hours: Optional[float] = None,
        predecessors: Optional[List[str]] = None,
    ) -> None:
        if not inputs or not outputs:
            raise ValueError(
                "Aktivitas konstruksi wajib memiliki minimal 1 komponen input dan 1 komponen output."
            )
        if duration_hours is not None and duration_hours < 0.0:
            raise ValueError("Durasi aktivitas tidak boleh negatif.")
        if predecessors is None:
            predecessors = []

        cleaned_predecessors = [p.strip() for p in predecessors if p.strip()]
        if len(cleaned_predecessors) != len(predecessors):
            raise ValueError("Predecessor tidak boleh berupa string kosong atau spasi.")

        self._task_type = task_type
        self._work_item_ref = work_item_ref
        self._inputs = [item.strip() for item in inputs if item.strip()]
        self._outputs = [item.strip() for item in outputs if item.strip()]
        self._resources = list(resources)
        self._duration_hours = (
            _to_decimal(duration_hours, "duration_hours")
            if duration_hours is not None
            else None
        )
        self._predecessors = cleaned_predecessors
        self._entity_type = EntityType.PROCESS

        if not self._inputs or not self._outputs:
            raise ValueError("Input/output tidak boleh kosong setelah pembersihan.")

    @property
    def task_type(self) -> TaskType:
        return self._task_type

    @property
    def work_item_ref(self) -> Optional[str]:
        return self._work_item_ref

    @property
    def inputs(self) -> List[str]:
        return list(self._inputs)

    @property
    def outputs(self) -> List[str]:
        return list(self._outputs)

    @property
    def resources(self) -> List[ResourceAllocation]:
        return list(self._resources)

    @property
    def duration_hours(self) -> Optional[Decimal]:
        return self._duration_hours

    @property
    def predecessors(self) -> List[str]:
        return list(self._predecessors)

    @property
    def entity_type(self) -> EntityType:
        return self._entity_type

    def verify_circular_dependency(self, current_task_id: str) -> bool:
        if current_task_id in self._predecessors:
            raise ValueError(
                f"Deteksi kegagalan logika CPM: Task '{current_task_id}' dilarang menjadi predecessor bagi dirinya sendiri."
            )
        return True

    def to_domain_state(self) -> Dict[str, Any]:
        """Serialisasi ke dictionary snake_case."""
        return {
            "task_type": self._task_type.value,
            "work_item_ref": self._work_item_ref,
            "inputs": list(self._inputs),
            "outputs": list(self._outputs),
            "resources": [res.to_domain_state() for res in self._resources],
            "duration_hours": (
                float(self._duration_hours) if self._duration_hours is not None else None
            ),
            "predecessors": list(self._predecessors),
            "entity_type": self._entity_type.value,
        }


class InspectionTask:
    def __init__(
        self,
        inspection_type: InspectionType,
        standard: str,
        checklist: List[str],
        frequency: InspectionFrequency,
        assigned_to: Optional[str] = None,
    ) -> None:
        if not checklist:
            raise ValueError(
                "Kumpulan kriteria lembar checklist pemeriksaan mutu wajib terisi."
            )
        if not standard.strip():
            raise ValueError(
                "Referensi standard rujukan regulasi teknis (seperti SNI/ASTM) tidak boleh kosong."
            )

        self._inspection_type = inspection_type
        self._standard = standard.strip()
        self._checklist = [item.strip() for item in checklist if item.strip()]
        self._frequency = frequency
        self._assigned_to = assigned_to
        self._entity_type = EntityType.PROCESS

        if not self._checklist:
            raise ValueError(
                "Kriteria lembar checklist terdeteksi kosong setelah proses pembersihan spasi."
            )

    @property
    def inspection_type(self) -> InspectionType:
        return self._inspection_type

    @property
    def standard(self) -> str:
        return self._standard

    @property
    def checklist(self) -> List[str]:
        return list(self._checklist)

    @property
    def frequency(self) -> InspectionFrequency:
        return self._frequency

    @property
    def assigned_to(self) -> Optional[str]:
        return self._assigned_to

    @property
    def entity_type(self) -> EntityType:
        return self._entity_type

    def to_domain_state(self) -> Dict[str, Any]:
        return {
            "inspection_type": self._inspection_type.value,
            "standard": self._standard,
            "checklist": list(self._checklist),
            "frequency": self._frequency.value,
            "assigned_to": self._assigned_to,
            "entity_type": self._entity_type.value,
        }