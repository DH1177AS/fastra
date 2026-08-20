from enum import Enum

class EntityType(Enum):
    PHYSICAL = "Physical"
    SPATIAL = "Spatial"
    TEMPORAL = "Temporal"
    ECONOMIC = "Economic"
    RESOURCE = "Resource"
    HUMAN = "Human"
    ORGANIZATION = "Organization"
    PROCESS = "Process"
    RULE = "Rule"
    EVENT = "Event"
    DOCUMENT = "Document"
    RELATIONSHIP = "Relationship"

ENTITY_FAMILIES = {
    EntityType.PHYSICAL: ["Structural Element", "Architectural Element", "MEP Element"],
    EntityType.SPATIAL: ["Macro Space", "Meso Space", "Micro Space"],
    EntityType.RESOURCE: ["Material", "Equipment", "Consumable"],
    EntityType.HUMAN: ["Labor", "Professional"],
    EntityType.PROCESS: ["Construction Process", "Inspection Process", "Procurement Process"],
}

ENTITY_TYPE_NAMES = {e.value: e for e in EntityType}
