"""
Materials Excel Importer Engine
Mengimpor data material bangunan dari berkas Excel ke dalam skema Knowledge Graph secara aman.
Menggunakan Decimal, validasi path aman, logging terstruktur, dan pencegahan duplikasi.
"""

from __future__ import annotations

import logging
import os
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd

# ------------------------------------------------------------------------------
# Logging Configuration
# ------------------------------------------------------------------------------
logger = logging.getLogger("fastra_core.materials_importer")
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
)

# ------------------------------------------------------------------------------
# Path Setup (Safe & Relatif)
# ------------------------------------------------------------------------------
TARGET_CORE_PATH = os.getenv("FASTRA_CORE_PATH", str(Path(__file__).parent.parent))
SANITY_PATH = Path(TARGET_CORE_PATH).resolve()
if not SANITY_PATH.is_dir():
    logger.critical("Core directory does not exist at %s", SANITY_PATH)
    sys.exit(1)

if str(SANITY_PATH) not in sys.path:
    sys.path.insert(0, str(SANITY_PATH))

# Import internal setelah path siap
try:
    from fastra_core.knowledge.graph import KnowledgeGraph
    from fastra_core.knowledge.nodes import MaterialNode
except ImportError as exc:
    logger.critical("Failed to import required modules: %s", exc)
    raise

# ------------------------------------------------------------------------------
# 1. DATA SANITIZATION & SLUG GENERATOR
# ------------------------------------------------------------------------------
def generate_secure_slug(text: Any) -> str:
    """Menghasilkan slug aman untuk ID entitas, hanya huruf kecil, angka, dan dash."""
    clean_text = str(text).lower().strip()
    clean_text = re.sub(r"[^a-z0-9\s-]", "", clean_text)  # hanya izinkan a-z, 0-9, spasi, dash
    clean_text = re.sub(r"[\s-]+", "-", clean_text)       # ganti spasi/dash berulang jadi satu dash
    return clean_text[:60].strip("-")


# ------------------------------------------------------------------------------
# 2. DOMAIN CONVERTER & VALIDATOR
# ------------------------------------------------------------------------------
class MaterialRowDomainConverter:
    """Mengonversi baris Excel menjadi data domain yang aman dan tervalidasi."""

    def __init__(self, row: pd.Series) -> None:
        self.row = row

    def extract_string(self, column_name: str) -> str:
        value = self.row.get(column_name)
        if pd.isna(value) or value is None:
            return ""
        return str(value).strip()

    def extract_price_decimal(self, column_name: str) -> Decimal:
        value = self.row.get(column_name)
        if pd.isna(value) or value is None:
            return Decimal("0.00")
        try:
            # Sanitasi string mata uang: hilangkan RP, titik, koma, spasi
            clean_str = str(value).upper().replace("RP", "").replace(".", "").replace(",", "").strip()
            if not clean_str:
                return Decimal("0.00")
            dec = Decimal(clean_str)
            if not dec.is_finite():
                return Decimal("0.00")
            return dec
        except (ValueError, InvalidOperation):
            return Decimal("0.00")


# ------------------------------------------------------------------------------
# 3. EXCEL IMPORTER (TRANSACTIONAL & ANTI-DUPLIKASI)
# ------------------------------------------------------------------------------
def import_materials_from_excel(kg: KnowledgeGraph) -> int:
    """Import material dari Excel ke Knowledge Graph dengan rollback aman dan pencegahan duplikasi."""
    if not isinstance(kg, KnowledgeGraph):
        logger.error("Parameter kg harus instance KnowledgeGraph")
        return 0

    # Path Excel dari env var dengan default relatif ke proyek
    default_filepath = Path(__file__).parent.parent / "Database_Material_Bangunan.xlsx"
    configured_filepath = os.getenv("FASTRA_MATERIAL_EXCEL_PATH", str(default_filepath))
    excel_path = Path(configured_filepath).resolve()

    if not excel_path.is_file():
        logger.error("Target material Excel file missing at %s", excel_path)
        return 0

    try:
        df = pd.read_excel(str(excel_path), sheet_name="Database Material")
    except Exception as exc:
        logger.exception("Error reading Excel workspace: %s", exc)
        return 0

    logger.info("Jumlah baris material terdeteksi di Excel: %d", len(df))

    # Backup existing materials untuk rollback jika terjadi kegagalan fatal
    original_materials = dict(getattr(kg, "materials", {}))
    try:
        # Set existing IDs untuk pencegahan duplikasi
        existing_ids: Set[str] = set()
        if hasattr(kg, "materials") and isinstance(kg.materials, dict):
            existing_ids = set(str(k) for k in kg.materials.keys())

        successful_import_count = 0
        skipped_duplicate_count = 0

        for idx, row in df.iterrows():
            if not isinstance(row, pd.Series):
                continue

            try:
                converter = MaterialRowDomainConverter(row)

                merek = converter.extract_string("Merek / Brand")
                tipe = converter.extract_string("Tipe / Grade")
                ukuran = converter.extract_string("Spesifikasi / Ukuran")
                kategori_raw = converter.extract_string("Kategori")
                sub_kategori = converter.extract_string("Sub Kategori")
                satuan = converter.extract_string("Satuan")
                catatan = converter.extract_string("Catatan")

                # Penapisan fail-fast: jika identitas utama kosong, lewati baris
                if not kategori_raw and not merek:
                    continue

                # Generate ID dengan prefix mat_ dan slug
                kat_slug = generate_secure_slug(kategori_raw)
                merek_slug = generate_secure_slug(merek)
                tipe_slug = generate_secure_slug(tipe)
                ukuran_slug = generate_secure_slug(ukuran)

                material_id_raw = f"mat_{kat_slug}_{merek_slug}_{tipe_slug}_{ukuran_slug}"
                secure_mat_id = material_id_raw[:120].rstrip("_")

                if secure_mat_id in existing_ids:
                    skipped_duplicate_count += 1
                    continue

                # Harga dalam Decimal untuk presisi finansial
                price_decimal = converter.extract_price_decimal("Harga Estimasi (Rp)")

                # Buat MaterialNode (asumsikan constructor menerima Decimal untuk harga)
                node = MaterialNode(
                    id=secure_mat_id,
                    name=f"{merek} {tipe} - {ukuran}".strip(),
                    unit=satuan,
                    category=kategori_raw,
                    specifications={
                        "sub_kategori": sub_kategori,
                        "merek": merek,
                        "tipe": tipe,
                        "ukuran": ukuran,
                        "harga_patokan": price_decimal,  # Decimal, bukan float
                        "sumber": "Excel Database",
                        "catatan": catatan,
                    },
                )

                kg.add_material(node)
                existing_ids.add(secure_mat_id)
                successful_import_count += 1

                if successful_import_count % 1000 == 0:
                    logger.info("   %d material berhasil diproses...", successful_import_count)

            except Exception as row_exc:
                logger.error("Baris %d gagal diproses: %s", idx, row_exc)

        logger.info("Material baru berhasil dimuat: %d", successful_import_count)
        logger.info("Duplikat dilewati: %d", skipped_duplicate_count)
        return successful_import_count

    except Exception as exc:
        # Rollback transaksional
        if hasattr(kg, "materials"):
            kg.materials = original_materials
        logger.exception("Import material gagal total, rollback dilakukan. Error: %s", exc)
        return 0


if __name__ == "__main__":
    knowledge_graph = KnowledgeGraph()
    imported = import_materials_from_excel(knowledge_graph)
    total_materials = len(getattr(knowledge_graph, "materials", {}))
    logger.info("Proses import selesai. Total material di KG: %d", total_materials)