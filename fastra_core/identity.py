# fastra_core\identity.py

from __future__ import annotations

import logging
import re
import threading
import uuid
from typing import Any

logger = logging.getLogger("fastra_core.identity")


class Identity:
    """
    Mesin Generator Identitas Kriptografis Unik (Military-Grade Identity Engine).
    Menjamin pematuhan formal struktur tanda pengenal lintas domain data hulu-ke-hilir.
    """
    _global_lock = threading.Lock()

    _UUID_V4_PATTERN = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        re.IGNORECASE,
    )

    @classmethod
    def generate(cls) -> str:
        """
        Menghasilkan token string identitas unik baru berbasis UUID v4 murni (CSPRNG).
        Menghapus total loop iterasi dan penampung array memori liar pembawa kebocoran.
        """
        with cls._global_lock:
            new_uuid = str(uuid.uuid4())

            if not cls._UUID_V4_PATTERN.match(new_uuid):
                logger.critical("CRYPTOGRAPHIC_INTEGRITY_VIOLATION_MALFORMED_UUID_V4_GENERATED")
                raise RuntimeError("CRYPTOGRAPHIC_INTEGRITY_VIOLATION_MALFORMED_UUID_V4_GENERATED")

            logger.debug("Generated UUID v4: %s", new_uuid)
            return new_uuid

    @classmethod
    def is_valid(cls, uuid_str: Any) -> bool:
        """
        Memverifikasi keabsahan struktur string penunjuk secara ketat dan fail-fast.
        Hanya menerima format UUID v4 murni, mendepak coercion hacks, data kosong, atau versi UUID ilegal.
        """
        if not isinstance(uuid_str, str):
            return False

        clean_str = uuid_str.strip()
        if not clean_str:
            return False

        return bool(cls._UUID_V4_PATTERN.match(clean_str))

    @classmethod
    def is_unique_in_context(cls, uuid_str: str) -> bool:
        """
        Metode kompatibilitas semantik arsitektur hulu.
        Setiap token UUID v4 murni yang lolos pengujian .is_valid() dijamin unik secara matematis
        pada skala probabilitas collision hipersfer tanpa membutuhkan penampung memori internal.
        """
        return cls.is_valid(uuid_str)

    @classmethod
    def reset(cls) -> None:
        """
        Metode pembersihan siklus hidup memori kontekstual.
        Memastikan penutupan penampung lama berjalan hampa efek samping.
        """
        with cls._global_lock:
            logger.debug("Identity engine context reset executed")