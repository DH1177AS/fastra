"""
Atomic transaction helper untuk Digital Twin DB.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from fastra_core.digital_twin.database_extended import ExtendedDigitalTwinDB


@contextmanager
def atomic(db: ExtendedDigitalTwinDB) -> Iterator[None]:
    """Bungkus operasi DB dalam satu transaksi atomik."""
    session = db.SessionLocal()
    try:
        with session.begin():
            yield
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
