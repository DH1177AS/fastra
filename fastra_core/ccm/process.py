from dataclasses import dataclass, field
from typing import List, Optional, Dict
from fastra_core.ontology.universal_object import UniversalObject
from fastra_core.ontology.entity_type import EntityType
from fastra_core.primitives.time import Time
from fastra_core.units.validator import validate_unit_not_unknown

@dataclass
class ResourceAllocation:
    resource_uuid: str
    quantity: float
    unit: str
    duration: Optional[Time] = None

    def __post_init__(self):
        if not self.resource_uuid.strip():
            raise ValueError("resource_uuid tidak boleh kosong")
        if self.quantity <= 0:
            raise ValueError("quantity harus > 0")
        if not self.unit.strip():
            raise ValueError("unit tidak boleh kosong")
        validate_unit_not_unknown(self.unit)
        if self.duration is not None and self.duration.value < 0:
            raise ValueError("duration tidak boleh negatif")

@dataclass
class ConstructionTask(UniversalObject):
    """ACES-200 Section 8.1: ConstructionTask"""
    task_type: str = 'GALIAN'
    work_item_ref: Optional[str] = None
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    resources: List[ResourceAllocation] = field(default_factory=list)
    duration: Optional[Time] = None
    predecessors: List[str] = field(default_factory=list)
    entity_type: EntityType = EntityType.PROCESS

    def __post_init__(self):
        super().__post_init__()
        valid_types = ['GALIAN', 'BEKISTING', 'PEMBESIAN', 'PENGECORAN', 'PASANGAN_BATA', 'PLESTERAN', 'PENGECATAN', 'INSTALASI']
        if self.task_type not in valid_types:
            raise ValueError(f'Task type tidak valid: {self.task_type}')
        if not self.inputs or not self.outputs:
            raise ValueError("ConstructionTask harus memiliki input dan output minimal 1")

@dataclass
class InspectionTask(UniversalObject):
    """ACES-200 Section 8: InspectionTask"""
    inspection_type: str = 'VISUAL'
    standard: str = 'SNI'
    checklist: List[str] = field(default_factory=list)
    frequency: str = 'HARIAN'
    assigned_to: Optional[str] = None
    entity_type: EntityType = EntityType.PROCESS

    def __post_init__(self):
        super().__post_init__()
        if not self.checklist:
            self.checklist = ['Check point 1']
        valid_inspection_types = {"VISUAL", "TEST", "VERIFICATION"}
        if self.inspection_type not in valid_inspection_types:
            raise ValueError(f"inspection_type tidak valid: {self.inspection_type}")
        valid_frequencies = {"HARIAN", "MINGGUAN", "BULANAN", "PER_BATCH", "PER_ZONA", "TAHUNAN"}
        if self.frequency not in valid_frequencies:
            raise ValueError(f"frequency tidak valid: {self.frequency}")
