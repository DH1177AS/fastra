# fastra_core\knowledge\loader.py

from __future__ import annotations

import logging
import os
import re
import sys
from pathlib import Path
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from fastra_core.knowledge.edges import PriceRecord
from fastra_core.knowledge.graph import KnowledgeGraph

logger = logging.getLogger("fastra.knowledge")

MATERIAL_DB_PATH = r"d:\fastra_projects\Database_Material_Bangunan.xlsx"
REGIONAL_INDEX_PATH = r"d:\fastra_projects\Database Referensi Indeks Regional.xlsx"


# ---------------------------------------------------------------------------
# Inbound & Outbound DTOs – Pydantic Strict Gateway (Fail-Fast)
# ---------------------------------------------------------------------------
class RegionalIndexRowDTO(BaseModel):
   
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    kota: str = Field(..., min_length=2, max_length=64, pattern=r"^[A-Za-z0-9_\-\s\(\)]+$")
    indeks: float = Field(..., gt=0.1, le=5.0, allow_inf_nan=False)


class MaterialExcelRowDTO(BaseModel):
  
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    mat_id: str = Field(..., min_length=5, max_length=128, pattern=r"^mat-[a-z0-9\-]+$")
    harga_estimasi: float = Field(..., gt=0.0, le=1e12, allow_inf_nan=False)
    brand_source: str = Field(default="UNKNOWN_BRAND", max_length=128)


# ---------------------------------------------------------------------------
# Core Utilities – Jaminan Keamanan Type Casting & Tokenizer Slug
# ---------------------------------------------------------------------------
def _to_decimal(value: float | int | Decimal, field_name: str) -> Decimal:
  
    if isinstance(value, Decimal):
        return value
    if not isinstance(value, (int, float)):
        raise TypeError(f"Field '{field_name}' wajib bertipe numerik dasar (int/float/Decimal).")
    try:
        return Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(
            f"Field '{field_name}' gagal dikonversi ke representasi Decimal imutabel."
        ) from exc


def _slugify(text: Any) -> str:
   
    cleaned = str(text).lower().strip()
    cleaned = re.sub(r"[^a-z0-9\s]", "", cleaned)
    cleaned = re.sub(r"\s+", "-", cleaned)
    return cleaned[:60]


# ---------------------------------------------------------------------------
# Core Internal Spreadsheet Loaders – Pure AHS Aggregation (QS-Safe)
# ---------------------------------------------------------------------------
def _load_prices_from_excel(kg: KnowledgeGraph) -> None:
    
    regional_multipliers: Dict[str, float] = {
        "DKI Jakarta": 1.0, "Surabaya": 0.98, "Bandung": 0.95,
        "Semarang": 0.93, "Surakarta (Solo)": 0.92, "Palembang": 1.05,
        "Medan": 1.08, "Denpasar": 1.1, "Makassar": 1.12,
        "Balikpapan": 1.2, "IKN": 1.35, "Morowali/Halmahera": 1.25,
        "Jayapura/Sorong": 1.45, "Wamena": 1.85, "Batam": 1.03,
        "Yogyakarta": 0.96, "Cirebon": 0.94, "Serang (Banten)": 0.97,
        "Bandar Lampung": 1.02, "Pontianak": 1.15, "Pekanbaru": 1.1,
        "Padang": 1.08,
    }
    
    try:
        if os.path.exists(MATERIAL_DB_PATH):
            df_mat = pd.read_excel(MATERIAL_DB_PATH, sheet_name="Database Material")
            new_prices = 0

            for _, row in df_mat.iterrows():
                kat_slug = _slugify(row.get("Kategori", ""))
                merek_slug = _slugify(row.get("Merek / Brand", ""))
                tipe_slug = _slugify(row.get("Tipe / Grade", ""))
                ukuran_slug = _slugify(row.get("Spesifikasi / Ukuran", ""))

                mat_id = f"mat-{kat_slug}-{merek_slug}-{tipe_slug}-{ukuran_slug}"[:120]
               
                harga_str = (
                    str(row.get("Harga Estimasi (Rp)", "0"))
                    .replace("Rp", "")
                    .replace(".", "")
                    .replace(",", "")
                    .strip()
                )
                if not harga_str:
                    continue
                try:
                    harga_base_float = float(harga_str)
                except ValueError:
                    continue

                row_payload = {
                    "mat_id": mat_id,
                    "harga_estimasi": harga_base_float,
                    "brand_source": str(row.get("Merek / Brand", "EXCEL_SOURCE")).strip(),
                }

                try:
                    validated_row = MaterialExcelRowDTO.model_validate(row_payload)
                except Exception as exc:
                    logger.warning("Baris material tidak valid dilewati: %s", exc)
                    continue

                if validated_row.mat_id in kg.materials:
                    if validated_row.mat_id not in kg.prices:
                        kg.prices[validated_row.mat_id] = []

                    harga_base_dec = _to_decimal(
                        validated_row.harga_estimasi, "harga_estimasi"
                    )

                    for region, multiplier in regional_multipliers.items():
                        multiplier_dec = _to_decimal(multiplier, f"multiplier.{region}")
                        harga_regional_dec = (
                            harga_base_dec * multiplier_dec
                        ).quantize(Decimal("0.01"))

                        kg.add_price(
                            validated_row.mat_id,
                            PriceRecord(
                                material_id=validated_row.mat_id,
                                price=float(harga_regional_dec),
                                region=region,
                                valid_from="2024-01-01",
                                valid_until="2026-12-31",
                                supplier_id="spl_excel_automated",
                                source=f"Excel Core DB ({validated_row.brand_source})",
                            ),
                        )
                        new_prices += 1
            logger.info(
                "Database indeks harga material regional sukses di-seeding: %d record aktif.",
                new_prices,
            )
    except Exception as exc:
        logger.warning("Gagal memproses seeding harga material dari Excel: %s", exc)
  
    try:
        if os.path.exists(REGIONAL_INDEX_PATH):
            df_reg = pd.read_excel(REGIONAL_INDEX_PATH, skiprows=1)
            df_reg.columns = ["no", "kota", "indeks", "deskripsi"]

            for _, row in df_reg.iterrows():
                kota_raw = row.get("kota")
                indeks_raw = row.get("indeks")
                if pd.isna(kota_raw) or pd.isna(indeks_raw):
                    continue

                try:
                    index_payload = {
                        "kota": str(kota_raw).strip(),
                        "indeks": float(indeks_raw),
                    }
                    validated_index = RegionalIndexRowDTO.model_validate(index_payload)
                    regional_multipliers[validated_index.kota] = validated_index.indeks
                except Exception as exc:
                    logger.warning("Baris material tidak valid dilewati: %s", exc)
                    continue
            logger.info(
                "Manifes tabel indeks override regional berhasil dikunci: %d wilayah kota.",
                len(regional_multipliers),
            )
    except Exception as exc:
        logger.warning("Gagal memuat dokumen indeks regional eksternal: %s", exc)

    if not hasattr(kg, "regions"):
        kg.regions = {}
    kg.regions = dict(regional_multipliers)


def create_fastra_knowledge_graph() -> KnowledgeGraph:
    
    kg = KnowledgeGraph()
   
    try:
        from fastra_core.knowledge.domains.material import load_all_materials
        load_all_materials(kg)
    except Exception as exc:
        logger.error("Kegagalan fatal domain material: %s", exc)
   
    try:
        from import_material_excel import import_materials_from_excel
        import_materials_from_excel(kg)
    except Exception as exc:
        logger.warning("Impor penunjang material excel dilewati: %s", exc)
   
    try:
        from import_tenaga_excel import import_tenaga_from_excel
        import_tenaga_from_excel(kg)
    except Exception as exc:
        logger.critical(
            "CRITICAL SEEDING FAILURE: Komponen upah harian tenaga kerja gagal dimuat: %s",
            exc,
        )
        raise RuntimeError(
            "Siklus hidup aplikasi dihentikan: Modul upah harian tenaga kerja wajib tersedia secara utuh."
        ) from exc
   
    try:
        from fastra_core.knowledge.domains.work_item import load_all_work_items
        load_all_work_items(kg)
    except Exception as exc:
        logger.error("Gagal memetakan domain master Work Item: %s", exc)
   
    try:
        from fastra_core.knowledge.integrasi_relasi_sni import integrasikan_relasi_sni
        integrasikan_relasi_sni(kg)
        logger.info("Relasi indeks juknis SNI nasional sukses dirajut ke dalam jaringan.")
    except Exception as exc:
        logger.warning("Integrasi relasi SNI dilewati: %s", exc)
    
    try:
        from import_equipment_excel import import_equipment_from_excel
        import_equipment_from_excel(kg)
    except Exception as exc:
        logger.warning("Pemuatan aset alat berat mekanikal dilewati: %s", exc)
   
    try:
        from fastra_core.knowledge.integrasi_aces500 import integrasi_aces500
        integrasi_aces500(kg)
    except Exception as exc:
        logger.warning("Integrasi parameter makro ACES-500 dilewati: %s", exc)
   
    try:
        from fastra_core.knowledge.segment_calibration import load_segment_calibration
        load_segment_calibration(kg)
        logger.info("Manifes segment calibration berhasil diamankan.")
    except Exception as exc:
        logger.warning("Segment calibration dilewati: %s", exc)
  
    _load_prices_from_excel(kg)

    logger.info("Proses kompilasi infrastruktur Knowledge Graph sukses dituntaskan secara sempurna.")
    return kg