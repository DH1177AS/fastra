"""
fastra_core/knowledge/domains/material/__init__.py

Paket pemuat data material konstruksi.
Mengorkestrasi pemuatan seluruh sub-domain material secara berurutan dan aman.
"""

from __future__ import annotations

import logging

from fastra_core.knowledge.graph import KnowledgeGraph

# Import fungsi pemuat data material dari masing-masing sub-domain
from .semen_dan_perekat import load_semen
from .besi_dan_baja import load_besi_baja
from .beton_dan_agregat import load_beton_agregat
from .kayu_dan_plywood import load_kayu_plywood
from .dinding_dan_partisi import load_dinding_partisi
from .lantai_dan_keramik import load_lantai_keramik
from .atap_dan_genteng import load_atap_genteng
from .plafon_dan_rangka import load_plafon_rangka
from .cat_dan_pelapis import load_cat_pelapis
from .pipa_dan_fitting import load_pipa_fitting
from .kabel_dan_listrik import load_kabel_listrik
from .sanitair_dan_plumbing import load_sanitair_plumbing
from .material_khusus import load_material_khusus

logger = logging.getLogger("fastra.knowledge")


def load_all_materials(kg: KnowledgeGraph) -> None:
    """
    Mengorkestrasi pemuatan berantai (cascading) seluruh basis data material konstruksi
    ke dalam Knowledge Graph. Menjamin keutuhan pengisian kontainer memori sejak hulu.
    """
    if not isinstance(kg, KnowledgeGraph):
        raise TypeError("Parameter 'kg' wajib berupa instance KnowledgeGraph.")

    # Eksekusi pemuatan seeder bertahap untuk merajut jaringan material
    load_semen(kg)
    load_besi_baja(kg)
    load_beton_agregat(kg)
    load_kayu_plywood(kg)
    load_dinding_partisi(kg)
    load_lantai_keramik(kg)
    load_atap_genteng(kg)
    load_plafon_rangka(kg)
    load_cat_pelapis(kg)
    load_pipa_fitting(kg)
    load_kabel_listrik(kg)
    load_sanitair_plumbing(kg)
    load_material_khusus(kg)

    # Menghitung total material yang berhasil dimuat
    total_materials_count = len(getattr(kg, "materials", {}) or {})

    logger.info(
        "Kompilasi orkestrasi data material selesai: %d master nodes berhasil diamankan.",
        total_materials_count,
    )


__all__ = [
    "load_all_materials",
    "load_semen",
    "load_besi_baja",
    "load_beton_agregat",
    "load_kayu_plywood",
    "load_dinding_partisi",
    "load_lantai_keramik",
    "load_atap_genteng",
    "load_plafon_rangka",
    "load_cat_pelapis",
    "load_pipa_fitting",
    "load_kabel_listrik",
    "load_sanitair_plumbing",
    "load_material_khusus",
]
