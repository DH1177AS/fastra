from enum import Enum

class LifecycleStatus(Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    OBSOLETE = "OBSOLETE"
    DEMOLISHED = "DEMOLISHED"

VALID_TRANSITIONS = {
    LifecycleStatus.DRAFT: [LifecycleStatus.ACTIVE, LifecycleStatus.OBSOLETE],
    LifecycleStatus.ACTIVE: [LifecycleStatus.SUPERSEDED, LifecycleStatus.OBSOLETE, LifecycleStatus.DEMOLISHED],
    LifecycleStatus.SUPERSEDED: [LifecycleStatus.OBSOLETE],
    LifecycleStatus.OBSOLETE: [],
    LifecycleStatus.DEMOLISHED: [],
}

def is_valid_transition(from_status, to_status):
    return to_status in VALID_TRANSITIONS.get(from_status, [])
