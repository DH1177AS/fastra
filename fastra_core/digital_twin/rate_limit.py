"""
Rate limiter dengan dukungan Redis (fallback memory) untuk API Digital Twin.
"""
from __future__ import annotations

import time
from typing import Dict, Optional, Tuple

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class RateLimiter:
    def __init__(self, redis_url: Optional[str] = None, limit: int = 60, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._memory: Dict[str, int] = {}
        self._redis_client: Optional["redis.Redis"] = None  # type: ignore
        if REDIS_AVAILABLE and redis_url:
            try:
                self._redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
                self._redis_client.ping()
            except Exception:
                self._redis_client = None

    def _memory_check(self, key: str) -> Tuple[bool, int, int]:
        now = time.time()
        window_start = int(now // self.window_seconds)
        bucket = f"{key}:{window_start}"
        count = self._memory.get(bucket, 0)
        if count >= self.limit:
            return False, 0, int(self.window_seconds - (now % self.window_seconds))
        self._memory[bucket] = count + 1
        return True, self.limit - count - 1, int(self.window_seconds - (now % self.window_seconds))

    def _redis_check(self, key: str) -> Tuple[bool, int, int]:
        if self._redis_client is None: raise RuntimeError("redis client is None")
        now = time.time()
        window_start = int(now // self.window_seconds)
        bucket = f"fastra:rate:{key}:{window_start}"
        pipe = self._redis_client.pipeline()
        pipe.incr(bucket)
        pipe.expire(bucket, self.window_seconds)
        count = int(pipe.execute()[0])
        remaining = max(self.limit - count, 0)
        reset = int(self.window_seconds - (now % self.window_seconds))
        return count <= self.limit, remaining, reset

    def allow(self, key: str) -> Tuple[bool, int, int]:
        if self._redis_client:
            return self._redis_check(key)
        return self._memory_check(key)

