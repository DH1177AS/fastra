"""
ACES-200 Section 6: Spatial Entities.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from fastra_core.ontology.universal_object import UniversalObject
from fastra_core.ontology.entity_type import EntityType
from fastra_core.primitives.length import Length
from fastra_core.primitives.area import Area
from fastra_core.spatial.coordinate import Coordinate


def _ensure_closed(points: List[Coordinate], epsilon: float = 1e-6) -> List[Coordinate]:
    if not points:
        return points
    pts = list(points)
    if pts[0] != pts[-1]:
        pts.append(pts[0])
    return pts


@dataclass
class Site(UniversalObject):
    boundary: List[Coordinate] = field(default_factory=list)
    address: str = ""
    geo_location: Optional[dict] = None
    zoning: str = ""
    entity_type: EntityType = EntityType.SPATIAL

    def __post_init__(self):
        super().__post_init__()
        if len(self.boundary) < 3:
            raise ValueError("Boundary site minimal 3 titik")
        self.boundary = _ensure_closed(self.boundary)
        if self.geo_location is not None and not isinstance(self.geo_location, dict):
            raise ValueError("geo_location harus dict")

    @property
    def area(self) -> Area:
        from fastra_core.geometry.polygon import area as poly_area
        return poly_area(self.boundary)


@dataclass
class Building(UniversalObject):
    building_type: str = "HOUSE"
    number_of_storeys: int = 1
    footprint: List[Coordinate] = field(default_factory=list)
    height: Length = Length(0)
    entity_type: EntityType = EntityType.SPATIAL

    def __post_init__(self):
        super().__post_init__()
        if self.number_of_storeys <= 0:
            raise ValueError("Jumlah lantai harus > 0")
        if len(self.footprint) < 3:
            raise ValueError("Footprint building minimal 3 titik")
        self.footprint = _ensure_closed(self.footprint)

    @property
    def total_area(self) -> Area:
        from fastra_core.geometry.polygon import area as poly_area
        base = poly_area(self.footprint)
        return Area(base.value * self.number_of_storeys)


@dataclass
class Storey(UniversalObject):
    level: int = 0
    elevation: Length = Length(0)
    height: Length = Length(3.5)
    building_id: Optional[str] = None
    entity_type: EntityType = EntityType.SPATIAL

    def __post_init__(self):
        super().__post_init__()
        if self.height.value <= 0:
            raise ValueError("Tinggi storey harus > 0")
        if self.elevation.value < 0:
            raise ValueError("Elevasi storey tidak boleh negatif")


@dataclass
class Room(UniversalObject):
    room_type: str = "LIVING"
    boundary: List[Coordinate] = field(default_factory=list)
    storey_id: Optional[str] = None
    finish: Optional[dict] = None
    entity_type: EntityType = EntityType.SPATIAL

    def __post_init__(self):
        super().__post_init__()
        if len(self.boundary) < 3:
            raise ValueError("Boundary room minimal 3 titik")
        valid_room_types = {"LIVING", "BEDROOM", "KITCHEN", "BATHROOM", "OFFICE", "CORRIDOR", "STORAGE", "MECHANICAL"}
        if self.room_type not in valid_room_types:
            raise ValueError(f"room_type tidak valid: {self.room_type}")

    @property
    def area(self) -> Area:
        from fastra_core.geometry.polygon import area as poly_area
        return poly_area(self.boundary)

    @property
    def is_closed(self) -> bool:
        from fastra_core.geometry.polygon import is_closed as poly_closed
        return poly_closed(self.boundary)


@dataclass
class Zone(UniversalObject):
    zone_type: str = 'HVAC'
    rooms: List[str] = field(default_factory=list)
    area: Area = Area(0)
    entity_type: EntityType = EntityType.SPATIAL

    def __post_init__(self):
        super().__post_init__()
        if self.zone_type not in ['HVAC', 'FIRE', 'SECURITY', 'ACOUSTIC', 'CUSTOM']:
            raise ValueError(f'Zone type tidak valid: {self.zone_type}')
        if self.area.value < 0:
            raise ValueError("Area zone tidak boleh negatif")
        if not all(isinstance(r, str) for r in self.rooms):
            raise ValueError("rooms harus list of string")
