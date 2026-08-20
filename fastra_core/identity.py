import uuid
from typing import Set

class Identity:
    _generated_uuids: Set[str] = set()
    
    @classmethod
    def generate(cls) -> str:
        max_attempts = 1000
        for _ in range(max_attempts):
            new_uuid = str(uuid.uuid4())
            if new_uuid not in cls._generated_uuids:
                cls._generated_uuids.add(new_uuid)
                return new_uuid
        raise RuntimeError("Gagal menghasilkan UUID unik")
    
    @classmethod
    def is_valid(cls, uuid_str: str) -> bool:
        try:
            uuid.UUID(uuid_str)
            return True
        except (ValueError, AttributeError):
            return False
    
    @classmethod
    def is_unique_in_context(cls, uuid_str: str) -> bool:
        return uuid_str not in cls._generated_uuids
    
    @classmethod
    def reset(cls):
        cls._generated_uuids.clear()
