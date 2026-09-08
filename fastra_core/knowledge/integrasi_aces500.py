# fastra_core\knowledge\integrasi_aces500.py

from __future__ import annotations

import logging
import os
import re
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from fastra_core.knowledge.graph import KnowledgeGraph

logger = logging.getLogger("fastra.knowledge")

TAX_PATH = "D:/fastra_projects/Kualifikasi_BUJK_dan_Tarif_PPh_Final_Konstruksi.xlsx"
RISK_PATH = "D:/fastra_projects/Matriks_Manajemen_Risiko_Konstruksi_EMV.xlsx"
SCHED_PATH = "D:/fastra_projects/Sistem_Jadwal_KurvaS_dan_CashFlow.xlsx"
TEMPLATE_PATH = "D:/fastra_projects/Multi_Template_RAB_Resmi_Generator.xlsx"
ALT_PATH = "D:/fastra_projects/Alternatif_Material_Hemat.xlsx"


# ---------------------------------------------------------------------------
# Outbound Integrity DTOs – Pydantic Strict Gateway (Fail-Fast)
# ---------------------------------------------------------------------------
class RiskRegisterItemDTO(BaseModel):
   
    model_config = ConfigDict(extra="forbid", strict=True)

    id: str = Field(..., min_length=2, max_length=32, pattern=r"^[A-Za-z0-9_\-\.]+$")
    description: str = Field(..., min_length=2, max_length=1024)
    probability: float = Field(..., ge=0.0, le=100.0, allow_inf_nan=False)
    impact: float = Field(..., ge=0.0, le=1e14, allow_inf_nan=False)
    emv: float = Field(..., ge=0.0, le=1e14, allow_inf_nan=False)


class AlternativeMaterialDTO(BaseModel):
   
    model_config = ConfigDict(extra="forbid", strict=True)

    original_id: str = Field(..., min_length=5, max_length=128, pattern=r"^mat-[a-z0-9\-]+$")
    alternative_id: str = Field(..., min_length=5, max_length=128, pattern=r"^mat-[a-z0-9\-]+$")
    original_price: float = Field(..., gt=0.0, le=1e12, allow_inf_nan=False)
    alternative_price: float = Field(..., gt=0.0, le=1e12, allow_inf_nan=False)
    status: str = Field(..., min_length=2, max_length=64)


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
# Fungsi Integrasi Utama
# ---------------------------------------------------------------------------
def integrate_aces500(kg: KnowledgeGraph) -> KnowledgeGraph:
   
    if not isinstance(kg, KnowledgeGraph):
        raise TypeError("Parameter kg harus berupa instance KnowledgeGraph")

    # ---------------------------------------------------------------------------
    # 1. TARIF PAJAK & FISKAL SUBSYSTEM (PPN & PPh Final PUPR)
    # ---------------------------------------------------------------------------
    try:
        
        kg.ppn_rate = float(Decimal("0.12"))
        kg.pph_rate = float(Decimal("0.0265"))
        kg.tax_rates = {}

        if os.path.exists(TAX_PATH):
            df_tax = pd.read_excel(TAX_PATH, sheet_name="Tarif PPh Final", header=3)
            for _, row in df_tax.iterrows():
                kategori = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
                kualifikasi = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
                tarif_raw = row.iloc[3]

                if pd.notna(tarif_raw) and isinstance(tarif_raw, (int, float)):
                    tarif_decimal = _to_decimal(tarif_raw, "tax_rate")
                    kg.tax_rates.setdefault(kategori, {})[kualifikasi] = float(tarif_decimal)
            logger.info("Manifes data tarif fiskal perpajakan nasional sukses dimuat.")
    except Exception as exc:
        logger.warning("Gagal sinkronisasi tarif pajak eksternal: %s. Mengaktifkan fallback aman.", exc)
        kg.ppn_rate = float(Decimal("0.11"))
        kg.pph_rate = float(Decimal("0.03"))
        kg.tax_rates = {}

    # ---------------------------------------------------------------------------
    # 2. RISK REGISTER & EMV EVALUATION SUBSYSTEM
    # ---------------------------------------------------------------------------
    kg.risk_register = []
    try:
        if os.path.exists(RISK_PATH):
            df_risk = pd.read_excel(RISK_PATH, sheet_name="2. Matriks Risiko & EMV", header=3)
            for _, row in df_risk.iterrows():
                rid = row.get("ID")
                if pd.isna(rid):
                    continue
                rid_str = str(rid).strip()
                if rid_str.upper().startswith("TOTAL"):
                    continue

                prob_raw = row.get("Probabilitas (%)")
                impact_raw = row.get("Dampak (Rp)")
                emv_raw = row.get("Nilai EMV (Rp)")

                if pd.isna(prob_raw) or pd.isna(impact_raw):
                    continue

                prob_dec = _to_decimal(prob_raw, "risk.probability")
                impact_dec = _to_decimal(impact_raw, "risk.impact")

                if pd.notna(emv_raw) and isinstance(emv_raw, (int, float)):
                    emv_dec = _to_decimal(emv_raw, "risk.emv")
                else:
                    # Rumus EMV: Probabilitas (pengali) * Dampak Finansial
                    emv_dec = (prob_dec / Decimal("100.00")) * impact_dec

                risk_payload = {
                    "id": rid_str,
                    "description": str(row.get("Deskripsi Kejadian Risiko / Bahaya", "")).strip(),
                    "probability": float(prob_dec),
                    "impact": float(impact_dec),
                    "emv": float(emv_dec.quantize(Decimal("0.01"))),
                }

                validated_risk = RiskRegisterItemDTO.model_validate(risk_payload)
                kg.risk_register.append(validated_risk.model_dump())
            logger.info("Matriks manajemen risiko terintegrasi: %d entri berhasil dikunci.", len(kg.risk_register))
    except Exception as exc:
        logger.warning("Gagal menguraikan berkas matriks risiko: %s.", exc)
        kg.risk_register = []

    # ---------------------------------------------------------------------------
    # 3. JADWAL DINAMIS & BOBOT KURVA S SUBSYSTEM
    # ---------------------------------------------------------------------------
    kg.schedule_weights = []
    try:
        if os.path.exists(SCHED_PATH):
            df_sched = pd.read_excel(SCHED_PATH, sheet_name="Kurva S & Jadwal Dinamis", header=3)
            total_row = df_sched[df_sched.iloc[:, 1].astype(str).str.contains("TOTAL BIAYA FISIK", na=False)]

            if not total_row.empty:
                row_data = total_row.iloc[0]
                # Ambil bentangan kolom berkala (indeks 7 s.d 19)
                raw_weights = [row_data.iloc[i] for i in range(7, 19)]

                for w in raw_weights:
                    if pd.notna(w) and isinstance(w, (int, float)):
                        kg.schedule_weights.append(float(_to_decimal(w, "curve_s_weight")))
            logger.info("Manifes bobot distribusi kurva S dinamis berhasil dimuat: %d periode aktif.", len(kg.schedule_weights))
    except Exception as exc:
        logger.warning("Gagal ekstraksi data kurva S: %s.", exc)
        kg.schedule_weights = []

    # ---------------------------------------------------------------------------
    # 4. MULTI-TEMPLATE DEFINITIONS STORAGE
    # ---------------------------------------------------------------------------
    kg.template_definitions = {}
    try:
        if os.path.exists(TEMPLATE_PATH):
            xls = pd.ExcelFile(TEMPLATE_PATH)
            for sheet_name in xls.sheet_names:
                df_template = pd.read_excel(TEMPLATE_PATH, sheet_name=sheet_name, header=2)
                kg.template_definitions[str(sheet_name).strip()] = [str(col).strip() for col in df_template.columns]
            logger.info("Koleksi multi-template skema RAB resmi berhasil diamankan: %s", list(kg.template_definitions.keys()))
    except Exception as exc:
        logger.warning("Gagal memuat definisi skema multi-template: %s.", exc)
        kg.template_definitions = {}

    # ---------------------------------------------------------------------------
    # 5. VALUE ENGINEERING & ALTERNATIF SUBSTITUSI BAHAN
    # ---------------------------------------------------------------------------
    kg.alternative_materials = []
    try:
        if os.path.exists(ALT_PATH):
            df_alt = pd.read_excel(ALT_PATH, sheet_name="Alternatif Material")
            for _, row in df_alt.iterrows():
                no_val = row.get("No")
                if pd.isna(no_val):
                    continue

                kategori = str(row.get("Kategori", "")).strip()
                merek_asli = str(row.get("Merek Asli", "")).strip()
                tipe_asli = str(row.get("Tipe/Grade Asli", "")).strip()
                spesifikasi = str(row.get("Spesifikasi", "")).strip()
                merek_alt = str(row.get("Merek Alternatif", "")).strip()
                tipe_alt = str(row.get("Tipe/Grade Alternatif", "")).strip()

                try:
                    harga_asli_raw = row.get("Harga Asli (Rp)")
                    harga_alt_raw = row.get("Harga Alternatif (Rp)")
                    status_str = str(row.get("Status Rekomendasi", "")).strip()

                    if pd.isna(harga_asli_raw) or pd.isna(harga_alt_raw):
                        continue

                    # Normalisasi nilai harga dari Excel: hapus semua karakter non-digit/non-titik/non-minus
                    def _normalize_price(raw: Any) -> Decimal:
                        if isinstance(raw, Decimal):
                            return raw
                        if isinstance(raw, (int, float)):
                            return Decimal(str(raw))
                        if isinstance(raw, str):
                            cleaned = re.sub(r"[^0-9\.\-]", "", raw.replace(",", "."))
                            if not cleaned:
                                raise ValueError("Harga kosong")
                            return Decimal(cleaned)
                        raise TypeError(f"Tipe harga tidak didukung: {type(raw)}")

                    price_orig_dec = _normalize_price(harga_asli_raw)
                    price_alt_dec = _normalize_price(harga_alt_raw)

                    original_id = f"mat-{_slugify(kategori)}-{_slugify(merek_asli)}-{_slugify(tipe_asli)}-{_slugify(spesifikasi)}"[:120]
                    alternative_id = f"mat-{_slugify(kategori)}-{_slugify(merek_alt)}-{_slugify(tipe_alt)}-{_slugify(spesifikasi)}"[:120]

                    alt_payload = {
                        "original_id": original_id,
                        "alternative_id": alternative_id,
                        "original_price": float(price_orig_dec),
                        "alternative_price": float(price_alt_dec),
                        "status": status_str,
                    }

                    validated_alt = AlternativeMaterialDTO.model_validate(alt_payload)
                    kg.alternative_materials.append(validated_alt.model_dump())
                except Exception as row_exc:
                    logger.warning("Baris alternatif material dilewati: %s", row_exc)
                    continue
            logger.info("Database relasi substitusi bahan sukses dikunci: %d matriks rekomendasi.", len(kg.alternative_materials))
    except Exception as exc:
        logger.warning("Gagal mengolah repositori material alternatif: %s.", exc)
        kg.alternative_materials = []

    return kg

# Alias untuk kompatibilitas impor test
integrasi_aces500 = integrate_aces500
