"""
Labor Excel Importer Engine
Mengimpor data klasifikasi tenaga kerja konstruksi nasional dari Excel ke dalam Knowledge Graph.
Menggunakan Decimal, validasi path aman, logging terstruktur, dan rollback transaksional.
"""

from __future__ import annotations

import logging
import os
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

# ------------------------------------------------------------------------------
# Logging Configuration
# ------------------------------------------------------------------------------
logger = logging.getLogger("fastra_core.labor_importer")
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
    from fastra_core.knowledge.nodes import LaborNode
    from fastra_core.primitives.currency import Currency
except ImportError as exc:
    logger.critical("Failed to import required modules: %s", exc)
    raise

# ------------------------------------------------------------------------------
# 1. DATA SANITIZATION & SLUG GENERATOR
# ------------------------------------------------------------------------------
def generate_secure_slug(text: Any) -> str:
    """Menghasilkan slug aman untuk ID entitas, hanya huruf kecil, angka, dan dash."""
    clean_text = str(text).lower().strip()
    clean_text = re.sub(r"[^a-z0-9\s-]", "", clean_text)
    clean_text = re.sub(r"[\s-]+", "-", clean_text)
    return clean_text[:60].strip("-")


# ------------------------------------------------------------------------------
# 2. DOMAIN CONVERTER & VALIDATOR
# ------------------------------------------------------------------------------
class LaborRowDomainConverter:
    """Mengonversi baris Excel menjadi data domain yang aman dan tervalidasi."""

    def __init__(self, row: pd.Series) -> None:
        self.row = row

    def extract_string(self, column_name: str) -> str:
        value = self.row.get(column_name)
        if pd.isna(value) or value is None:
            return ""
        return str(value).strip()

    def extract_wage_decimal(self, column_name: str) -> Decimal:
        value = self.row.get(column_name)
        if pd.isna(value) or value is None:
            return Decimal("0.00")
        if isinstance(value, (int, float)):
            try:
                dec = Decimal(str(value))
                return dec if dec.is_finite() else Decimal("0.00")
            except (ValueError, InvalidOperation):
                return Decimal("0.00")
        try:
            clean_str = str(value).upper().replace("RP", "").replace(".", "").replace(",", "").strip()
            if not clean_str:
                return Decimal("0.00")
            dec = Decimal(clean_str)
            return dec if dec.is_finite() else Decimal("0.00")
        except (ValueError, InvalidOperation):
            return Decimal("0.00")


# ------------------------------------------------------------------------------
# 3. EXCEL IMPORTER (TRANSACTIONAL & ATOMIC)
# ------------------------------------------------------------------------------
def import_tenaga_from_excel(kg: KnowledgeGraph) -> int:
    """Import tenaga kerja dari Excel ke Knowledge Graph dengan rollback aman."""
    if not isinstance(kg, KnowledgeGraph):
        logger.error("Parameter kg harus instance KnowledgeGraph")
        return 0

    # Path Excel dari env var dengan default relatif ke proyek
    default_filepath = Path(__file__).parent.parent / "Database Tenaga Kerja Konstruksi Nasional.xlsx"
    configured_filepath = os.getenv("FASTRA_LABOR_EXCEL_PATH", str(default_filepath))
    excel_path = Path(configured_filepath).resolve()

    if not excel_path.is_file():
        logger.error("Target labor Excel file missing at %s", excel_path)
        return 0

    try:
        df = pd.read_excel(str(excel_path), sheet_name="Database Tenaga Kerja")
    except Exception as exc:
        logger.exception("Error reading labor Excel workspace: %s", exc)
        return 0

    logger.info("Jumlah baris tenaga kerja terdeteksi di Excel: %d", len(df))

    # Backup existing labors untuk rollback
    original_labors = dict(getattr(kg, "labors", {}))
    try:
        # Bersihkan state lama (atomic)
        if hasattr(kg, "labors") and hasattr(kg.labors, "clear"):
            kg.labors.clear()

        successful_import_count = 0
        failed_row_errors_count = 0

        for idx, row in df.iterrows():
            if not isinstance(row, pd.Series):
                continue

            try:
                converter = LaborRowDomainConverter(row)

                nama = converter.extract_string("Klasifikasi Tenaga Kerja")
                bidang = converter.extract_string("Rumpun Bidang Pekerjaan")
                jenis_upah = converter.extract_string("Jenis Upah")

                if not nama or not bidang:
                    logger.debug("Baris %d dilewati: nama atau bidang kosong", idx)
                    continue

                batas_bawah = converter.extract_wage_decimal("Batas Bawah (Rp)")
                batas_atas = converter.extract_wage_decimal("Batas Atas (Rp)")

                # Perhitungan rata-rata upah menggunakan Decimal
                upah_rata = (batas_bawah + batas_atas) / Decimal("2")

                # Normalisasi upah bulanan ke harian (22 hari kerja)
                if "Bulan" in jenis_upah:
                    upah_rata = upah_rata / Decimal("22")

                # Generate ID unik dengan prefix lab_
                slug_nama = generate_secure_slug(nama)
                labor_id = f"lab_{slug_nama}"[:80].rstrip("_")

                # Konversi ke objek Currency (Decimal-based)
                currency_rate = Currency(upah_rata)  # Asumsikan constructor menerima Decimal

                node = LaborNode(
                    id=labor_id,
                    name=nama,
                    role=bidang,
                    daily_rate=currency_rate,
                )

                kg.add_labor(node)
                successful_import_count += 1

            except Exception as row_exc:
                failed_row_errors_count += 1
                if failed_row_errors_count <= 3:  # Batasi logging detail error
                    error_item_name = str(row.get("Klasifikasi Tenaga Kerja", "?"))
                    logger.error("Baris %d (%s) gagal: %s", idx, error_item_name, row_exc)

        logger.info("Total tenaga kerja berhasil dimuat: %d", successful_import_count)
        if failed_row_errors_count > 0:
            logger.warning("Total baris gagal diproses: %d", failed_row_errors_count)

        return successful_import_count

    except Exception as exc:
        # Rollback transaksional
        if hasattr(kg, "labors"):
            kg.labors = original_labors
        logger.exception("Import tenaga kerja gagal total, rollback dilakukan. Error: %s", exc)
        return 0


if __name__ == "__main__":
    knowledge_graph = KnowledgeGraph()
    imported = import_tenaga_from_excel(knowledge_graph)
    total_labors = len(getattr(knowledge_graph, "labors", {}))
    logger.info("Proses import selesai. Total tenaga kerja di KG: %d", total_labors)