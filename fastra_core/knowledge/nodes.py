from dataclasses import dataclass, field
from typing import Optional, Dict
from fastra_core.primitives.currency import Currency

@dataclass
class MaterialNode:
    id: str
    name: str
    unit: str
    category: str = ""
    specifications: Dict = field(default_factory=dict)

@dataclass
class LaborNode:
    id: str
    name: str
    role: str
    daily_rate: Currency

@dataclass
class EquipmentNode:
    id: str
    name: str
    unit: str
    rate_per_day: Optional[float] = None
    rate_per_hour: Optional[float] = None
    rate_per_month: Optional[float] = None
    category: str = ""
    specifications: Dict = field(default_factory=dict)

@dataclass
class WorkItemNode:
    id: str
    code: str
    name: str
    unit: str
    sni_ref: str = ""
    category: str = ""

@dataclass
class SupplierNode:
    id: str
    name: str
    region: str
    delivery_radius_km: float = 20.0
