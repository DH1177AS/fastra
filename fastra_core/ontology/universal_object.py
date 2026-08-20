from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastra_core.identity import Identity
from fastra_core.ontology.entity_type import EntityType
from fastra_core.ontology.lifecycle import LifecycleStatus

@dataclass
class UniversalObject:
    uuid: str = field(default_factory=Identity.generate)
    name: str = ""
    description: Optional[str] = None
    entity_type: EntityType = EntityType.PHYSICAL
    version: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    change_reason: Optional[str] = None
    status: LifecycleStatus = LifecycleStatus.DRAFT
    lifecycle_history: list = field(default_factory=list, init=False)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.uuid:
            self.uuid = Identity.generate()
        if not Identity.is_valid(self.uuid):
            raise ValueError(f"UUID tidak valid: {self.uuid}")
        if not isinstance(self.entity_type, EntityType):
            raise ValueError(f"Entity type tidak valid: {self.entity_type}")

    def update(self, **kwargs):
        """Perbarui atribut dengan dukungan Axiom 9: updated_by dan change_reason."""
        updated_by = kwargs.pop("updated_by", None)
        change_reason = kwargs.pop("change_reason", None)

        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        self.version += 1
        self.updated_at = datetime.now(timezone.utc)
        if updated_by is not None:
            self.updated_by = updated_by
        if change_reason is not None:
            self.change_reason = change_reason

    def transition_to(self, new_status):
        from fastra_core.ontology.lifecycle import is_valid_transition
        if not is_valid_transition(self.status, new_status):
            raise ValueError(f"Transisi tidak valid: {self.status.value} -> {new_status.value}")
        self.status = new_status
        self.update()