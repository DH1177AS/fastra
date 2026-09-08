# fastra_core/ccm/physical.py

from __future__ import annotations

import enum
import math
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from fastra_core.ccm.common import (
    FinishSpec,
    Opening,
    OpeningType,
    ReinforcementSpec,
)
from fastra_core.primitives.length import Length
from fastra_core.primitives.area import Area
from fastra_core.primitives.volume import Volume
from fastra_core.primitives.angle import Angle


# ---------------------------------------------------------------------------
# ENUM DEFINITIONS 
# ---------------------------------------------------------------------------
class StructuralWallType(str, enum.Enum):
    LOAD_BEARING = "LOAD_BEARING"
    NON_LOAD_BEARING = "NON_LOAD_BEARING"
    SHEAR = "SHEAR"
    RETAINING = "RETAINING"


class ConstructionWallType(str, enum.Enum):
    BATA_MERAH = "BATA_MERAH"
    BATA_RINGAN = "BATA_RINGAN"
    BETON_BERTULANG = "BETON_BERTULANG"
    KAYU = "KAYU"
    GYPSUM = "GYPSUM"
    PARTISI = "PARTISI"


class ColumnType(str, enum.Enum):
    TIANG = "TIANG"
    KOLOM_STRUKTUR = "KOLOM_STRUKTUR"
    KOLOM_PRAKTIS = "KOLOM_PRAKTIS"


class BeamType(str, enum.Enum):
    SLOOF = "SLOOF"
    BALOK_INDUK = "BALOK_INDUK"
    BALOK_ANAK = "BALOK_ANAK"
    RING_BALK = "RING_BALK"


class EntityType(str, enum.Enum):
    PHYSICAL = "PHYSICAL"


class SlabType(str, enum.Enum):
    PLAT_LANTAI = "PLAT_LANTAI"
    PLAT_ATAP = "PLAT_ATAP"
    PLAT_CANTILEVER = "PLAT_CANTILEVER"


class FoundationType(str, enum.Enum):
    FOOTPLATE = "FOOTPLATE"
    BATU_KALI = "BATU_KALI"
    BORE_PILE = "BORE_PILE"
    TIANG_PANCANG = "TIANG_PANCANG"
    RAFT = "RAFT"


class RoofType(str, enum.Enum):
    GABLE = "GABLE"
    HIP = "HIP"
    FLAT = "FLAT"
    SHED = "SHED"


class RoofStructureType(str, enum.Enum):
    BAJA_RINGAN = "BAJA_RINGAN"
    KAYU = "KAYU"
    BAJA_KONVENSIONAL = "BAJA_KONVENSIONAL"
    BETON_PLAT = "BETON_PLAT"


class DoorType(str, enum.Enum):
    SINGLE = "SINGLE"
    DOUBLE = "DOUBLE"
    SLIDING = "SLIDING"
    FOLDING = "FOLDING"


class WindowType(str, enum.Enum):
    CASEMENT = "CASEMENT"
    SLIDING = "SLIDING"
    AWNING = "AWNING"
    FIXED = "FIXED"


class GlazingType(str, enum.Enum):
    CLEAR = "CLEAR"
    TINTED = "TINTED"
    FROSTED = "FROSTED"
    LOW_E = "LOW_E"


class StairStructureType(str, enum.Enum):
    CONCRETE = "CONCRETE"
    STEEL = "STEEL"
    WOOD = "WOOD"


class RampSurfaceType(str, enum.Enum):
    CONCRETE = "CONCRETE"
    ASPHALT = "ASPHALT"
    PAVING = "PAVING"


# ---------------------------------------------------------------------------
# COORDINATE
# ---------------------------------------------------------------------------
class CoordinateDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    x: float = Field(..., ge=-1e6, le=1e6, allow_inf_nan=False)
    y: float = Field(..., ge=-1e6, le=1e6, allow_inf_nan=False)
    z: float = Field(default=0.0, ge=-1e4, le=1e4, allow_inf_nan=False)


class Coordinate:
    def __init__(self, x: float | int | Decimal, y: float | int | Decimal, z: float | int | Decimal = 0.0) -> None:
        self._x = Decimal(str(x))
        self._y = Decimal(str(y))
        self._z = Decimal(str(z))

    @property
    def x(self) -> Decimal:
        return self._x

    @property
    def y(self) -> Decimal:
        return self._y

    @property
    def z(self) -> Decimal:
        return self._z

    def distance_to(self, other: Coordinate) -> Decimal:
        dx = float(self._x - other.x)
        dy = float(self._y - other.y)
        dz = float(self._z - other.z)
        dist_float = math.sqrt(dx * dx + dy * dy + dz * dz)
        return Decimal(str(dist_float))


# ---------------------------------------------------------------------------
# UTILITIES
# ---------------------------------------------------------------------------
def _to_decimal(value: Any, field_name: str) -> Decimal:
    """Mengonversi berbagai tipe input menjadi Decimal dengan validasi ketat."""
    if isinstance(value, Length):
        return value.value
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            return Decimal(str(value))
        except InvalidOperation as exc:
            raise ValueError(f"Field '{field_name}' gagal dikonversi ke Decimal.") from exc
    raise TypeError(f"Field '{field_name}' wajib bertipe numerik dasar (int/float/Decimal/Length).")


def _ensure_closed(points: List[Coordinate]) -> List[Coordinate]:
    if not points:
        return []
    pts = list(points)
    if pts[0].x != pts[-1].x or pts[0].y != pts[-1].y or pts[0].z != pts[-1].z:
        pts.append(pts[0])
    return pts


def _calculate_polygon_area(points: List[Coordinate]) -> Decimal:
    if len(points) < 3:
        return Decimal("0.00")
    closed_pts = _ensure_closed(points)
    n = len(closed_pts)
    area_sum = Decimal("0.00")
    for i in range(n - 1):
        x1 = Decimal(str(closed_pts[i].x))
        y1 = Decimal(str(closed_pts[i].y))
        x2 = Decimal(str(closed_pts[i + 1].x))
        y2 = Decimal(str(closed_pts[i + 1].y))
        area_sum += (x1 * y2) - (x2 * y1)
    return abs(area_sum / Decimal("2.00"))


def _orientation(a: Coordinate, b: Coordinate, c: Coordinate) -> int:
    val = (float(b.y) - float(a.y)) * (float(c.x) - float(b.x)) - (float(b.x) - float(a.x)) * (float(c.y) - float(b.y))
    if abs(val) < 1e-12:
        return 0
    return 1 if val > 0 else -1


def _on_segment(a: Coordinate, b: Coordinate, c: Coordinate) -> bool:
    return (
        min(float(a.x), float(b.x)) <= float(c.x) <= max(float(a.x), float(b.x))
        and min(float(a.y), float(b.y)) <= float(c.y) <= max(float(a.y), float(b.y))
    )


def _segments_intersect(p1: Coordinate, q1: Coordinate, p2: Coordinate, q2: Coordinate) -> bool:
    o1 = _orientation(p1, q1, p2)
    o2 = _orientation(p1, q1, q2)
    o3 = _orientation(p2, q2, p1)
    o4 = _orientation(p2, q2, q1)
    if o1 != o2 and o3 != o4:
        return True
    if o1 == 0 and _on_segment(p1, q1, p2):
        return True
    if o2 == 0 and _on_segment(p1, q1, q2):
        return True
    if o3 == 0 and _on_segment(p2, q2, p1):
        return True
    if o4 == 0 and _on_segment(p2, q2, q1):
        return True
    return False


def _is_self_intersecting(points: List[Coordinate]) -> bool:
    if len(points) < 4:
        return False
    closed_pts = _ensure_closed(points)
    n = len(closed_pts)
    seg_count = n - 1
    for i in range(seg_count):
        p1 = closed_pts[i]
        q1 = closed_pts[i + 1]
        for j in range(i + 1, seg_count):
            if j == i + 1 or (i == 0 and j == seg_count - 1):
                continue
            p2 = closed_pts[j]
            q2 = closed_pts[j + 1]
            if _segments_intersect(p1, q1, p2, q2):
                return True
    return False


# ---------------------------------------------------------------------------
# DOMAIN ENTITY CLASSES with primitive properties
# ---------------------------------------------------------------------------
class Wall:
    def __init__(
        self,
        axis_line: Optional[List[Coordinate]] = None,
        height: Any = None,
        thickness: Any = 0.15,
        structural_type: StructuralWallType = StructuralWallType.NON_LOAD_BEARING,
        construction_type: ConstructionWallType = ConstructionWallType.BATA_MERAH,
        base_elevation: Any = 0.0,
        openings: List[Opening] | None = None,
        finish: FinishSpec | None = None,
        name: str = "",
    ) -> None:
        if axis_line is None:
            axis_line = [Coordinate(0, 0, 0), Coordinate(1, 0, 0)]

        height_val = _to_decimal(height, "height") if height is not None else Decimal("3.0")
        thickness_val = _to_decimal(thickness, "thickness")
        base_elevation_val = _to_decimal(base_elevation, "base_elevation")

        if height_val <= Decimal("0.1"):
            raise ValueError("Tinggi dinding harus lebih besar dari 0.1 meter.")
        if thickness_val <= Decimal("0.02"):
            raise ValueError("Ketebalan dinding harus lebih besar dari 0.02 meter.")
        if len(axis_line) < 2:
            raise ValueError("Garis sumbu dinding minimal memerlukan 2 titik koordinat.")
        if base_elevation_val < Decimal("-100.0") or base_elevation_val > Decimal("1000.0"):
            raise ValueError("Elevasi dasar dinding di luar rentang yang diizinkan.")

        self._name = name
        self._axis_line = list(axis_line)
        self._height = height_val
        self._thickness = thickness_val
        self._structural_type = structural_type
        self._construction_type = construction_type
        self._base_elevation = base_elevation_val
        self._openings = list(openings) if openings else []
        self._finish = finish
        self._entity_type = EntityType.PHYSICAL

        gross = self.calculate_gross_area()
        total_deduction = sum(op.calculate_deduction_area() for op in self._openings)
        if total_deduction > gross.value:
            raise ValueError("Total luas bukaan tidak boleh melebihi luas dinding induk.")

    @property
    def name(self) -> str:
        return self._name

    @property
    def height(self) -> Length:
        return Length(value=self._height)

    @property
    def thickness(self) -> Length:
        return Length(value=self._thickness)

    @property
    def gross_area(self) -> Area:
        return Area(value=self.calculate_gross_area().value)

    @property
    def net_area(self) -> Area:
        return Area(value=self.calculate_net_area().value)

    @property
    def openings(self) -> List[Opening]:
        return self._openings

    @property
    def construction_type(self) -> ConstructionWallType:
        return self._construction_type

    @property
    def structural_type(self) -> StructuralWallType:
        return self._structural_type

    def calculate_total_length(self) -> Decimal:
        length_sum = Decimal("0.00")
        for i in range(len(self._axis_line) - 1):
            dist = self._axis_line[i].distance_to(self._axis_line[i + 1])
            if isinstance(dist, Length):
                dist_val = dist.value
            elif isinstance(dist, Decimal):
                dist_val = dist
            else:
                dist_val = Decimal(str(dist))
            length_sum += dist_val
        return length_sum

    def calculate_gross_area(self) -> Area:
        height_decimal = self._height if isinstance(self._height, Decimal) else Decimal(str(self._height))
        return Area(value=self.calculate_total_length() * height_decimal)

    def calculate_net_area(self) -> Area:
        height_decimal = self._height if isinstance(self._height, Decimal) else Decimal(str(self._height))
        total_deduction = sum(op.calculate_deduction_area() for op in self._openings)
        return Area(value=self.calculate_total_length() * height_decimal - total_deduction)

    def to_domain_state(self) -> Dict[str, Any]:
        return {
            "name": self._name,
            "height": float(self._height),
            "thickness": float(self._thickness),
            "structural_type": self._structural_type.value,
            "construction_type": self._construction_type.value,
            "base_elevation": float(self._base_elevation),
            "gross_area": float(self.calculate_gross_area().value),
            "net_area": float(self.calculate_net_area().value),
            "entity_type": self._entity_type.value,
        }


class Column:
    def __init__(
        self,
        width: Any,
        depth: Any,
        height: Any,
        base_elevation: Any = 0.0,
        structural_type: ColumnType = ColumnType.KOLOM_STRUKTUR,
        material_id: str | None = None,
        reinforcement: ReinforcementSpec | None = None,
        name: str = "",
    ) -> None:
        width_val = _to_decimal(width, "width")
        depth_val = _to_decimal(depth, "depth")
        height_val = _to_decimal(height, "height")
        base_elevation_val = _to_decimal(base_elevation, "base_elevation")

        if width_val <= Decimal("0.05") or depth_val <= Decimal("0.05") or height_val <= Decimal("0.1"):
            raise ValueError("Dimensi kolom (lebar, dalam, tinggi) harus positif.")
        if base_elevation_val < Decimal("-100.0") or base_elevation_val > Decimal("1000.0"):
            raise ValueError("Elevasi dasar kolom di luar rentang.")

        self._name = name
        self._width = width_val
        self._depth = depth_val
        self._height = height_val
        self._base_elevation = base_elevation_val
        self._structural_type = structural_type
        self._material_id = material_id
        self._reinforcement = reinforcement
        self._entity_type = EntityType.PHYSICAL

    @property
    def name(self) -> str:
        return self._name

    @property
    def width(self) -> Length:
        return Length(value=self._width)

    @property
    def depth(self) -> Length:
        return Length(value=self._depth)

    @property
    def height(self) -> Length:
        return Length(value=self._height)

    @property
    def volume(self) -> Volume:
        return Volume(value=self.calculate_volume().value)

    @property
    def bekisting_area(self) -> Area:
        return Area(value=self.calculate_bekisting_area().value)

    @property
    def reinforcement(self) -> Optional[ReinforcementSpec]:
        return self._reinforcement

    def calculate_volume(self) -> Volume:
        return Volume(value=self._width * self._depth * self._height)

    def calculate_bekisting_area(self) -> Area:
        perimeter_float = 2.0 * (float(self._width) + float(self._depth))
        area_float = perimeter_float * float(self._height)
        return Area(value=area_float)

    def to_domain_state(self) -> Dict[str, Any]:
        return {
            "name": self._name,
            "width": float(self._width),
            "depth": float(self._depth),
            "height": float(self._height),
            "base_elevation": float(self._base_elevation),
            "structural_type": self._structural_type.value,
            "volume": float(self.calculate_volume().value),
            "bekisting_area": float(self.calculate_bekisting_area().value),
            "entity_type": self._entity_type.value,
        }


class Beam:
    def __init__(
        self,
        width: Any,
        depth: Any,
        length: Any,
        beam_type: BeamType = BeamType.BALOK_INDUK,
        start_connection: str | None = None,
        end_connection: str | None = None,
        reinforcement: ReinforcementSpec | None = None,
        name: str = "",
    ) -> None:
        width_val = _to_decimal(width, "width")
        depth_val = _to_decimal(depth, "depth")
        length_val = _to_decimal(length, "length")

        if width_val <= Decimal("0.05") or depth_val <= Decimal("0.05") or length_val <= Decimal("0.1"):
            raise ValueError("Dimensi balok (lebar, dalam, panjang) harus positif.")

        self._name = name
        self._width = width_val
        self._depth = depth_val
        self._length = length_val
        self._beam_type = beam_type
        self._start_connection = start_connection
        self._end_connection = end_connection
        self._reinforcement = reinforcement
        self._entity_type = EntityType.PHYSICAL

    @property
    def name(self) -> str:
        return self._name

    @property
    def width(self) -> Length:
        return Length(value=self._width)

    @property
    def depth(self) -> Length:
        return Length(value=self._depth)

    @property
    def length(self) -> Length:
        return Length(value=self._length)

    @property
    def volume(self) -> Volume:
        return Volume(value=self.calculate_volume().value)

    def calculate_volume(self) -> Volume:
        return Volume(value=self._width * self._depth * self._length)

    def to_domain_state(self) -> Dict[str, Any]:
        return {
            "name": self._name,
            "width": float(self._width),
            "depth": float(self._depth),
            "length": float(self._length),
            "beam_type": self._beam_type.value,
            "volume": float(self.calculate_volume().value),
            "entity_type": self._entity_type.value,
        }


class Slab:
    def __init__(
        self,
        boundary: List[Coordinate],
        thickness: Any,
        slab_type: SlabType = SlabType.PLAT_LANTAI,
        elevation: Any = 0.0,
        supports: List[str] | None = None,
        reinforcement: ReinforcementSpec | None = None,
        name: str = "",
    ) -> None:
        thickness_val = _to_decimal(thickness, "thickness")
        elevation_val = _to_decimal(elevation, "elevation")
        supports = list(supports) if supports is not None else []

        if thickness_val <= Decimal("0.0"):
            raise ValueError("Ketebalan plat beton harus lebih besar dari nol.")
        if len(boundary) < 3:
            raise ValueError("Garis batas plat minimal memerlukan 3 titik koordinat.")
        if len(supports) < 1:
            raise ValueError("Plat lantai wajib didukung minimal 1 tumpuan.")
        if _is_self_intersecting(boundary):
            raise ValueError("Perimeter boundary slab saling bersilangan (self-intersecting).")

        self._name = name
        self._boundary = _ensure_closed(boundary)
        self._thickness = thickness_val
        self._slab_type = slab_type
        self._elevation = elevation_val
        self._supports = supports
        self._reinforcement = reinforcement
        self._entity_type = EntityType.PHYSICAL

    @property
    def name(self) -> str:
        return self._name

    @property
    def thickness(self) -> Length:
        return Length(value=self._thickness)

    @property
    def area(self) -> Area:
        return Area(value=self.calculate_area().value)

    @property
    def volume(self) -> Volume:
        return Volume(value=self.calculate_volume().value)

    @property
    def supports(self) -> List[str]:
        return self._supports

    def calculate_area(self) -> Area:
        area_val = _calculate_polygon_area(self._boundary)
        if area_val <= Decimal("0"):
            raise ValueError("Luas area slab tidak boleh nol atau negatif.")
        return Area(value=area_val)

    def calculate_volume(self) -> Volume:
        area_val = self.calculate_area().value  # float
        thickness_val = float(self._thickness)
        volume_val = area_val * thickness_val
        if volume_val <= 0:
            raise ValueError("Volume beton slab harus bernilai positif.")
        return Volume(value=volume_val)

    def to_domain_state(self) -> Dict[str, Any]:
        return {
            "name": self._name,
            "thickness": float(self._thickness),
            "slab_type": self._slab_type.value,
            "elevation": float(self._elevation),
            "supports": list(self._supports),
            "area": float(self.calculate_area().value),
            "volume": float(self.calculate_volume().value),
            "entity_type": self._entity_type.value,
        }


class Foundation:
    def __init__(
        self,
        footprint: List[Coordinate],
        depth: float,
        foundation_type: FoundationType,
        material_id: str | None = None,
        name: str = "",
    ) -> None:
        if depth <= 0.0:
            raise ValueError("Kedalaman pondasi harus positif.")
        if len(footprint) < 3:
            raise ValueError("Tapak pondasi minimal 3 koordinat.")
        if _is_self_intersecting(footprint):
            raise ValueError("Perimeter footprint pondasi self-intersecting.")

        self._name = name
        self._footprint = _ensure_closed(footprint)
        self._depth = _to_decimal(depth, "depth")
        self._foundation_type = foundation_type
        self._material_id = material_id
        self._entity_type = EntityType.PHYSICAL

    @property
    def name(self) -> str:
        return self._name

    @property
    def volume(self) -> Volume:
        return Volume(value=self.calculate_volume().value)

    @property
    def foundation_type(self) -> FoundationType:
        return self._foundation_type

    @property
    def area(self) -> Area:
        return Area(value=self.calculate_area().value)

    def calculate_area(self) -> Area:
        area_val = _calculate_polygon_area(self._footprint)
        if area_val <= Decimal("0"):
            raise ValueError("Luas tapak pondasi tidak valid.")
        return Area(value=area_val)

    def calculate_volume(self) -> Volume:
        area_val = self.calculate_area().value  # float
        depth_val = float(self._depth)
        volume_val = area_val * depth_val
        return Volume(value=volume_val)

    def to_domain_state(self) -> Dict[str, Any]:
        return {
            "name": self._name,
            "depth": float(self._depth),
            "foundation_type": self._foundation_type.value,
            "material_id": self._material_id,
            "area": float(self.calculate_area().value),
            "volume": float(self.calculate_volume().value),
            "entity_type": self._entity_type.value,
        }


class Roof:
    def __init__(
        self,
        roof_type: RoofType,
        structure_type: RoofStructureType,
        slope: float,
        footprint: List[Coordinate],
        ridge_line: List[Coordinate],
        overhang: float,
        covering_material_id: str | None = None,
        name: str = "",
    ) -> None:
        if slope < 0.0 or slope > 90.0:
            raise ValueError("Sudut kemiringan atap harus antara 0 dan 90 derajat.")
        if len(footprint) < 3:
            raise ValueError("Footprint atap minimal 3 koordinat.")
        if overhang < 0.0:
            raise ValueError("Overhang atap tidak boleh negatif.")

        self._name = name
        self._roof_type = roof_type
        self._structure_type = structure_type
        self._slope = _to_decimal(slope, "slope")
        self._footprint = _ensure_closed(footprint)
        self._ridge_line = list(ridge_line)
        self._overhang = _to_decimal(overhang, "overhang")
        self._covering_material_id = covering_material_id
        self._entity_type = EntityType.PHYSICAL

    @property
    def name(self) -> str:
        return self._name

    @property
    def area(self) -> Area:
        return Area(value=self.calculate_projected_area().value)

    def calculate_projected_area(self) -> Area:
        base_area = _calculate_polygon_area(self._footprint)
        slope_radians = math.radians(float(self._slope))
        cos_factor = max(0.01, abs(math.cos(slope_radians)))
        calculated_area = base_area / Decimal(str(cos_factor))
        return Area(value=calculated_area.quantize(Decimal("0.01")))

    def to_domain_state(self) -> Dict[str, Any]:
        return {
            "name": self._name,
            "roof_type": self._roof_type.value,
            "structure_type": self._structure_type.value,
            "slope": float(self._slope),
            "overhang": float(self._overhang),
            "covering_material_id": self._covering_material_id,
            "projected_surface_area": float(self.calculate_projected_area().value),
            "entity_type": self._entity_type.value,
        }


class Door:
    def __init__(
        self,
        width: float,
        height: float,
        door_type: DoorType,
        position_on_wall: float = 0.0,
        sill_height: float = 0.0,
        material_id: str | None = None,
        host_wall: str | None = None,
        name: str = "",
    ) -> None:
        if width <= 0.1 or height <= 0.1:
            raise ValueError("Dimensi pintu tidak rasional.")
        if sill_height < 0.0:
            raise ValueError("Ketinggian ambang bawah pintu tidak boleh negatif.")

        self._name = name
        self._width = _to_decimal(width, "width")
        self._height = _to_decimal(height, "height")
        self._door_type = door_type
        self._position_on_wall = _to_decimal(position_on_wall, "position_on_wall")
        self._sill_height = _to_decimal(sill_height, "sill_height")
        self._material_id = material_id
        self._host_wall = host_wall
        self._entity_type = EntityType.PHYSICAL

    @property
    def name(self) -> str:
        return self._name

    @property
    def width(self) -> Length:
        return Length(value=self._width)

    @property
    def height(self) -> Length:
        return Length(value=self._height)

    @property
    def door_type(self) -> DoorType:
        return self._door_type

    @property
    def area(self) -> Area:
        return Area(value=self.calculate_area().value)

    def calculate_area(self) -> Area:
        return Area(value=self._width * self._height)

    def to_domain_state(self) -> Dict[str, Any]:
        return {
            "name": self._name,
            "width": float(self._width),
            "height": float(self._height),
            "door_type": self._door_type.value,
            "sill_height": float(self._sill_height),
            "material_id": self._material_id,
            "host_wall": self._host_wall,
            "area": float(self.calculate_area().value),
            "entity_type": self._entity_type.value,
        }


class Window:
    def __init__(
        self,
        width: float,
        height: float,
        window_type: WindowType,
        position_on_wall: float = 0.0,
        sill_height: float = 0.0,
        glazing_type: GlazingType = GlazingType.CLEAR,
        material_id: str | None = None,
        host_wall: str | None = None,
        name: str = "",
    ) -> None:
        if width <= 0.1 or height <= 0.1:
            raise ValueError("Dimensi jendela tidak rasional.")
        if sill_height < 0.0:
            raise ValueError("Ketinggian ambang bawah jendela tidak boleh negatif.")

        self._name = name
        self._width = _to_decimal(width, "width")
        self._height = _to_decimal(height, "height")
        self._window_type = window_type
        self._position_on_wall = _to_decimal(position_on_wall, "position_on_wall")
        self._sill_height = _to_decimal(sill_height, "sill_height")
        self._glazing_type = glazing_type
        self._material_id = material_id
        self._host_wall = host_wall
        self._entity_type = EntityType.PHYSICAL

    @property
    def name(self) -> str:
        return self._name

    @property
    def width(self) -> Length:
        return Length(value=self._width)

    @property
    def height(self) -> Length:
        return Length(value=self._height)

    @property
    def window_type(self) -> WindowType:
        return self._window_type

    @property
    def area(self) -> Area:
        return Area(value=self.calculate_area().value)

    def calculate_area(self) -> Area:
        return Area(value=self._width * self._height)

    def to_domain_state(self) -> Dict[str, Any]:
        return {
            "name": self._name,
            "width": float(self._width),
            "height": float(self._height),
            "window_type": self._window_type.value,
            "sill_height": float(self._sill_height),
            "glazing_type": self._glazing_type.value,
            "material_id": self._material_id,
            "host_wall": self._host_wall,
            "area": float(self.calculate_area().value),
            "entity_type": self._entity_type.value,
        }


class Stair:
    def __init__(
        self,
        number_of_risers: int,
        riser_height: float,
        tread_depth: float,
        width: float,
        start_elevation: float,
        end_elevation: float,
        structural_type: StairStructureType,
        name: str = "",
    ) -> None:
        if number_of_risers <= 0 or riser_height <= 0.0 or tread_depth <= 0.0 or width <= 0.0:
            raise ValueError("Parameter fungsional tangga harus positif.")
        if end_elevation <= start_elevation:
            raise ValueError("Elevasi akhir tangga harus lebih tinggi dari elevasi awal.")

        self._name = name
        self._number_of_risers = number_of_risers
        self._riser_height = _to_decimal(riser_height, "riser_height")
        self._tread_depth = _to_decimal(tread_depth, "tread_depth")
        self._width = _to_decimal(width, "width")
        self._start_elevation = _to_decimal(start_elevation, "start_elevation")
        self._end_elevation = _to_decimal(end_elevation, "end_elevation")
        self._structural_type = structural_type
        self._entity_type = EntityType.PHYSICAL

    @property
    def name(self) -> str:
        return self._name

    @property
    def width(self) -> Length:
        return Length(value=self._width)

    @property
    def area(self) -> Area:
        return Area(value=self.calculate_footprint_area().value)

    def calculate_total_rise(self) -> Length:
        return Length(value=Decimal(str(self._number_of_risers)) * self._riser_height)

    def calculate_total_run(self) -> Length:
        steps_count = Decimal(str(self._number_of_risers - 1))
        return Length(value=steps_count * self._tread_depth)

    def calculate_footprint_area(self) -> Area:
        return Area(value=self.calculate_total_run().value * self._width)

    def to_domain_state(self) -> Dict[str, Any]:
        return {
            "name": self._name,
            "number_of_risers": self._number_of_risers,
            "riser_height": float(self._riser_height),
            "tread_depth": float(self._tread_depth),
            "width": float(self._width),
            "start_elevation": float(self._start_elevation),
            "end_elevation": float(self._end_elevation),
            "structural_type": self._structural_type.value,
            "total_rise": float(self.calculate_total_rise().value),
            "total_run": float(self.calculate_total_run().value),
            "footprint_area": float(self.calculate_footprint_area().value),
            "entity_type": self._entity_type.value,
        }


class Ramp:
    def __init__(
        self,
        length: float,
        width: float,
        slope: float,
        start_elevation: float,
        end_elevation: float,
        surface_type: RampSurfaceType,
        handrail: bool = True,
        name: str = "",
    ) -> None:
        if length <= 0.0 or width <= 0.0:
            raise ValueError("Panjang dan lebar ramp harus positif.")
        if slope < 0.0 or slope > 15.0:
            raise ValueError("Kemiringan ramp maksimal 15 derajat.")
        if end_elevation <= start_elevation:
            raise ValueError("Elevasi akhir ramp harus lebih tinggi dari elevasi awal.")

        self._name = name
        self._length = _to_decimal(length, "length")
        self._width = _to_decimal(width, "width")
        self._slope = _to_decimal(slope, "slope")
        self._start_elevation = _to_decimal(start_elevation, "start_elevation")
        self._end_elevation = _to_decimal(end_elevation, "end_elevation")
        self._surface_type = surface_type
        self._handrail = handrail
        self._entity_type = EntityType.PHYSICAL

    @property
    def name(self) -> str:
        return self._name

    @property
    def length(self) -> Length:
        return Length(value=self._length)

    @property
    def width(self) -> Length:
        return Length(value=self._width)

    @property
    def area(self) -> Area:
        return Area(value=self.calculate_footprint_area().value)

    def calculate_footprint_area(self) -> Area:
        return Area(value=self._length * self._width)

    def to_domain_state(self) -> Dict[str, Any]:
        return {
            "name": self._name,
            "length": float(self._length),
            "width": float(self._width),
            "slope": float(self._slope),
            "start_elevation": float(self._start_elevation),
            "end_elevation": float(self._end_elevation),
            "surface_type": self._surface_type.value,
            "handrail": self._handrail,
            "entity_type": self._entity_type.value,
        }


class Room:
    def __init__(
        self,
        name: str = "",
        boundary: Optional[List[Coordinate]] = None,
        area: Optional[float] = None,
        height: float = 3.0,
    ) -> None:
        if boundary is None and area is None:
            raise ValueError("Harus menyediakan boundary atau area.")
        if not name or not name.strip():
            raise ValueError("Nama ruangan tidak boleh kosong.")
        if height <= 0:
            raise ValueError("Tinggi ruangan harus positif.")

        self.name = name.strip()
        if boundary is not None:
            if len(boundary) < 3:
                raise ValueError("Boundary ruangan minimal 3 titik.")
            self._boundary = _ensure_closed(boundary)
            self._area = _calculate_polygon_area(self._boundary)
        else:
            self._boundary = None
            self._area = _to_decimal(area, "area")
        self._height = _to_decimal(height, "height")

    @property
    def area(self) -> Area:
        return Area(value=self._area)

    @property
    def height(self) -> Length:
        return Length(value=self._height)

    def calculate_room_area(self) -> Decimal:
        return self._area

    def calculate_volume(self) -> Volume:
        return Volume(value=self._area * self._height)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "area": float(self._area),
            "height": float(self._height),
            "volume": float(self.calculate_volume().value),
        }