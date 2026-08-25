from dataclasses import dataclass, field
from typing import Optional, Dict
from fastra_core.ontology.universal_object import UniversalObject
from fastra_core.ontology.entity_type import EntityType
from fastra_core.primitives.currency import Currency
from fastra_core.units.validator import validate_dimension
from decimal import Decimal

@dataclass
class Material(UniversalObject):
    material_class: str = "CONCRETE"
    material_type: str = ""
    unit: str = "mÂ³"
    density: Optional[float] = None
    strength_grade: Optional[str] = None
    specifications: Dict = field(default_factory=dict)
    entity_type: EntityType = EntityType.RESOURCE

    def __post_init__(self):
        super().__post_init__()
        valid_classes = {"CONCRETE", "STEEL", "WOOD", "MASONRY", "GLASS", "PLASTIC", "COMPOSITE", "FINISH"}
        if self.material_class not in valid_classes:
            raise ValueError(f"material_class tidak valid: {self.material_class}")
        if not self.unit.strip():
            raise ValueError("unit tidak boleh kosong")
        pass
        validate_dimension(self.unit, 'volume')
        if self.density is not None and self.density <= 0:
            raise ValueError("density harus > 0")
        if not self.material_type.strip():
            raise ValueError("material_type tidak boleh kosong")

@dataclass
class Equipment(UniversalObject):
    equipment_type: str = "EXCAVATOR"
    capacity: Optional[str] = None
    unit: str = "hari"
    hourly_rate: Optional[Currency] = None
    entity_type: EntityType = EntityType.RESOURCE

    def __post_init__(self):
        super().__post_init__()
        valid_types = {"EXCAVATOR", "CRANE", "MIXER", "VIBRATOR", "SCAFFOLDING", "PUMP", "GENERATOR", "TOWER_CRANE"}
        if self.equipment_type not in valid_types:
            raise ValueError(f"equipment_type tidak valid: {self.equipment_type}")
        if not self.unit.strip():
            raise ValueError("unit tidak boleh kosong")
        if self.hourly_rate is not None and self.hourly_rate.value < 0:
            raise ValueError("hourly_rate tidak boleh negatif")
        if self.capacity is not None and not self.capacity.strip():
            raise ValueError("capacity tidak boleh kosong")

@dataclass
class Labor(UniversalObject):
    labor_type: str = "PEKERJA"
    daily_rate: Currency = Currency.from_float(120000)
    productivity: Dict = field(default_factory=dict)
    skill_level: str = "JUNIOR"
    entity_type: EntityType = EntityType.HUMAN

    def __post_init__(self):
        super().__post_init__()
        valid_labor_types = {"TUKANG_BATU", "TUKANG_KAYU", "TUKANG_BESI", "PEKERJA", "KEPALA_TUKANG", "MANDOR"}
        if self.labor_type not in valid_labor_types:
            raise ValueError(f"labor_type tidak valid: {self.labor_type}")
        if self.daily_rate.value < 0:
            raise ValueError("daily_rate tidak boleh negatif")
        if self.skill_level not in {"JUNIOR", "SENIOR", "EXPERT"}:
            raise ValueError(f"skill_level tidak valid: {self.skill_level}")
        if not isinstance(self.productivity, dict):
            raise ValueError("productivity harus dict")

