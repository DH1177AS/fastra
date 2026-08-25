"""
Integrasi data eksternal ACES-500:
- Tarif pajak (PPh/PPN)
- Register risiko EMV
- Jadwal kurva S
- Template RAB
"""
import pandas as pd
import logging

logger = logging.getLogger("fastra.knowledge")

def _slugify(text):
    import re
    text = str(text).lower().strip()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', '-', text)
    return text[:60]

def integrasi_aces500(kg):
    # 1. Tarif pajak
    try:
        kg.ppn_rate = 0.12
        kg.pph_rate = 0.0265
        tax_path = "D:/fastra_projects/Kualifikasi_BUJK_dan_Tarif_PPh_Final_Konstruksi.xlsx"
        df_tax = pd.read_excel(tax_path, sheet_name="Tarif PPh Final", header=3)
        kg.tax_rates = {}
        for _, row in df_tax.iterrows():
            kategori = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
            kualifikasi = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
            tarif = row.iloc[3]
            if pd.notna(tarif):
                kg.tax_rates.setdefault(kategori, {})[kualifikasi] = float(tarif)
        logger.info("Data tarif pajak dimuat.")
    except Exception as e:
        logger.warning(f"Gagal muat tarif pajak: {e}")
        kg.ppn_rate = 0.11
        kg.pph_rate = 0.03
        kg.tax_rates = {}

    # 2. Risk register
    try:
        risk_path = "D:/fastra_projects/Matriks_Manajemen_Risiko_Konstruksi_EMV.xlsx"
        df_risk = pd.read_excel(risk_path, sheet_name="2. Matriks Risiko & EMV", header=3)
        kg.risk_register = []
        for _, row in df_risk.iterrows():
            rid = row.get("ID")
            if pd.isna(rid):
                continue
            rid_str = str(rid).strip()
            if rid_str.upper().startswith("TOTAL"):
                continue
            prob = row.get("Probabilitas (%)")
            impact = row.get("Dampak (Rp)")
            emv = row.get("Nilai EMV (Rp)")
            if pd.isna(prob) or pd.isna(impact):
                continue
            kg.risk_register.append({
                "id": rid_str,
                "description": str(row.get("Deskripsi Kejadian Risiko / Bahaya", "")),
                "probability": float(prob),
                "impact": float(impact),
                "emv": float(emv) if pd.notna(emv) else float(prob) * float(impact),
            })
        logger.info(f"Risk register dimuat: {len(kg.risk_register)} risiko.")
    except Exception as e:
        logger.warning(f"Gagal muat risk register: {e}")
        kg.risk_register = []

    # 3. Jadwal kurva S
    try:
        sched_path = "D:/fastra_projects/Sistem_Jadwal_KurvaS_dan_CashFlow.xlsx"
        df_sched = pd.read_excel(sched_path, sheet_name="Kurva S & Jadwal Dinamis", header=3)
        total_row = df_sched[df_sched.iloc[:,1].astype(str).str.contains("TOTAL BIAYA FISIK", na=False)]
        if not total_row.empty:
            row = total_row.iloc[0]
            weights = [row.iloc[i] for i in range(7, 19)]
            kg.schedule_weights = [float(w) for w in weights if pd.notna(w)]
        else:
            kg.schedule_weights = []
        logger.info(f"Schedule weights dimuat: {len(kg.schedule_weights)} periode.")
    except Exception as e:
        logger.warning(f"Gagal muat jadwal: {e}")
        kg.schedule_weights = []

    # 4. Template RAB
    try:
        template_path = "D:/fastra_projects/Multi_Template_RAB_Resmi_Generator.xlsx"
        xls = pd.ExcelFile(template_path)
        kg.template_definitions = {}
        for sheet in xls.sheet_names:
            df = pd.read_excel(template_path, sheet_name=sheet, header=2)
            kg.template_definitions[sheet] = list(df.columns)
        logger.info(f"Template RAB dimuat: {list(kg.template_definitions.keys())}")
    except Exception as e:
        logger.warning(f"Gagal muat template: {e}")
        kg.template_definitions = {}

    # 5. Value Engineering - Alternatif Material
    try:
        alt_path = "D:/fastra_projects/Alternatif_Material_Hemat.xlsx"
        df_alt = pd.read_excel(alt_path, sheet_name="Alternatif Material")
        kg.alternative_materials = []
        for _, row in df_alt.iterrows():
            no = row.get("No")
            if pd.isna(no):
                continue
            kategori = str(row.get("Kategori", ""))
            merek_asli = str(row.get("Merek Asli", ""))
            tipe_asli = str(row.get("Tipe/Grade Asli", ""))
            spesifikasi = str(row.get("Spesifikasi", ""))
            merek_alt = str(row.get("Merek Alternatif", ""))
            tipe_alt = str(row.get("Tipe/Grade Alternatif", ""))
            harga_asli_raw = row.get("Harga Asli (Rp)")
            harga_alt_raw = row.get("Harga Alternatif (Rp)")
            status = str(row.get("Status Rekomendasi", ""))
            if pd.isna(harga_asli_raw) or pd.isna(harga_alt_raw):
                continue
            try:
                harga_asli = float(harga_asli_raw)
                harga_alt = float(harga_alt_raw)
            except (ValueError, TypeError):
                continue

            original_id = f"mat-{_slugify(kategori)}-{_slugify(merek_asli)}-{_slugify(tipe_asli)}-{_slugify(spesifikasi)}"[:120]
            alternative_id = f"mat-{_slugify(kategori)}-{_slugify(merek_alt)}-{_slugify(tipe_alt)}-{_slugify(spesifikasi)}"[:120]
            kg.alternative_materials.append({
                "original_id": original_id,
                "alternative_id": alternative_id,
                "original_price": float(harga_asli),
                "alternative_price": float(harga_alt),
                "status": status,
            })
        logger.info(f"Material alternatif dimuat: {len(kg.alternative_materials)} relasi.")
    except Exception as e:
        logger.warning(f"Gagal muat material alternatif: {e}")
        kg.alternative_materials = []

    return kg
