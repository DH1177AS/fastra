from dataclasses import dataclass, field
from typing import List, Optional
from fastra_core.ontology.universal_object import UniversalObject
from fastra_core.ontology.entity_type import EntityType
from fastra_core.primitives.length import Length
from fastra_core.spatial.coordinate import Coordinate

@dataclass
class GridAxis:
    name: str = ''
    start: Optional[Coordinate] = None
    end: Optional[Coordinate] = None
    is_primary: bool = True

    def __post_init__(self):
        if self.name.strip() == "":
            raise ValueError("GridAxis name tidak boleh kosong")

@dataclass
class GridIntersection:
    axis_1: str = ''
    axis_2: str = ''
    coordinate: Optional[Coordinate] = None

    def __post_init__(self):
        if not self.axis_1.strip() or not self.axis_2.strip():
            raise ValueError("GridIntersection axis_1/axis_2 tidak boleh kosong")

@dataclass
class Grid(UniversalObject):
    """ACES-200 Section 10.1: Grid"""
    grid_type: str = 'CARTESIAN'
    axes: List[GridAxis] = field(default_factory=list)
    intersections: List[GridIntersection] = field(default_factory=list)
    entity_type: EntityType = EntityType.SPATIAL

    def __post_init__(self):
        super().__post_init__()
        if self.grid_type not in ['CARTESIAN', 'RADIAL', 'COMBINED']:
            raise ValueError(f'Grid type tidak valid: {self.grid_type}')
        if not all(isinstance(a, GridAxis) for a in self.axes):
            raise ValueError("Semua elemen axes harus GridAxis")
        if not all(isinstance(i, GridIntersection) for i in self.intersections):
            raise ValueError("Semua elemen intersections harus GridIntersection")
        if self.grid_type == 'CARTESIAN' and len(self.axes) < 2:
            raise ValueError("Grid CARTESIAN minimal 2 sumbu")

@dataclass
class Level(UniversalObject):
    """ACES-200 Section 10.2: Level"""
    elevation: Length = Length(0)
    level_type: str = 'GROUND'
    name: str = 'Level 0'
    entity_type: EntityType = EntityType.SPATIAL

    def __post_init__(self):
        super().__post_init__()
        if self.level_type not in ['GROUND', 'STOREY', 'ROOF', 'FOUNDATION', 'REFERENCE']:
            raise ValueError(f'Level type tidak valid: {self.level_type}')
        if self.elevation.value < 0:
            raise ValueError("Elevasi level tidak boleh negatif")

@dataclass
class Opening(UniversalObject):
    """ACES-200 Section 10.3: Opening"""
    opening_type: str = 'DOOR'
    width: Length = Length(0.9)
    height: Length = Length(2.1)
    position: Length = Length(0)
    host_element: Optional[str] = None
    entity_type: EntityType = EntityType.PHYSICAL

    def __post_init__(self):
        super().__post_init__()
        if self.opening_type not in ['DOOR', 'WINDOW', 'VENT', 'PASSAGE', 'SHAFT', 'SKYLIGHT']:
            raise ValueError(f'Opening type tidak valid: {self.opening_type}')
        if self.width.value <= 0:
            raise ValueError('Lebar bukaan harus > 0')
        if self.height.value <= 0:
            raise ValueError('Tinggi bukaan harus > 0')
        if self.position.value < 0:
            raise ValueError('Posisi bukaan tidak boleh negatif')
        if self.host_element is not None and not isinstance(self.host_element, str):
            raise ValueError("host_element harus string")
