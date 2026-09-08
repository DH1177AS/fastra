# fastra_core\ccm\spatial.py

from __future__ import annotations

import enum
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from fastra_core.primitives.area import Area
from fastra_core.ccm.physical import (
    Coordinate,
    CoordinateDTO,
    _calculate_polygon_area,
    _ensure_closed,
    _is_self_intersecting,
)


class SpatialEntityType(str, enum.Enum):
  
    SPATIAL = "SPATIAL"


class SpatialBuildingType(str, enum.Enum):
  
    HOUSE = "HOUSE"
    OFFICE = "OFFICE"
    WAREHOUSE = "WAREHOUSE"
    HIGH_RISE = "HIGH_RISE"
    INFRASTRUCTURE = "INFRASTRUCTURE"


class RoomType(str, enum.Enum):
   
    LIVING = "LIVING"
    BEDROOM = "BEDROOM"
    KITCHEN = "KITCHEN"
    BATHROOM = "BATHROOM"
    OFFICE = "OFFICE"
    CORRIDOR = "CORRIDOR"
    STORAGE = "STORAGE"
    MECHANICAL = "MECHANICAL"


class ZoneType(str, enum.Enum):
  
    HVAC = "HVAC"
    FIRE = "FIRE"
    SECURITY = "SECURITY"
    ACOUSTIC = "ACOUSTIC"
    CUSTOM = "CUSTOM"


# ---------------------------------------------------------------------------
# Inbound DTOs – Pydantic Strict Gateway & Sanitization (Fail-Fast)
# ---------------------------------------------------------------------------
class SiteInboundDTO(BaseModel):
   
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    boundary: List[CoordinateDTO] = Field(..., min_length=3, max_length=500)
    address: str = Field(..., min_length=5, max_length=512)
    geo_location: Optional[Dict[str, float]] = Field(default=None, max_length=10)
    zoning: str = Field(
        ..., min_length=2, max_length=64, pattern=r"^[A-Z0-9_\-\s]+$"
    )

    @field_validator("geo_location", mode="after")
    @classmethod
    def validate_geo_coordinates(
        cls, value: Optional[Dict[str, float]]
    ) -> Optional[Dict[str, float]]:
       
        if value is not None:
            required_keys = {"latitude", "longitude"}
            if not required_keys.issubset(value.keys()):
                raise ValueError(
                    "Skema geo_location wajib mengandung komponen 'latitude' dan 'longitude'."
                )
            if not (-90.0 <= value["latitude"] <= 90.0) or not (
                -180.0 <= value["longitude"] <= 180.0
            ):
                raise ValueError(
                    "Parameter koordinat geografis garis lintang/bujur melanggar batas rotasi bumi."
                )
        return value


class BuildingInboundDTO(BaseModel):
 
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    building_type: SpatialBuildingType = Field(default=SpatialBuildingType.HOUSE)
    number_of_storeys: int = Field(default=1, gt=0, le=200)
    footprint: List[CoordinateDTO] = Field(..., min_length=3, max_length=500)
    height: float = Field(..., gt=0.1, le=1000.0, allow_inf_nan=False)


class StoreyInboundDTO(BaseModel):
  
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    level: int = Field(..., ge=-10, le=200)
    elevation: float = Field(..., ge=-50.0, le=1000.0, allow_inf_nan=False)
    height: float = Field(..., gt=0.1, le=20.0, allow_inf_nan=False)
    building_id: Optional[str] = Field(
        default=None, min_length=5, max_length=64, pattern=r"^bld_[a-z0-9_]+$"
    )


class RoomInboundDTO(BaseModel):
  
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    room_type: RoomType = Field(default=RoomType.LIVING)
    boundary: List[CoordinateDTO] = Field(..., min_length=3, max_length=500)
    storey_id: Optional[str] = Field(
        default=None, min_length=5, max_length=64, pattern=r"^sty_[a-z0-9_]+$"
    )
    finish: Optional[Dict[str, Any]] = Field(default=None, max_length=50)


class ZoneInboundDTO(BaseModel):
  
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    zone_type: ZoneType = Field(default=ZoneType.HVAC)
    rooms: List[str] = Field(default_factory=list, max_length=1000)
    area: float = Field(..., ge=0.0, le=1e8, allow_inf_nan=False)

    @field_validator("rooms", mode="after")
    @classmethod
    def validate_room_references(cls, value: List[str]) -> List[str]:
       
        for r in value:
            if not r.strip() or not r.startswith("rom_"):
                raise ValueError(
                    "Kode identifikasi referensi kamar wajib diawali dengan prefiks 'rom_'."
                )
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
        raise ValueError(
            f"Field '{field_name}' gagal dikonversi ke representasi Decimal."
        ) from exc


# ---------------------------------------------------------------------------
# Domain Models – Pure Business & Geometrical Spatial Invariants
# ---------------------------------------------------------------------------
class Site:
  
    def __init__(
        self,
        boundary: List[Coordinate],
        address: str,
        zoning: str,
        geo_location: Optional[Dict[str, float]] = None,
    ) -> None:
        if len(boundary) < 3:
            raise ValueError("Batas lahan (boundary) minimal memerlukan 3 titik koordinat.")
        if not address.strip():
            raise ValueError("Alamat lahan tidak boleh kosong.")
        if not zoning.strip():
            raise ValueError("Zonasi lahan tidak boleh kosong.")
        if _is_self_intersecting(boundary):
            raise ValueError("Perimeter batas lahan terdeteksi saling bersilangan (self-intersecting).")
        if geo_location is not None:
            if "latitude" not in geo_location or "longitude" not in geo_location:
                raise ValueError("geo_location harus memiliki kunci latitude dan longitude.")
            if not (-90.0 <= geo_location["latitude"] <= 90.0) or not (
                -180.0 <= geo_location["longitude"] <= 180.0
            ):
                raise ValueError("Koordinat geo_location di luar rentang valid.")

        self._boundary = _ensure_closed(boundary)
        self._address = address.strip()
        self._zoning = zoning.strip()
        self._geo_location = dict(geo_location) if geo_location is not None else None
        self._entity_type = SpatialEntityType.SPATIAL

    @property
    def boundary(self) -> List[Coordinate]:
        return list(self._boundary)

    @property
    def address(self) -> str:
        return self._address

    @property
    def zoning(self) -> str:
        return self._zoning

    @property
    def geo_location(self) -> Optional[Dict[str, float]]:
        return dict(self._geo_location) if self._geo_location is not None else None

    def calculate_site_area(self) -> Decimal:
        
        area_val = _calculate_polygon_area(self._boundary)
        if area_val <= Decimal("0"):
            raise ValueError(
                "Hasil komputasi matematis area tapak lahan (Site) dilarang bernilai nol atau negatif."
            )
        return area_val

    def to_domain_state(self) -> Dict[str, Any]:
        
        return {
            "address": self._address,
            "zoning": self._zoning,
            "geo_location": dict(self._geo_location) if self._geo_location is not None else None,
            "site_area": float(self.calculate_site_area()),
            "entity_type": self._entity_type.value,
        }


class Building:
  
    def __init__(
        self,
        building_type: SpatialBuildingType,
        number_of_storeys: int,
        footprint: List[Coordinate],
        height: float,
    ) -> None:
        if number_of_storeys <= 0 or number_of_storeys > 200:
            raise ValueError(
                "Jumlah kapasitas lantai (number_of_storeys) melanggar batas regulasi sipil bangunan bertingkat."
            )
        if len(footprint) < 3:
            raise ValueError("Denah tapak kaki bangunan minimal memerlukan 3 koordinat.")
        if height <= 0.1 or height > 1000.0:
            raise ValueError("Tinggi total bangunan di luar batas teknis.")
        if _is_self_intersecting(footprint):
            raise ValueError("Perimeter footprint bangunan saling bersilangan (self-intersecting).")

        self._building_type = building_type
        self._number_of_storeys = number_of_storeys
        self._footprint = _ensure_closed(footprint)
        self._height = _to_decimal(height, "height")
        self._entity_type = SpatialEntityType.SPATIAL

    @property
    def building_type(self) -> SpatialBuildingType:
        return self._building_type

    @property
    def number_of_storeys(self) -> int:
        return self._number_of_storeys

    @property
    def height(self) -> Decimal:
        return self._height

    def calculate_footprint_area(self) -> Decimal:
        
        area_val = _calculate_polygon_area(self._footprint)
        if area_val <= Decimal("0"):
            raise ValueError("Luas tapak kaki bangunan tidak valid.")
        return area_val

    def calculate_total_floor_area(self) -> Decimal:
       
        multiplier = Decimal(str(self._number_of_storeys))
        return self.calculate_footprint_area() * multiplier

    def to_domain_state(self) -> Dict[str, Any]:
       
        return {
            "building_type": self._building_type.value,
            "number_of_storeys": self._number_of_storeys,
            "height": float(self._height),
            "footprint_area": float(self.calculate_footprint_area()),
            "total_floor_area": float(self.calculate_total_floor_area()),
            "entity_type": self._entity_type.value,
        }


class Storey:
   
    def __init__(
        self,
        level: int,
        elevation: float,
        height: float,
        building_id: Optional[str] = None,
    ) -> None:
        if height <= 0.1 or height > 20.0:
            raise ValueError(
                "Tinggi ruang bersih per lantai bangunan (height) melanggar ambang batas teknik arsitektur."
            )
        if elevation < -50.0 or elevation > 1000.0:
            raise ValueError("Elevasi lantai di luar rentang yang diizinkan.")

        self._level = level
        self._elevation = _to_decimal(elevation, "elevation")
        self._height = _to_decimal(height, "height")
        self._building_id = building_id
        self._entity_type = SpatialEntityType.SPATIAL

    @property
    def level(self) -> int:
        return self._level

    @property
    def elevation(self) -> Decimal:
        return self._elevation

    @property
    def height(self) -> Decimal:
        return self._height

    @property
    def building_id(self) -> Optional[str]:
        return self._building_id

    def calculate_top_elevation(self) -> Decimal:
       
        return self._elevation + self._height

    def to_domain_state(self) -> Dict[str, Any]:
       
        return {
            "level": self._level,
            "elevation": float(self._elevation),
            "height": float(self._height),
            "top_elevation": float(self.calculate_top_elevation()),
            "building_id": self._building_id,
            "entity_type": self._entity_type.value,
        }


class Room:
    def __init__(
        self,
        name: str = "",
        boundary: Optional[List[Coordinate]] = None,
        room_type: RoomType = RoomType.LIVING,
        storey_id: Optional[str] = None,
        finish: Optional[Dict[str, Any]] = None,
    ) -> None:
        if boundary is None:
            raise ValueError("boundary wajib diisi")
        if not name or not name.strip():
            raise ValueError("Nama ruangan tidak boleh kosong.")
        if len(boundary) < 3:
            raise ValueError("Batas ruangan (boundary) minimal memerlukan 3 titik koordinat.")
        if _is_self_intersecting(boundary):
            raise ValueError("Perimeter batas ruangan saling bersilangan (self-intersecting).")
        if finish is not None and not isinstance(finish, dict):
            raise TypeError("finish harus berupa dictionary.")

        self._name = name.strip()
        self._room_type = room_type
        self._boundary = list(boundary)   
        self._is_closed = (
            len(boundary) >= 3 and
            boundary[0].x == boundary[-1].x and
            boundary[0].y == boundary[-1].y and
            boundary[0].z == boundary[-1].z
        )
        self._storey_id = storey_id
        self._finish = dict(finish) if finish is not None else {}
        self._entity_type = SpatialEntityType.SPATIAL

    @property
    def name(self) -> str:
        return self._name

    @property
    def room_type(self) -> RoomType:
        return self._room_type

    @property
    def boundary(self) -> List[Coordinate]:
        return list(self._boundary)

    @property
    def storey_id(self) -> Optional[str]:
        return self._storey_id

    @property
    def finish(self) -> Dict[str, Any]:
        return dict(self._finish)

    @property
    def area(self) -> Area:
        return Area(value=self.calculate_room_area())

    @property
    def is_closed(self) -> bool:
        if len(self._boundary) < 3:
            return False
        first = self._boundary[0]
        last = self._boundary[-1]
        return first.x == last.x and first.y == last.y and first.z == last.z

    def calculate_room_area(self) -> Decimal:
        area_val = _calculate_polygon_area(self._boundary)
        if area_val <= Decimal("0"):
            raise ValueError("Hasil hitung area ruangan dilarang bernilai nol.")
        return area_val

    def to_domain_state(self) -> Dict[str, Any]:
        return {
            "name": self._name,
            "room_type": self._room_type.value,
            "storey_id": self._storey_id,
            "finish_spec": dict(self._finish),
            "room_area": float(self.calculate_room_area()),
            "entity_type": self._entity_type.value,
        }


class Zone:
   
    def __init__(
        self,
        zone_type: ZoneType,
        rooms: List[str],
        area: float,
    ) -> None:
        if area < 0.0:
            raise ValueError("Luas zona tidak boleh negatif.")
        if not rooms:
            raise ValueError("Zona minimal harus memiliki satu referensi ruangan.")
       
        cleaned_rooms = []
        for r in rooms:
            r_clean = r.strip()
            if not r_clean.startswith("rom_"):
                raise ValueError("Kode ruangan harus diawali dengan 'rom_'.")
            cleaned_rooms.append(r_clean)
        if len(cleaned_rooms) != len(rooms):
            raise ValueError("Terdapat referensi ruangan kosong atau tidak valid.")

        self._zone_type = zone_type
        self._rooms = cleaned_rooms
        self._area = _to_decimal(area, "area")
        self._entity_type = SpatialEntityType.SPATIAL

    @property
    def zone_type(self) -> ZoneType:
        return self._zone_type

    @property
    def rooms(self) -> List[str]:
        return list(self._rooms)

    @property
    def area(self) -> Decimal:
        return self._area

    def verify_and_update_zone_area(self, derived_room_areas: List[Decimal]) -> Decimal:
      
        summed_area = sum(derived_room_areas)
        self._area = summed_area.quantize(Decimal("0.01"))
        return self._area

    def to_domain_state(self) -> Dict[str, Any]:
       
        return {
            "zone_type": self._zone_type.value,
            "rooms": list(self._rooms),
            "allocated_area": float(self._area),
            "entity_type": self._entity_type.value,
        }