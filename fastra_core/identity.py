# fastra_core\identity.py

from __future__ import annotations

import logging
import re
import threading
import uuid
from typing import Any

logger = logging.getLogger("fastra_core.identity")


class Identity:
   
    _global_lock = threading.Lock()

    _UUID_V4_PATTERN = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        re.IGNORECASE,
    )

    @classmethod
    def generate(cls) -> str:
        
        with cls._global_lock:
            new_uuid = str(uuid.uuid4())

            if not cls._UUID_V4_PATTERN.match(new_uuid):
                logger.critical("CRYPTOGRAPHIC_INTEGRITY_VIOLATION_MALFORMED_UUID_V4_GENERATED")
                raise RuntimeError("CRYPTOGRAPHIC_INTEGRITY_VIOLATION_MALFORMED_UUID_V4_GENERATED")

            logger.debug("Generated UUID v4: %s", new_uuid)
            return new_uuid

    @classmethod
    def is_valid(cls, uuid_str: Any) -> bool:
        
        if not isinstance(uuid_str, str):
            return False

        clean_str = uuid_str.strip()
        if not clean_str:
            return False

        return bool(cls._UUID_V4_PATTERN.match(clean_str))

    @classmethod
    def is_unique_in_context(cls, uuid_str: str) -> bool:
       
        return cls.is_valid(uuid_str)

    @classmethod
    def reset(cls) -> None:
       
        with cls._global_lock:
            logger.debug("Identity engine context reset executed")