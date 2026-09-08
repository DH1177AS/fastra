"""
Equipment Excel Importer Engine
Mengimpor data alat berat dari berkas Excel ke dalam Knowledge Graph secara transaksional.
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
logger = logging.getLogger("fastra_core.equipment_importer")
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
    from fastra_core.knowledge.nodes import EquipmentNode
except ImportError as exc:
    logger.critical("Failed to import required modules: %s", exc)
    raise

# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------
VALID_UNIT_TYPES = {"Hari", "Jam", "Bulan"}

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
class EquipmentRowDomainConverter:
    """Mengonversi baris Excel menjadi data domain yang aman dan tervalidasi."""

    def __init__(self, row: pd.Series) -> None:
        self.row = row

    def extract_string(self, column_name: str) -> str:
        value = self.row.get(column_name)
        if pd.isna(value) or value is None:
            return ""
        return str(value).strip()

    def extract_decimal(self, column_name: str) -> Decimal:
        value = self.row.get(column_name)
        if pd.isna(value) or value is None:
            return Decimal("0.00")
        try:
            clean_str = str(value).strip().replace(",", "")
            dec = Decimal(clean_str)
            if not dec.is_finite():
                return Decimal("0.00")
            return dec
        except (ValueError, InvalidOperation):
            return Decimal("0.00")


# ------------------------------------------------------------------------------
# 3. EXCEL IMPORTER (TRANSACTIONAL)
# ------------------------------------------------------------------------------
def import_equipment_from_excel(kg: KnowledgeGraph) -> int:
    """Import equipment dari Excel ke Knowledge Graph dengan rollback aman."""
    if not isinstance(kg, KnowledgeGraph):
        logger.error("Parameter kg harus instance KnowledgeGraph")
        return 0

    # Path Excel dari env var dengan default relatif ke proyek
    default_filepath = Path(__file__).parent.parent / "Database Equipment.xlsx"
    configured_filepath = os.getenv("FASTRA_EQUIPMENT_EXCEL_PATH", str(default_filepath))
    excel_path = Path(configured_filepath).resolve()

    if not excel_path.is_file():
        logger.error("Target Excel file missing at %s", excel_path)
        return 0

    try:
        df = pd.read_excel(str(excel_path), sheet_name="Database Equipment", header=2)
    except Exception as exc:
        logger.exception("Error reading Excel workspace: %s", exc)
        return 0

    logger.info("Jumlah alat terdeteksi di Excel: %d", len(df))

    # Backup existing equipments untuk rollback
    original_equipments = dict(kg.equipments)
    try:
        kg.equipments.clear()
        successful_import_count = 0

        for idx, row in df.iterrows():
            if not isinstance(row, pd.Series):
                continue

            try:
                no_value = row.get("No")
                if pd.isna(no_value) or no_value is None:
                    continue

                converter = EquipmentRowDomainConverter(row)

                nama = converter.extract_string("Nama Alat Berat Konstruksi")
                kategori = converter.extract_string("Rumpun Kategori Alat")
                model = converter.extract_string("Model / Kode Seri Acuan Pabrikan")
                spesifikasi = converter.extract_string("Spesifikasi & Kapasitas Teknis Lapangan")
                satuan = converter.extract_string("Jenis Satuan")
                kapasitas = converter.extract_string("Koefisien Kapasitas Produksi Efektif / Jam Kerja")

                # Validasi unit
                if satuan not in VALID_UNIT_TYPES:
                    logger.warning("Baris %d: satuan '%s' tidak valid, dilewati.", idx, satuan)
                    continue

                tarif_decimal = converter.extract_decimal("Tarif Sewa Dasar Jakarta (Rp)")

                if not nama or not model:
                    logger.warning("Baris %d: Nama atau Model kosong, dilewati.", idx)
                    continue

                # Generate ID dengan prefix eqp_
                slug_nama = generate_secure_slug(nama)
                slug_model = generate_secure_slug(model)
                equipment_id = f"eqp_{slug_nama}_{slug_model}"[:100].rstrip("_")

                # Mapping tarif sewa berdasarkan satuan
                rate_per_day: Optional[Decimal] = None
                rate_per_month: Optional[Decimal] = None
                if satuan in {"Hari", "Jam"}:
                    rate_per_day = tarif_decimal
                elif satuan == "Bulan":
                    rate_per_month = tarif_decimal

                # Buat EquipmentNode (asumsikan constructor menerima Decimal untuk rate)
                node = EquipmentNode(
                    id=equipment_id,
                    name=f"{nama} - {model}",
                    unit=satuan,
                    rate_per_day=rate_per_day,
                    rate_per_month=rate_per_month,
                    category=kategori,
                    specifications={
                        "model": model,
                        "spesifikasi": spesifikasi,
                        "kapasitas": kapasitas,
                        "kategori": kategori,
                        "sumber": "Excel Database Equipment",
                    },
                )

                kg.add_equipment(node)
                successful_import_count += 1

            except Exception as row_exc:
                error_item_name = str(row.get("Nama Alat Berat Konstruksi", "?"))
                logger.error("Baris %d (%s) gagal: %s", idx, error_item_name, row_exc)

        logger.info("Total equipment berhasil dimuat: %d", len(kg.equipments))
        return successful_import_count

    except Exception as exc:
        # Rollback transaksional
        kg.equipments = original_equipments
        logger.exception("Import equipment gagal total, rollback dilakukan. Error: %s", exc)
        return 0


if __name__ == "__main__":
    knowledge_graph = KnowledgeGraph()
    imported = import_equipment_from_excel(knowledge_graph)
    logger.info("Proses import selesai. Jumlah data baru: %d", imported)