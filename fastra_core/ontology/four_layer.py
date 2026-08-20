from dataclasses import dataclass, field
from typing import Optional, Any
from fastra_core.primitives.length import Length
from fastra_core.primitives.area import Area
from fastra_core.primitives.volume import Volume
from fastra_core.primitives.currency import Currency

@dataclass
class PhysicalReality:
    exists_in_field: bool = False
    last_inspection_date: Optional[str] = None
    condition: Optional[str] = None

@dataclass
class GeometricReality:
    has_geometry: bool = False
    bounding_box: Optional[Any] = None
    volume: Optional[Volume] = None
    area: Optional[Area] = None

@dataclass
class SemanticReality:
    entity_class: Optional[str] = None
    structural_type: Optional[str] = None
    material_type: Optional[str] = None
    function: Optional[str] = None

@dataclass
class EconomicReality:
    material_cost: Optional[Currency] = None
    labor_cost: Optional[Currency] = None
    equipment_cost: Optional[Currency] = None
    total_cost: Optional[Currency] = None
    risk_factor: float = 0.0

@dataclass
class FourLayerReality:
    physical: PhysicalReality = field(default_factory=PhysicalReality)
    geometric: GeometricReality = field(default_factory=GeometricReality)
    semantic: SemanticReality = field(default_factory=SemanticReality)
    economic: EconomicReality = field(default_factory=EconomicReality)

    def is_complete(self) -> bool:
        return (self.physical.exists_in_field and
                self.geometric.has_geometry and
                self.semantic.entity_class is not None and
                self.economic.total_cost is not None)
