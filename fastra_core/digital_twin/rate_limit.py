# fastra_core\digital_twin\rate_limit.py

from __future__ import annotations

import logging
import math
import threading
import time
from typing import Any, Dict, Optional, Tuple

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:  # pragma: no cover - fallback scenario
    REDIS_AVAILABLE = False

logger = logging.getLogger("fastra_core.digital_twin.rate_limit")


class RateLimiter:
    """
    Sistem Pembatas Laju Akses API (Rate Limiter Engine).
    Menjamin ketersediaan infrastruktur orkestrasi Digital Twin dari ancaman brute-force
    maupun serangan kehabisan sumber daya memori (Denial of Service).
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        limit: int = 60,
        window_seconds: int = 60,
    ) -> None:
        # Strict numeric validation with anti-coercion guard
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            logger.error("RATE_LIMITER_INVALID_LIMIT: %r", limit)
            raise ValueError("LIMIT_MUST_BE_A_POSITIVE_INTEGER")
        if isinstance(window_seconds, bool) or not isinstance(window_seconds, int) or window_seconds <= 0:
            logger.error("RATE_LIMITER_INVALID_WINDOW: %r", window_seconds)
            raise ValueError("WINDOW_SECONDS_MUST_BE_A_POSITIVE_INTEGER")

        self.limit = limit
        self.window_seconds = window_seconds

        # Thread lock internal untuk mengamankan isolasi transaksional fallback memori lokal
        self._lock = threading.Lock()
        self._memory: Dict[str, int] = {}
        self._last_cleanup_window: int = int(time.time() // self.window_seconds)

        self._redis_client: Optional[redis.Redis] = None

        if REDIS_AVAILABLE and redis_url:
            if not isinstance(redis_url, str) or not redis_url.strip():
                logger.error("RATE_LIMITER_INVALID_REDIS_URL: %r", redis_url)
                raise ValueError("REDIS_URL_MUST_BE_A_NON_EMPTY_STRING_WHEN_PROVIDED")

            try:
                # Mengatur timeouts ketat agar terhindar dari pemblokiran thread utama saat jaringan drop
                self._redis_client = redis.Redis.from_url(
                    redis_url.strip(),
                    decode_responses=True,
                    socket_timeout=1.0,
                    socket_connect_timeout=1.0,
                )
                self._redis_client.ping()
                logger.info("Redis rate limiter connected: %s", redis_url.strip())
            except Exception as exc:
                # Fallback otomatis ke mode in-memory jika koneksi cluster Redis hulu gagal
                logger.warning("Redis connection failed, falling back to in-memory: %s", exc)
                self._redis_client = None

    def _memory_check(self, key: str) -> Tuple[bool, int, int]:
        """
        Pengecekan laju kuota internal memori (In-Memory Fixed-Window Engine).
        Dilengkapi dengan garbage collection otomatis untuk mencegah memory leak.
        """
        now = time.time()
        if math.isnan(now) or math.isinf(now):
            logger.error("RATE_LIMITER_SYSTEM_CLOCK_ANOMALY: %s", now)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_IN_SYSTEM_CLOCK_STATE")

        current_window = int(now // self.window_seconds)
        bucket = f"{key}:{current_window}"

        with self._lock:
            # Pemicu Pembersihan Memori Otomatis (Garbage Collection Loop)
            # Menghapus seluruh entri window masa lalu agar memori tidak membengkak tanpa batas (Anti-DoS)
            if current_window > self._last_cleanup_window:
                # Memilah kunci lama secara aman
                expired_buckets = [
                    k for k in self._memory.keys() if not k.endswith(f":{current_window}")
                ]
                for k in expired_buckets:
                    self._memory.pop(k, None)
                self._last_cleanup_window = current_window
                logger.debug("Memory rate limit cleanup removed %d old buckets", len(expired_buckets))

            count = self._memory.get(bucket, 0)
            reset = int(self.window_seconds - (now % self.window_seconds))

            if count >= self.limit:
                return False, 0, max(0, reset)

            new_count = count + 1
            self._memory[bucket] = new_count
            remaining = max(self.limit - new_count, 0)

            return True, remaining, max(0, reset)

    def _redis_check(self, key: str) -> Tuple[bool, int, int]:
        """
        Pengecekan laju kuota terdistribusi melalui transaksi atomik pipa Redis.
        """
        if self._redis_client is None:
            logger.error("REDIS_CLIENT_DESYNC: None client in _redis_check")
            raise RuntimeError("REDIS_CLIENT_DESYNCHRONIZATION_ENCOUNTERED")

        now = time.time()
        if math.isnan(now) or math.isinf(now):
            logger.error("RATE_LIMITER_SYSTEM_CLOCK_ANOMALY: %s", now)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_IN_SYSTEM_CLOCK_STATE")

        current_window = int(now // self.window_seconds)
        bucket = f"fastra:rate:{key}:{current_window}"
        reset = int(self.window_seconds - (now % self.window_seconds))

        try:
            # Memanfaatkan transaksi atomik pipeline untuk memutus kondisi balapan (Race Condition)
            pipe = self._redis_client.pipeline()
            pipe.incr(bucket)
            pipe.expire(bucket, self.window_seconds + 5)  # Buffer 5 detik ekstra untuk expiry bersih

            responses = pipe.execute()
            count = int(responses[0])

            remaining = max(self.limit - count, 0)
            allowed = count <= self.limit
            logger.debug("Redis rate limit check key=%s count=%d allowed=%s", key, count, allowed)
            return allowed, remaining, max(0, reset)

        except Exception as exc:
            # Sirkuit Pemutus Cadangan (Circuit Breaker): Jika Redis crash runtime mendadak,
            # alihkan permintaan menuju engine subsistem memori lokal agar API tidak mati total.
            logger.error("Redis pipeline failed, falling back to memory: %s", exc)
            return self._memory_check(key)

    def allow(self, key: str) -> Tuple[bool, int, int]:
        """
        Gerbang Penilai Akses Utama (Rate-Limit Enforcement Point).
        Mengevaluasi identitas token penunjuk secara aman dan mengembalikan skema tuple:
        (is_allowed, remaining_quota, reset_seconds)
        """
        if not isinstance(key, str) or not key.strip():
            logger.error("RATE_LIMITER_INVALID_KEY: %r", key)
            raise ValueError("RATE_LIMITER_ERROR_KEY_MUST_BE_A_PURE_NON_EMPTY_STRING")

        clean_key = key.strip()

        if self._redis_client is not None:
            return self._redis_check(clean_key)
        return self._memory_check(clean_key)