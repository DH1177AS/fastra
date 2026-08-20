import hashlib
from .canonical_json import to_json

def canonical_hash(obj) -> str:
    json_str = to_json(obj)
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()
