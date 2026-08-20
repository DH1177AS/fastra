"""
ACES-300 Knowledge Edges.
"""
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class MaterialRequirement:
    material_id: str
    coefficient: float
    waste_factor: float = 1.0
    source: str = ""

@dataclass
class LaborRequirement:
    labor_id: str
    coefficient: float  # OH per unit
    source: str = ""

@dataclass
class EquipmentRequirement:
    equipment_id: str
    coefficient: float
    source: str = ""

@dataclass
class PriceRecord:
    material_id: str
    price: float
    region: str
    valid_from: str
    valid_until: Optional[str] = None
    supplier_id: Optional[str] = None
    source: str = ""