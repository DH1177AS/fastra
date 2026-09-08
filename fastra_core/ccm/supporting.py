# fastra_core\ccm\supporting.py

from __future__ import annotations

import enum
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from fastra_core.ccm.physical import Coordinate, CoordinateDTO


class GridType(str, enum.Enum):
   
    CARTESIAN = "CARTESIAN"
    RADIAL = "RADIAL"
    COMBINED = "COMBINED"


class LevelType(str, enum.Enum):
   
    GROUND = "GROUND"
    STOREY = "STOREY"
    ROOF = "ROOF"
    FOUNDATION = "FOUNDATION"
    REFERENCE = "REFERENCE"


class SupportingOpeningType(str, enum.Enum):
  
    DOOR = "DOOR"
    WINDOW = "WINDOW"
    VENT = "VENT"
    PASSAGE = "PASSAGE"
    SHAFT = "SHAFT"
    SKYLIGHT = "SKYLIGHT"


class SupportingEntityType(str, enum.Enum):
  
    SPATIAL = "SPATIAL"
    PHYSICAL = "PHYSICAL"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Gateway & Sanitization (Fail-Fast)
# ---------------------------------------------------------------------------
class GridAxisInboundDTO(BaseModel):
   
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    name: str = Field(
        ..., min_length=1, max_length=16, pattern=r"^[A-Za-z0-9_\-\.\s]+$"
    )
    start: Optional[CoordinateDTO] = Field(default=None)
    end: Optional[CoordinateDTO] = Field(default=None)
    is_primary: bool = Field(default=True)


class GridIntersectionInboundDTO(BaseModel):
  
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    axis_1: str = Field(
        ..., min_length=1, max_length=16, pattern=r"^[A-Za-z0-9_\-\.\s]+$"
    )
    axis_2: str = Field(
        ..., min_length=1, max_length=16, pattern=r"^[A-Za-z0-9_\-\.\s]+$"
    )
    coordinate: Optional[CoordinateDTO] = Field(default=None)


class GridInboundDTO(BaseModel):
    
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    grid_type: GridType = Field(default=GridType.CARTESIAN)
    axes: List[GridAxisInboundDTO] = Field(default_factory=list, max_length=500)
    intersections: List[GridIntersectionInboundDTO] = Field(
        default_factory=list, max_length=25000
    )

    @field_validator("axes", mode="after")
    @classmethod
    def validate_cartesian_axes_count(
        cls, value: List[GridAxisInboundDTO], info: Any
    ) -> List[GridAxisInboundDTO]:
       
        grid_type = info.data.get("grid_type", GridType.CARTESIAN)
        if grid_type == GridType.CARTESIAN and len(value) < 2:
            raise ValueError(
                "Sistem Grid berjenis CARTESIAN sekurang-kurangnya membutuhkan 2 sumbu koordinat aktif."
            )
        return value


class LevelInboundDTO(BaseModel):
   
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    elevation: float = Field(..., ge=-50.0, le=1000.0, allow_inf_nan=False)
    level_type: LevelType = Field(default=LevelType.GROUND)
    name: str = Field(..., min_length=2, max_length=64)


class SupportingOpeningInboundDTO(BaseModel):
   
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    opening_type: SupportingOpeningType = Field(default=SupportingOpeningType.DOOR)
    width: float = Field(..., gt=0.01, le=50.0, allow_inf_nan=False)
    height: float = Field(..., gt=0.01, le=50.0, allow_inf_nan=False)
    position: float = Field(..., ge=0.0, le=5000.0, allow_inf_nan=False)
    host_element: Optional[str] = Field(
        default=None, min_length=5, max_length=64, pattern=r"^[a-z0-9_]+$"
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
            f"Field '{field_name}' gagal dikonversi ke representasi Decimal imutabel."
        ) from exc


# ---------------------------------------------------------------------------
# Domain Models – Pure Business & Geometrical Supporting Invariants
# ---------------------------------------------------------------------------
class GridAxis:
   
    def __init__(
        self,
        name: str,
        start: Optional[Coordinate] = None,
        end: Optional[Coordinate] = None,
        is_primary: bool = True,
    ) -> None:
        if not name.strip():
            raise ValueError(
                "Identifikasi identitas nama sumbu GridAxis dilarang berupa spasi kosong."
            )

        self._name = name.strip()
        self._start = start
        self._end = end
        self._is_primary = is_primary

    @property
    def name(self) -> str:
        return self._name

    @property
    def start(self) -> Optional[Coordinate]:
        return self._start

    @property
    def end(self) -> Optional[Coordinate]:
        return self._end

    @property
    def is_primary(self) -> bool:
        return self._is_primary

    def calculate_axis_length(self) -> Optional[Decimal]:
        
        if self._start is not None and self._end is not None:
            return self._start.distance_to(self._end)
        return None

    def to_domain_state(self) -> Dict[str, Any]:
       
        return {
            "name": self._name,
            "is_primary": self._is_primary,
            "axis_length": (
                float(length) if (length := self.calculate_axis_length()) is not None else None
            ),
        }


class GridIntersection:
  
    def __init__(
        self,
        axis_1: str,
        axis_2: str,
        coordinate: Optional[Coordinate] = None,
    ) -> None:
        if not axis_1.strip() or not axis_2.strip():
            raise ValueError(
                "Parameter relasi identitas penamaan sumbu axis_1/axis_2 tidak boleh kosong."
            )
        if axis_1.strip() == axis_2.strip():
            raise ValueError(
                "Kalkulasi anomali: Titik persilangan dilarang merujuk pada sumbu grid yang sama."
            )

        self._axis_1 = axis_1.strip()
        self._axis_2 = axis_2.strip()
        self._coordinate = coordinate

    @property
    def axis_1(self) -> str:
        return self._axis_1

    @property
    def axis_2(self) -> str:
        return self._axis_2

    @property
    def coordinate(self) -> Optional[Coordinate]:
        return self._coordinate

    def to_domain_state(self) -> Dict[str, Any]:
        
        return {
            "axis_1": self._axis_1,
            "axis_2": self._axis_2,
            "has_coordinate": self._coordinate is not None,
        }


class Grid:
   
    def __init__(
        self,
        grid_type: GridType,
        axes: List[GridAxis],
        intersections: List[GridIntersection],
    ) -> None:
        if grid_type == GridType.CARTESIAN and len(axes) < 2:
            raise ValueError(
                "Sistem Grid berjenis CARTESIAN membutuhkan minimal 2 sumbu aktif."
            )

        self._grid_type = grid_type
        self._axes = list(axes)
        self._intersections = list(intersections)
        self._entity_type = SupportingEntityType.SPATIAL

    @property
    def grid_type(self) -> GridType:
        return self._grid_type

    @property
    def axes(self) -> List[GridAxis]:
        return list(self._axes)

    @property
    def intersections(self) -> List[GridIntersection]:
        return list(self._intersections)

    def to_domain_state(self) -> Dict[str, Any]:
        
        return {
            "grid_type": self._grid_type.value,
            "axes_count": len(self._axes),
            "intersections_count": len(self._intersections),
            "entity_type": self._entity_type.value,
        }


class Level:

    def __init__(
        self,
        elevation: float,
        level_type: LevelType,
        name: str,
    ) -> None:
        if elevation < -50.0 or elevation > 1000.0:
            raise ValueError("Elevasi level berada di luar rentang yang diizinkan.")
        if not name.strip():
            raise ValueError("Nama level tidak boleh kosong.")

        self._elevation = _to_decimal(elevation, "elevation")
        self._level_type = level_type
        self._name = name.strip()
        self._entity_type = SupportingEntityType.SPATIAL

    @property
    def elevation(self) -> Decimal:
        return self._elevation

    @property
    def level_type(self) -> LevelType:
        return self._level_type

    @property
    def name(self) -> str:
        return self._name

    def calculate_relative_distance_to(self, other_level: "Level") -> Decimal:
       
        return abs(self._elevation - other_level.elevation)

    def to_domain_state(self) -> Dict[str, Any]:
       
        return {
            "elevation": float(self._elevation),
            "level_type": self._level_type.value,
            "name": self._name,
            "entity_type": self._entity_type.value,
        }


class Opening:
    
    def __init__(
        self,
        opening_type: SupportingOpeningType,
        width: float,
        height: float,
        position: float,
        host_element: Optional[str] = None,
    ) -> None:
        if width <= 0.01 or width > 50.0:
            raise ValueError("Lebar bukaan di luar batas yang diizinkan.")
        if height <= 0.01 or height > 50.0:
            raise ValueError("Tinggi bukaan di luar batas yang diizinkan.")
        if position < 0.0 or position > 5000.0:
            raise ValueError("Posisi bukaan di luar rentang yang diizinkan.")

        self._opening_type = opening_type
        self._width = _to_decimal(width, "width")
        self._height = _to_decimal(height, "height")
        self._position = _to_decimal(position, "position")
        self._host_element = host_element
        self._entity_type = SupportingEntityType.PHYSICAL

    @property
    def opening_type(self) -> SupportingOpeningType:
        return self._opening_type

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
    def host_element(self) -> Optional[str]:
        return self._host_element

    def calculate_deduction_area(self) -> Decimal:
       
        return self._width * self._height

    def to_domain_state(self) -> Dict[str, Any]:
      
        return {
            "opening_type": self._opening_type.value,
            "width": float(self._width),
            "height": float(self._height),
            "position": float(self._position),
            "host_element": self._host_element,
            "deduction_area": float(self.calculate_deduction_area()),
            "entity_type": self._entity_type.value,
        }