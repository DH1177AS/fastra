# fastra_core\ontology\lifecycle.py

from __future__ import annotations

import logging
from enum import Enum
from types import MappingProxyType
from typing import Any, Dict, Mapping, Tuple

logger = logging.getLogger("fastra.ontology.lifecycle")


class LifecycleStatus(str, Enum):
    """
    Strict Domain Enum untuk mengunci Status Siklus Hidup Aset Konstruksi (Lifecycle).
    Mewarisi `str` untuk memastikan validasi serialisasi bebas dari coercion hacks.
    """
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    OBSOLETE = "OBSOLETE"
    DEMOLISHED = "DEMOLISHED"


_VALID_TRANSITIONS_INTERNAL: Dict[LifecycleStatus, Tuple[LifecycleStatus, ...]] = {
    LifecycleStatus.DRAFT: (LifecycleStatus.ACTIVE, LifecycleStatus.OBSOLETE),
    LifecycleStatus.ACTIVE: (LifecycleStatus.SUPERSEDED, LifecycleStatus.OBSOLETE, LifecycleStatus.DEMOLISHED),
    LifecycleStatus.SUPERSEDED: (LifecycleStatus.OBSOLETE,),
    LifecycleStatus.OBSOLETE: (),
    LifecycleStatus.DEMOLISHED: (),
}

VALID_TRANSITIONS: Mapping[LifecycleStatus, Tuple[LifecycleStatus, ...]] = MappingProxyType(
    _VALID_TRANSITIONS_INTERNAL
)


def is_valid_transition(from_status: Any, to_status: Any) -> bool:
    """
    Memverifikasi legalitas perpindahan status manajemen siklus hidup aset konstruksi.
    Menerapkan strict fail-fast validation tanpa toleransi terhadap coercion hacks.
    """
    if not isinstance(from_status, LifecycleStatus):
        logger.error("LIFECYCLE_TRANSITION_REJECTED_INVALID_SOURCE_TYPE: %r", from_status)
        raise TypeError("SOURCE_STATUS_MUST_BE_AN_INSTANCE_OF_LIFECYCLE_STATUS_ENUM")

    if not isinstance(to_status, LifecycleStatus):
        logger.error("LIFECYCLE_TRANSITION_REJECTED_INVALID_TARGET_TYPE: %r", to_status)
        raise TypeError("TARGET_STATUS_MUST_BE_AN_INSTANCE_OF_LIFECYCLE_STATUS_ENUM")

    allowed_targets = VALID_TRANSITIONS.get(from_status)
    if allowed_targets is None:
        logger.error("LIFECYCLE_TRANSITION_REJECTED_UNREGISTERED_SOURCE: %s", from_status)
        raise KeyError(f"UNREGISTERED_LIFECYCLE_STATUS_MAPPING: {from_status}")

    result = to_status in allowed_targets
    if not result:
        logger.debug(
            "LIFECYCLE_TRANSITION_REJECTED_ILLEGAL_TARGET: %s -> %s",
            from_status.value,
            to_status.value,
        )
    return result