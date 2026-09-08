# fastra_core\digital_twin\transaction.py

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Iterator

from fastra_core.digital_twin.database_extended import ExtendedDigitalTwinDB

logger = logging.getLogger("fastra_core.digital_twin.transaction")


@contextmanager
def atomic(db: Any) -> Iterator[Any]:
    """
    Context manager formal untuk membungkus operasi database dalam satu transaksi atomik terisolasi.
    Menjamin otomatisasi komit jika sukses, melakukan rollback penuh jika terjadi interupsi,
    serta memastikan penutupan alokasi memori sesi secara mutlak hulu-ke-hilir.
    """
    if db is None:
        logger.error("TRANSACTION_ERROR_DATABASE_INSTANCE_CANNOT_BE_NULL")
        raise ValueError("TRANSACTION_ERROR_DATABASE_INSTANCE_CANNOT_BE_NULL")

    if not isinstance(db, ExtendedDigitalTwinDB):
        logger.error("INVALID_DATABASE_TYPE_EXPECTED_EXTENDED_DIGITAL_TWIN_DB: %r", db)
        raise TypeError("TRANSACTION_ERROR_DATABASE_MUST_BE_EXTENDED_DIGITAL_TWIN_DB_INSTANCE")

    if not hasattr(db, "SessionLocal") or not callable(db.SessionLocal):
        logger.error("INVALID_DATABASE_INSTANCE_MISSING_SESSION_FACTORY")
        raise AttributeError("INVALID_DATABASE_INSTANCE_MISSING_SESSION_FACTORY")

    # Instansiasi objek sesi mandiri terisolasi murni dari connection pool hulu
    session = db.SessionLocal()

    try:
        # Memanfaatkan protokol context manager internal .begin() SQLAlchemy 2.0
        # Secara otomatis mengontrol komit atomik hulu dan memangkas redudansi komit manual ganda.
        with session.begin():
            # Mentransmisikan instansiasi objek sesi aktif menuju internal blok pekerja konsumen (yield session)
            yield session

    except Exception as transaction_exception:
        # Melakukan interupsi pemulihan state awal (Transaction Rollback) secara fail-fast
        try:
            session.rollback()
        except Exception as rollback_sub_exception:
            # Mengamankan sistem dari kegagalan berantai sekunder jika server DB terputus mendadak
            logger.critical(
                "[CRITICAL_DATABASE_FAILURE] Rollback operation failed: %s",
                rollback_sub_exception,
            )

        logger.error(
            "[TRANSACTION_ABORTED] Database operation collapsed. Rollback executed safely. Error: %s",
            transaction_exception,
        )
        raise RuntimeError(
            f"GLOBAL_TRANSACTION_ATOMIC_BLOCK_FAILED_ROLLBACK_EXECUTED: {transaction_exception}"
        ) from transaction_exception

    finally:
        # Menjamin pengembalian slot koneksi menuju connection pool sistem secara mutlak demi mencegah memory leaks
        session.close()
        logger.debug("Database session closed cleanly")