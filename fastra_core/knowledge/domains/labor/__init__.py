# fastra_core\knowledge\domains\labor\__init__.py

from __future__ import annotations

import logging
from typing import Any, List

# Impor fungsi pemuat data upah terverifikasi dari masing-masing sub-domain spesialis
from .tenaga_umum import load_tenaga_umum
from .tenaga_spesialis_batu import load_tenaga_spesialis_batu
from .tenaga_spesialis_kayu import load_tenaga_spesialis_kayu
from .tenaga_spesialis_besi import load_tenaga_spesialis_besi
from .tenaga_spesialis_listrik import load_tenaga_spesialis_listrik
from .tenaga_spesialis_plumbing import load_tenaga_spesialis_plumbing
from .tenaga_spesialis_cat import load_tenaga_spesialis_cat
from .tenaga_spesialis_atap import load_tenaga_spesialis_atap
from .operator_alat_berat import load_operator_alat_berat
from .tenaga_profesional import load_tenaga_profesional

logger = logging.getLogger("fastra.knowledge")


def load_all_labors(kg: Any) -> None:
    """
    Mengorkestrasi pemuatan berantai (Cascading Load) seluruh basis data upah tenaga kerja.
    Menjamin keutuhan pengisian kontainer memori KnowledgeGraph sejak hulu.
    """
    # Eksekusi pemuatan seeder bertahap untuk merajut jaringan upah Orang Hari (OH)
    load_tenaga_umum(kg)
    load_tenaga_spesialis_batu(kg)
    load_tenaga_spesialis_kayu(kg)
    load_tenaga_spesialis_besi(kg)
    load_tenaga_spesialis_listrik(kg)
    load_tenaga_spesialis_plumbing(kg)
    load_tenaga_spesialis_cat(kg)
    load_tenaga_spesialis_atap(kg)
    load_operator_alat_berat(kg)
    load_tenaga_profesional(kg)

    # Menghitung jumlah total riil data labors terenkapsulasi di dalam memori grafik
    total_labors_count = len(getattr(kg, "labors", {}) or {})
    logger.info(
        "Kompilasi orkestrasi data tenaga kerja selesai: %d entitas Orang Hari berhasil diamankan ke dalam repositori.",
        total_labors_count
    )


# Eksportir Publik Eksplisit (Compiler Linting & Namespace Protection)
__all__ = [
    "load_all_labors",
    "load_tenaga_umum",
    "load_tenaga_spesialis_batu",
    "load_tenaga_spesialis_kayu",
    "load_tenaga_spesialis_besi",
    "load_tenaga_spesialis_listrik",
    "load_tenaga_spesialis_plumbing",
    "load_tenaga_spesialis_cat",
    "load_tenaga_spesialis_atap",
    "load_operator_alat_berat",
    "load_tenaga_profesional",
]