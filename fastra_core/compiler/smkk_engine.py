# fastra_core\compiler\smkk_engine.py

from __future__ import annotations

import enum
import logging
import os
from decimal import Decimal, InvalidOperation
from types import MappingProxyType
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class SMKKRiskLevel(str, enum.Enum):
    KECIL = "KECIL"
    SEDANG = "SEDANG"
    BESAR = "BESAR"

RISK_LEVELS = MappingProxyType({
    "KECIL": 0.5,
    "SEDANG": 1.0,
    "BESAR": 2.0,
})


class SMKKComponentCode(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"
    H = "H"
    I = "I"


class SMKKQSStatus(str, enum.Enum):
    APPROVED = "APPROVED"
    ASSUMED = "ASSUMED"
    NEEDS_QUOTE = "NEEDS_QUOTE"
    NEEDS_QS_DECISION = "NEEDS_QS_DECISION"
    APPROVED_QS_EXTERNAL = "APPROVED_QS_EXTERNAL"
    APPROVED_DENGAN_ASUMSI_PROYEK = "APPROVED_DENGAN_ASUMSI_PROYEK"
    PERLU_KUOTASI_VENDOR = "PERLU_KUOTASI_VENDOR"

SMKK_FILE = r"D:\fastra_projects\SMKK_Calibration.xlsx"

COMPONENT_LABELS: Dict[SMKKComponentCode, str] = MappingProxyType({
    SMKKComponentCode.A: "A. Penyiapan Dokumen Penerapan SMKK",
    SMKKComponentCode.B: "B. Sosialisasi, Promosi, dan Pelatihan",
    SMKKComponentCode.C: "C. Alat Pelindung Kerja dan Alat Pelindung Diri",
    SMKKComponentCode.D: "D. Asuransi (CAR)",
    SMKKComponentCode.E: "E. Personel Keselamatan Konstruksi",
    SMKKComponentCode.F: "F. Fasilitas Sarana, Prasarana, dan Alat Kesehatan",
    SMKKComponentCode.G: "G. Rambu dan Perlengkapan Lalu Lintas",
    SMKKComponentCode.H: "H. Konsultasi dengan Ahli Terkait Keselamatan Konstruksi",
    SMKKComponentCode.I: "I. Kegiatan dan Peralatan Terkait Pengendalian Risiko",
})

DEFAULT_PRICES: Dict[SMKKRiskLevel, Dict[SMKKComponentCode, float]] = MappingProxyType({
    SMKKRiskLevel.KECIL: {
        SMKKComponentCode.A: 3000000.0, SMKKComponentCode.B: 5000000.0, SMKKComponentCode.C: 15000000.0,
        SMKKComponentCode.D: 3000000.0, SMKKComponentCode.E: 5399406.0, SMKKComponentCode.F: 2000000.0,
        SMKKComponentCode.G: 1500000.0, SMKKComponentCode.H: 0.0,       SMKKComponentCode.I: 2000000.0
    },
    SMKKRiskLevel.SEDANG: {
        SMKKComponentCode.A: 6000000.0,  SMKKComponentCode.B: 15000000.0, SMKKComponentCode.C: 45000000.0,
        SMKKComponentCode.D: 7500000.0,  SMKKComponentCode.E: 20798811.0, SMKKComponentCode.F: 5000000.0,
        SMKKComponentCode.G: 4000000.0,  SMKKComponentCode.H: 4000000.0,  SMKKComponentCode.I: 15000000.0
    },
    SMKKRiskLevel.BESAR: {
        SMKKComponentCode.A: 10000000.0, SMKKComponentCode.B: 30000000.0, SMKKComponentCode.C: 80000000.0,
        SMKKComponentCode.D: 20000000.0, SMKKComponentCode.E: 46198220.0, SMKKComponentCode.F: 35000000.0,
        SMKKComponentCode.G: 10000000.0, SMKKComponentCode.H: 18000000.0, SMKKComponentCode.I: 35000000.0
    },
}
)


# ---------------------------------------------------------------------------
# Inbound & Outbound DTOs – Pydantic Strict Gateway (Fail-Fast)
# ---------------------------------------------------------------------------
class SMKKCalculationInputDTO(BaseModel):
   
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    risk_level: SMKKRiskLevel = Field(...)
    contract_value: Optional[float] = Field(default=None, gt=0.0, le=1e15, allow_inf_nan=False)
    worker_count: int = Field(default=25, gt=0, le=50000)
    duration_months: int = Field(default=6, gt=0, le=120)


class SMKKComponentOutputDTO(BaseModel):
  
    model_config = ConfigDict(extra="forbid", strict=True)

    component: str = Field(..., min_length=5, max_length=128)
    amount: float = Field(..., ge=0.0, le=1e14, allow_inf_nan=False)
    status: SMKKQSStatus = Field(...)
    evidence: str = Field(default="", max_length=512)


class SMKKFinalReportDTO(BaseModel):
    
    model_config = ConfigDict(extra="forbid", strict=True)

    risk_level: SMKKRiskLevel = Field(...)
    components: List[SMKKComponentOutputDTO] = Field(..., max_length=9)
    total_smkk: float = Field(..., ge=0.0, le=1e15, allow_inf_nan=False)
    note: str = Field(..., min_length=10, max_length=256)


# ---------------------------------------------------------------------------
# Core Utilities – Jaminan Keamanan Type Casting
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


# ---------------------------------------------------------------------------
# Core Internal Spreadsheet Reader & Calculations
# ---------------------------------------------------------------------------
def _load_excel() -> Optional[Dict[str, Dict[str, Dict[str, Any]]]]:
   
    if not os.path.exists(SMKK_FILE):
        logger.info("File SMKK_Calibration.xlsx tidak ditemukan, gunakan default internal.")
        return None

    try:
        import pandas as pd  # Import opsional di dalam fungsi untuk menghindari kegagalan global
    except ImportError:
        logger.warning("pandas tidak terpasang, fallback ke default internal.")
        return None

    try:
        xl = pd.ExcelFile(SMKK_FILE)
        data: Dict[str, Dict[str, Dict[str, Any]]] = {}

        for risk_enum in SMKKRiskLevel:
            risk_str = risk_enum.value
            if risk_str not in xl.sheet_names:
                continue

            df = pd.read_excel(xl, sheet_name=risk_str, header=0)
            comps: Dict[str, Dict[str, Any]] = {}

            for _, row in df.iterrows():
                komponen_raw = str(row.get("Komponen", "")).strip()
                if not komponen_raw or komponen_raw.upper().startswith("TOTAL"):
                    continue
               
                code_str = komponen_raw.split(".")[0].strip().upper()
                if code_str not in [c.value for c in SMKKComponentCode]:
                    continue

                price_raw = row.get("Harga Satuan (Rp)")
                qty_raw = row.get("Kuantitas")
                total_raw = row.get("Total (Rp)")
               
                price = float(price_raw) if pd.notna(price_raw) and isinstance(price_raw, (int, float)) else 0.0
                qty = float(qty_raw) if pd.notna(qty_raw) and isinstance(qty_raw, (int, float)) else 0.0
                total = float(total_raw) if pd.notna(total_raw) and isinstance(total_raw, (int, float)) else 0.0

                status_raw = str(row.get("QS_Status", "")).strip().upper()
                try:
                    status = SMKKQSStatus(status_raw).value
                except ValueError:
                    status = SMKKQSStatus.NEEDS_QS_DECISION.value

                evidence = str(row.get("Bukti Dukung / Referensi", "")).strip()

                comps[code_str] = {
                    "name": komponen_raw,
                    "quantity": qty,
                    "price": price,
                    "total": total,
                    "status": status,
                    "evidence": evidence,
                }
            data[risk_str] = comps

        return data if data else None
    except Exception as exc:
        logger.warning("Gagal membaca file Excel SMKK: %s", exc)
        return None


def calculate_smkk(
    risk_level: str,
    contract_value: Optional[float] = None,
    worker_count: int = 25,
    duration_months: int = 6,
) -> Dict[str, Any]:
   
    input_dto = SMKKCalculationInputDTO(
        risk_level=SMKKRiskLevel(risk_level.upper()),
        contract_value=contract_value,
        worker_count=worker_count,
        duration_months=duration_months,
    )

    excel_data = _load_excel()
    output_components: List[Dict[str, Any]] = []
    total_smkk_val = Decimal("0.00")
    
    for code_enum, label_str in COMPONENT_LABELS.items():
        code_str = code_enum.value
        total_item_val = Decimal("0.00")
        current_status = SMKKQSStatus.PERLU_KUOTASI_VENDOR
        current_evidence = ""

        if (
            excel_data
            and input_dto.risk_level.value in excel_data
            and code_str in excel_data[input_dto.risk_level.value]
        ):
            item = excel_data[input_dto.risk_level.value][code_str]
            try:
                current_status = SMKKQSStatus(item["status"])
            except ValueError:
                current_status = SMKKQSStatus.PERLU_KUOTASI_VENDOR
            current_evidence = item["evidence"]
           
            if code_enum == SMKKComponentCode.D and input_dto.contract_value is not None:
                rate_decimal = _to_decimal(item["price"], "excel_car_rate")
                contract_decimal = _to_decimal(input_dto.contract_value, "contract_value")
                total_item_val = (contract_decimal * rate_decimal).quantize(Decimal("0.01"))
            else:
                total_item_val = _to_decimal(item["total"], "excel_item_total").quantize(Decimal("0.01"))
        else:
           
            if code_enum == SMKKComponentCode.D:
                if input_dto.contract_value is not None:
                    # Standar PUPR: 0.1% dari nilai konstruksi
                    contract_decimal = _to_decimal(input_dto.contract_value, "contract_value")
                    total_item_val = (contract_decimal * Decimal("0.001")).quantize(Decimal("0.01"))
                else:
                    total_item_val = Decimal("0.00")
            else:
                base_price = DEFAULT_PRICES[input_dto.risk_level][code_enum]
                total_item_val = _to_decimal(base_price, "default_price").quantize(Decimal("0.01"))
       
        component_payload = {
            "component": label_str,
            "amount": float(total_item_val),
            "status": current_status.value,
            "evidence": current_evidence,
        }

        try:
            validated_row = SMKKComponentOutputDTO.model_validate(component_payload)
            output_components.append(validated_row.model_dump())
        except Exception as exc:
            logger.error("Gagal validasi komponen SMKK %s: %s", code_str, exc)
            
            output_components.append({
                "component": label_str,
                "amount": 0.0,
                "status": SMKKQSStatus.PERLU_KUOTASI_VENDOR.value,
                "evidence": current_evidence,
            })

        total_smkk_val += total_item_val
   
    report_payload = {
        "risk_level": input_dto.risk_level,
        "components": output_components,
        "total_smkk": float(total_smkk_val.quantize(Decimal("0.01"))),
        "note": "Data dari SMKK_Calibration.xlsx (jika tersedia). Status APPROVED/ASSUMED/NEEDS_QUOTE harus diperhatikan.",
    }

    try:
        validated_report = SMKKFinalReportDTO.model_validate(report_payload)
        return validated_report.model_dump()
    except Exception as exc:
        logger.error("Gagal validasi laporan akhir SMKK: %s", exc)
        
        return {
            "risk_level": input_dto.risk_level,
            "components": output_components,
            "total_smkk": float(total_smkk_val.quantize(Decimal("0.01"))),
            "note": "Laporan SMKK gagal divalidasi penuh; periksa kembali.",
        }