# fastra_core\ccm\common.py

from __future__ import annotations

import enum
from decimal import Decimal
from fastra_core.primitives.length import Length
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OpeningType(str, enum.Enum):
   
    DOOR = "DOOR"
    WINDOW = "WINDOW"
    VENTS = "VENTS"
    ARCH = "ARCH"


class FinishType(str, enum.Enum):
   
    PLESTER = "PLESTER"
    ACIAN = "ACIAN"
    CAT = "CAT"
    KERAMIK = "KERAMIK"
    GYPSUM = "GYPSUM"
    EXPOSED = "EXPOSED"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Gateway & Sanitization
# ---------------------------------------------------------------------------
class OpeningInboundDTO(BaseModel):
    
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
    )

    width: float = Field(
        ...,
        gt=0.1,
        le=15.0,
        allow_inf_nan=False,
        description="Lebar bukaan dalam meter",
    )
    height: float = Field(
        ...,
        gt=0.1,
        le=15.0,
        allow_inf_nan=False,
        description="Tinggi bukaan dalam meter",
    )
    position: float = Field(
        ...,
        ge=0.0,
        le=1000.0,
        allow_inf_nan=False,
        description="Posisi offset linier pada elemen induk",
    )
    opening_type: OpeningType = Field(default=OpeningType.DOOR)


class ReinforcementSpecInboundDTO(BaseModel):
    
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
    )

    main_diameter: float = Field(
        ...,
        ge=0.006,
        le=0.050,
        allow_inf_nan=False,
        description="Diameter tulangan utama dalam meter",
    )
    main_quantity: int = Field(
        ...,
        gt=0,
        le=200,
        description="Jumlah batang tulangan utama",
    )
    main_grade: str = Field(
        default="BJTS 420",
        min_length=2,
        max_length=16,
        pattern=r"^[A-Z0-9\s\-]+$",
        description="Mutu baja tulangan (contoh: BJTS 420)",
    )
    stirrup_diameter: Optional[float] = Field(
        default=None,
        ge=0.006,
        le=0.025,
        allow_inf_nan=False,
        description="Diameter tulangan sengkang dalam meter",
    )
    stirrup_spacing: Optional[float] = Field(
        default=None,
        ge=0.05,
        le=0.50,
        allow_inf_nan=False,
        description="Jarak antar sengkang dalam meter",
    )
    cover: float = Field(
        default=0.04,
        ge=0.01,
        le=0.10,
        allow_inf_nan=False,
        description="Tebal selimut beton dalam meter",
    )

    @model_validator(mode="after")
    def validate_stirrup_consistency(self) -> "ReinforcementSpecInboundDTO":
        
        has_diameter = self.stirrup_diameter is not None
        has_spacing = self.stirrup_spacing is not None
        if has_diameter != has_spacing:
            raise ValueError(
                "stirrup_diameter dan stirrup_spacing harus diberikan bersamaan."
            )
        return self


class FinishSpecInboundDTO(BaseModel):
   
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
    )

    finish_type: FinishType = Field(...)
    material_id: Optional[str] = Field(
        default=None,
        min_length=5,
        max_length=64,
        pattern=r"^mat_[a-z0-9_]+$",
        description="ID material terkait (format mat_xxxxx)",
    )
    thickness: Optional[float] = Field(
        default=None,
        ge=0.001,
        le=0.10,
        allow_inf_nan=False,
        description="Ketebalan lapisan finishing dalam meter",
    )
    area: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=500000.0,
        allow_inf_nan=False,
        description="Luas area pekerjaan finishing dalam m²",
    )


# ---------------------------------------------------------------------------
# Domain Models – Pure Business & Engineering Logical Invariants
# ---------------------------------------------------------------------------
def _to_decimal(value: Any, field_name: str) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, Length):
        return value.value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return Decimal(str(value))
    raise TypeError(f"{field_name} harus berupa angka (int/float/Length/Decimal).")

class Opening:
   
    def __init__(
        self,
        width: float,
        height: float,
        position: float,
        opening_type: OpeningType,
    ) -> None:
        # Validasi invarian internal (defense-in-depth)
        if not (0.1 < width <= 15.0) or not (0.1 < height <= 15.0):
            raise ValueError("Dimensi fisik bukaan di luar batas struktural aman arsitektur.")
        if not (0.0 <= position <= 1000.0):
            raise ValueError("Posisi penempatan bukaan di luar batas elemen induk.")

        self._width = _to_decimal(width, "width")
        self._height = _to_decimal(height, "height")
        self._position = _to_decimal(position, "position")
        self._opening_type = opening_type

    @property
    def width(self) -> Decimal:
        return self._width

    @property
    def height(self) -> Decimal:
        return self._height

    @property
    def position(self) -> Decimal:
        return self._position

    @property
    def opening_type(self) -> OpeningType:
        return self._opening_type

    def calculate_deduction_area(self) -> Decimal:
       
        return self._width * self._height

    def to_domain_state(self) -> Dict[str, Any]:
        
        return {
            "width": float(self._width),
            "height": float(self._height),
            "position": float(self._position),
            "opening_type": self._opening_type.value,
        }


class ReinforcementSpec:
    
    def __init__(
        self,
        main_diameter: float,
        main_quantity: int,
        main_grade: str,
        stirrup_diameter: Optional[float],
        stirrup_spacing: Optional[float],
        cover: float,
    ) -> None:
        # Validasi silang internal (civil engineering code compliance)
        if not (0.006 <= main_diameter <= 0.050):
            raise ValueError("Diameter tulangan utama melanggar standar baja struktural.")
        if not (0 < main_quantity <= 200):
            raise ValueError("Jumlah tulangan utama di luar batas yang diizinkan.")
        if not (0.01 <= cover <= 0.10):
            raise ValueError("Tebal selimut beton di luar rentang proteksi korosi.")

        if stirrup_diameter is not None and not (0.006 <= stirrup_diameter <= 0.025):
            raise ValueError("Diameter sengkang tidak standar.")
        if stirrup_spacing is not None and not (0.05 <= stirrup_spacing <= 0.50):
            raise ValueError("Spasi sengkang melanggar batas keamanan geser.")
        if (stirrup_diameter is None) != (stirrup_spacing is None):
            raise ValueError("Parameter sengkang harus lengkap (diameter dan spasi).")

        self._main_diameter = _to_decimal(main_diameter, "main_diameter")
        self._main_quantity = main_quantity
        self._main_grade = main_grade
        self._stirrup_diameter = (
            _to_decimal(stirrup_diameter, "stirrup_diameter")
            if stirrup_diameter is not None
            else None
        )
        self._stirrup_spacing = (
            _to_decimal(stirrup_spacing, "stirrup_spacing")
            if stirrup_spacing is not None
            else None
        )
        self._cover = _to_decimal(cover, "cover")

    @property
    def main_diameter(self) -> Decimal:
        return self._main_diameter

    @property
    def main_quantity(self) -> int:
        return self._main_quantity

    @property
    def main_grade(self) -> str:
        return self._main_grade

    @property
    def stirrup_diameter(self) -> Optional[Decimal]:
        return self._stirrup_diameter

    @property
    def stirrup_spacing(self) -> Optional[Decimal]:
        return self._stirrup_spacing

    @property
    def cover(self) -> Decimal:
        return self._cover

    def to_domain_state(self) -> Dict[str, Any]:
        """Serialisasi ke dictionary snake_case."""
        return {
            "main_diameter": float(self._main_diameter),
            "main_quantity": self._main_quantity,
            "main_grade": self._main_grade,
            "stirrup_diameter": (
                float(self._stirrup_diameter) if self._stirrup_diameter is not None else None
            ),
            "stirrup_spacing": (
                float(self._stirrup_spacing) if self._stirrup_spacing is not None else None
            ),
            "cover": float(self._cover),
        }


class FinishSpec:
    
    def __init__(
        self,
        finish_type: FinishType,
        material_id: Optional[str],
        thickness: Optional[float],
        area: Optional[float],
    ) -> None:
        if thickness is not None and not (0.001 <= thickness <= 0.10):
            raise ValueError("Ketebalan finishing di luar toleransi konstruksi.")
        if area is not None and not (0.0 <= area <= 500000.0):
            raise ValueError("Luas area finishing melampaui batas proyek.")

        self._finish_type = finish_type
        self._material_id = material_id
        self._thickness = (
            _to_decimal(thickness, "thickness") if thickness is not None else None
        )
        self._area = _to_decimal(area, "area") if area is not None else None

    @property
    def finish_type(self) -> FinishType:
        return self._finish_type

    @property
    def material_id(self) -> Optional[str]:
        return self._material_id

    @property
    def thickness(self) -> Optional[Decimal]:
        return self._thickness

    @property
    def area(self) -> Optional[Decimal]:
        return self._area

    def calculate_consumption_volume(self) -> Optional[Decimal]:
       
        if self._thickness is not None and self._area is not None:
            return self._area * self._thickness
        return None

    def to_domain_state(self) -> Dict[str, Any]:
        
        return {
            "finish_type": self._finish_type.value,
            "material_id": self._material_id,
            "thickness": float(self._thickness) if self._thickness is not None else None,
            "area": float(self._area) if self._area is not None else None,
        }