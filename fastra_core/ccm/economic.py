from dataclasses import dataclass, field
from typing import Optional, List, Dict
from fastra_core.ontology.universal_object import UniversalObject
from fastra_core.ontology.entity_type import EntityType
from fastra_core.primitives.currency import Currency
from fastra_core.units.validator import validate_dimension, validate_unit_not_unknown
from decimal import Decimal

@dataclass
class WorkItem(UniversalObject):
    work_item_code: str = ""
    work_item_name: str = ""
    unit: str = "m²"
    quantity: float = 0.0
    source_entity_id: Optional[str] = None
    ahs_ref: Optional[str] = None
    sni_ref: Optional[str] = None
    entity_type: EntityType = EntityType.ECONOMIC

    def __post_init__(self):
        super().__post_init__()
        if not self.work_item_code.strip():
            raise ValueError("work_item_code tidak boleh kosong")
        if not self.unit.strip():
            raise ValueError("unit tidak boleh kosong")
        validate_unit_not_unknown(self.unit)
        if self.quantity < 0:
            raise ValueError("quantity tidak boleh negatif")

@dataclass
class BOQItem(UniversalObject):
    boq_section: str = ""
    work_items: List[str] = field(default_factory=list)
    total_quantity: float = 0.0
    unit: str = "m²"
    entity_type: EntityType = EntityType.ECONOMIC

    def __post_init__(self):
        super().__post_init__()
        if not self.boq_section.strip():
            raise ValueError("boq_section tidak boleh kosong")
        validate_unit_not_unknown(self.unit)
        if self.total_quantity < 0:
            raise ValueError("total_quantity tidak boleh negatif")

@dataclass
class CostItem(UniversalObject):
    cost_type: str = "MATERIAL"
    amount: Currency = Currency.from_float(0)
    work_item_ref: Optional[str] = None
    resource_ref: Optional[str] = None
    coefficient: float = 1.0
    unit_price: Currency = Currency.from_float(0)
    price_source: str = ""
    price_date: str = ""
    entity_type: EntityType = EntityType.ECONOMIC

    def __post_init__(self):
        super().__post_init__()
        valid_cost_types = {"MATERIAL", "LABOR", "EQUIPMENT", "OVERHEAD", "PROFIT", "TAX", "CONTINGENCY"}
        if self.cost_type not in valid_cost_types:
            raise ValueError(f"cost_type tidak valid: {self.cost_type}")
        if self.coefficient <= 0:
            raise ValueError("coefficient harus > 0")
        if self.amount.value < 0:
            raise ValueError("amount tidak boleh negatif")

@dataclass
class RABItem(UniversalObject):
    rab_section: str = ""
    cost_items: List[str] = field(default_factory=list)
    subtotal: Currency = Currency.from_float(0)
    total: Currency = Currency.from_float(0)
    location_factor: float = 1.0
    entity_type: EntityType = EntityType.ECONOMIC

    def __post_init__(self):
        super().__post_init__()
        if not self.rab_section.strip():
            raise ValueError("rab_section tidak boleh kosong")
        if self.location_factor <= 0:
            raise ValueError("location_factor harus > 0")
        if self.subtotal.value < 0 or self.total.value < 0:
            raise ValueError("subtotal/total tidak boleh negatif")
