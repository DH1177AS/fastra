# fastra_core\serialization\hash.py

# fastra_core\serialization\hash.py
from __future__ import annotations

import hashlib
import logging
from typing import Any

from .canonical_json import to_json

logger = logging.getLogger("fastra_core.serialization.hash")


def canonical_hash(obj: Any) -> str:
    """
    Computes a deterministic, cryptographic SHA-256 hash string from any given object.
    Enforces a strict fail-fast canonical json representation as the immutable source byte stream.

    Guarantees that identical object topologies always yield the exact same hash signature,
    providing complete multi-thread security against structural data poisoning.
    """
    if obj is None:
        logger.error("CRYPTOGRAPHIC_ERROR_CANNOT_HASH_NULL_OBJECT")
        raise ValueError("CRYPTOGRAPHIC_ERROR_CANNOT_HASH_NULL_OBJECT")

    # Serialize object to its exact minimal, whitespace-free lexicographically sorted string
    try:
        json_str: str = to_json(obj)
    except Exception as exc:
        logger.error("CANONICAL_SERIALIZATION_FAILED_BEFORE_HASH: %s", exc)
        raise ValueError(f"SERIALIZATION_FAILURE_CANNOT_HASH_OBJECT: {exc}") from exc

    # Verify signature generation input state integrity
    if not json_str:
        logger.error("SERIALIZATION_ANOMALY_PRODUCED_EMPTY_CANONICAL_STRING")
        raise ValueError("SERIALIZATION_ANOMALY_PRODUCED_EMPTY_CANONICAL_STRING")

    # Enforce standard binary byte encoding array layout
    byte_stream: bytes = json_str.encode("utf-8")

    # Fire high-performance secure cryptographic calculation lane
    hasher = hashlib.sha256()
    hasher.update(byte_stream)

    # Return pure hexadecimal string footprint digest
    digest = hasher.hexdigest()
    logger.debug("Canonical hash generated: %s", digest)
    return digest