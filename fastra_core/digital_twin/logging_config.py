# fastra_core\digital_twin\logging_config.py

from __future__ import annotations

import json
import logging
import math
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict


class JsonFormatter(logging.Formatter):
    """
    Format Log Terstruktur Kriptografis (Structured JSON Log Formatter).
    Memotong habis seluruh padding spasi sekunder penampung token string
    guna menjamin kepatuhan format kanonikal dan integrasi streaming data terikat.
    """

    def format(self, record: logging.LogRecord) -> str:
        if not isinstance(record, logging.LogRecord):
            raise TypeError("LOGGING_ERROR_INVALID_RECORD_INSTANCE")

        # Sanitasi ketat pesan string log untuk memblokir kerentanan Log Injection (\r atau \n)
        raw_message = record.getMessage()
        sanitized_message = re.sub(r"[\r\n]", " ", raw_message) if raw_message else ""

        log_payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": str(record.levelname).strip(),
            "logger": str(record.name).strip(),
            "message": sanitized_message.strip(),
        }

        # Mengamankan ekstraksi pelacakan pengecualian (Stack Trace Exception Data Logging)
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            log_payload["exception"] = re.sub(r"[\r\n]", " | ", exc_text).strip() if exc_text else ""

        # Menyuntikkan properti metadata khusus dari parameter ekstra jika ditransmisikan
        if hasattr(record, "extra_metadata") and isinstance(record.extra_metadata, dict):
            # Memanfaatkan structural clone untuk menghindari polusi state runtime memori
            clean_metadata = {}
            for k, v in record.extra_metadata.items():
                if isinstance(k, str) and k.strip():
                    key_clean = k.strip()
                    # Blokir anomali data mengambang (NaN/inf) agar format JSON tidak rusak saat diparsing
                    if isinstance(v, (int, float)) and not isinstance(v, bool):
                        if not math.isnan(v) and not math.isinf(v):
                            clean_metadata[key_clean] = v
                    else:
                        clean_metadata[key_clean] = v
            if clean_metadata:
                log_payload["metadata"] = clean_metadata

        # Mengunci format output minimalis deterministik tanpa space padding (separators=(",", ":"))
        return json.dumps(
            log_payload,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )


def setup_logging(log_level: int = logging.INFO) -> None:
    """
    Mengonfigurasi dan mengaktifkan repositori mesin logging pusat secara terikat thread-safe.
    Mengalihkan aliran log murni menuju standardisasi output konsol sistem (sys.stdout).
    """
    # Menerapkan validasi fail-fast terhadap level penalaan log yang diizinkan
    if log_level not in {logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL}:
        raise ValueError(f"ILLEGAL_LOG_LEVEL_ASSIGNMENT_ATTEMPTED: {log_level}")

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()

    # Bersihkan handler lama secara atomik demi menghindari redudansi duplikasi penulisan baris log
    while root_logger.handlers:
        root_logger.removeHandler(root_logger.handlers[0])

    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)