
"""
SMKK Engine ? Biaya Penerapan Sistem Manajemen Keselamatan Konstruksi.
Membaca SMKK_Calibration.xlsx jika tersedia; fallback ke default.
"""
from typing import Any, Dict, List, Optional
import pandas as pd
import os

RISK_LEVELS = ("KECIL", "SEDANG", "BESAR")
SMKK_FILE = r"D:\fastra_projects\SMKK_Calibration.xlsx"

COMPONENT_LABELS = {
    "A": "A. Penyiapan Dokumen Penerapan SMKK",
    "B": "B. Sosialisasi, Promosi, dan Pelatihan",
    "C": "C. Alat Pelindung Kerja dan Alat Pelindung Diri",
    "D": "D. Asuransi (CAR)",
    "E": "E. Personel Keselamatan Konstruksi",
    "F": "F. Fasilitas Sarana, Prasarana, dan Alat Kesehatan",
    "G": "G. Rambu dan Perlengkapan Lalu Lintas",
    "H": "H. Konsultasi dengan Ahli Terkait Keselamatan Konstruksi",
    "I": "I. Kegiatan dan Peralatan Terkait Pengendalian Risiko",
}

DEFAULT_PRICES: Dict[str, Dict[str, float]] = {
    "KECIL": {"A": 3_000_000, "B": 5_000_000, "C": 15_000_000, "D": 3_000_000, "E": 5_399_406,
               "F": 2_000_000, "G": 1_500_000, "H": 0, "I": 2_000_000},
    "SEDANG": {"A": 6_000_000, "B": 15_000_000, "C": 45_000_000, "D": 7_500_000, "E": 20_798_811,
                "F": 5_000_000, "G": 4_000_000, "H": 4_000_000, "I": 15_000_000},
    "BESAR": {"A": 10_000_000, "B": 30_000_000, "C": 80_000_000, "D": 20_000_000, "E": 46_198_220,
               "F": 35_000_000, "G": 10_000_000, "H": 18_000_000, "I": 35_000_000},
}

def _load_excel() -> Optional[Dict[str, Dict[str, Dict[str, Any]]]]:
    """Baca SMKK_Calibration.xlsx, kembalikan dict per risiko."""
    if not os.path.exists(SMKK_FILE):
        return None
    xl = pd.ExcelFile(SMKK_FILE)
    data = {}
    for risk in RISK_LEVELS:
        if risk not in xl.sheet_names:
            continue
        df = pd.read_excel(xl, sheet_name=risk, header=0)
        comps = {}
        for _, row in df.iterrows():
            komponen = str(row.get("Komponen", "")).strip()
            if not komponen or komponen.upper().startswith("TOTAL"):
                continue
            # Ambil kode huruf dari awal string, misal "A. Penyiapan..."
            code = komponen.split(".")[0].strip().upper()
            price = row.get("Harga Satuan (Rp)")
            qty = row.get("Kuantitas")
            total = row.get("Total (Rp)")
            try:
                price = float(price) if pd.notna(price) else 0.0
            except (TypeError, ValueError):
                price = 0.0
            try:
                qty = float(qty) if pd.notna(qty) else 0.0
            except (TypeError, ValueError):
                qty = 0.0
            try:
                total = float(total) if pd.notna(total) else 0.0
            except (TypeError, ValueError):
                total = 0.0

            status = str(row.get("QS_Status", "")).strip()
            bukti = str(row.get("Bukti Dukung / Referensi", "")).strip()

            comps[code] = {
                "name": komponen,
                "quantity": qty,
                "price": price,
                "total": total,
                "status": status,
                "evidence": bukti,
            }
        data[risk] = comps
    return data if data else None


def calculate_smkk(
    risk_level: str,
    contract_value: Optional[float] = None,
    worker_count: int = 25,
    duration_months: int = 6,
) -> Dict[str, Any]:
    """Hitung subtotal SMKK per 9 komponen + total.

    Gunakan file Excel jika tersedia; jika tidak fallback default.
    contract_value dipakai untuk mengganti placeholder pada komponen D (Asuransi CAR).
    """
    if risk_level not in RISK_LEVELS:
        raise ValueError(f"risk_level harus salah satu dari {RISK_LEVELS}")

    excel_data = _load_excel()
    components = []
    total_smkk = 0.0

    for code, label in COMPONENT_LABELS.items():
        price = 0.0
        qty = 0.0
        status = "NEEDS_QS_DECISION"
        evidence = ""

        if excel_data and risk_level in excel_data and code in excel_data[risk_level]:
            item = excel_data[risk_level][code]
            price = item["price"]
            qty = item["quantity"]
            status = item["status"] or "NEEDS_QS_DECISION"
            evidence = item["evidence"]

            # Jika komponen D dan contract_value disediakan, pakai rate ? contract_value
            if code == "D" and contract_value is not None:
                rate = price
                total = round(contract_value * rate, 2)
                qty = contract_value
            else:
                total = item["total"]
        else:
            # Fallback default
            if code == "D":
                # fallback: asumsikan 0.001 * project_value dihitung di CostEngine? di sini pakai contract_value
                if contract_value:
                    total = round(contract_value * 0.001, 2)
                else:
                    total = 0.0
            else:
                price = DEFAULT_PRICES.get(risk_level, {}).get(code, 0.0)
                qty = 1.0
                total = round(price * qty, 2)

        components.append({
            "component": label,
            "amount": round(total, 2),
            "status": status,
            "evidence": evidence,
        })
        total_smkk += total

    return {
        "risk_level": risk_level,
        "components": components,
        "total_smkk": round(total_smkk, 2),
        "note": "Data dari SMKK_Calibration.xlsx (jika tersedia). Status APPROVED/ASSUMED/NEEDS_QUOTE harus diperhatikan.",
    }
