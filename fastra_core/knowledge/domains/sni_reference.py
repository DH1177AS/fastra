# fastra_core\knowledge\domains\sni_reference.py

from __future__ import annotations

import enum
import logging
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("fastra.knowledge.sni_reference")


class SNIDocumentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    WITHDRAWN = "WITHDRAWN"


# ---------------------------------------------------------------------------
# Inbound & Outbound DTOs – Pydantic Strict Gateway (Fail-Fast)
# ---------------------------------------------------------------------------
class SNIItemQueryDTO(BaseModel):
   
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    work_item_name: str = Field(
        ..., min_length=2, max_length=128, pattern=r"^[A-Za-z0-9_\-\.\s\(\)\,\/:]+$"
    )


class SNICoeffValidationQueryDTO(BaseModel):
   
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    work_item_name: str = Field(
        ..., min_length=2, max_length=128, pattern=r"^[A-Za-z0-9_\-\.\s\(\)\,\/:]+$"
    )
    material_name: str = Field(
        ..., min_length=2, max_length=128, pattern=r"^[A-Za-z0-9_\-\.\s\(\)\,\/]+$"
    )
    coefficient: float = Field(..., gt=0.0, le=100000.0, allow_inf_nan=False)


class SNIAuditReportDTO(BaseModel):
   
    model_config = ConfigDict(extra="forbid", strict=True)

    valid: Optional[bool] = Field(default=None)
    sni: Optional[str] = Field(default=None, min_length=5, max_length=32)
    expected: Optional[float] = Field(default=None, gt=0.0)
    actual: Optional[float] = Field(default=None, gt=0.0)
    deviation_pct: Optional[float] = Field(default=None, ge=0.0)
    message: Optional[str] = Field(default=None, max_length=256)


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
        raise ValueError(f"Field '{field_name}' gagal dikonversi ke representasi Decimal imutabel.") from exc


# ---------------------------------------------------------------------------
# Immutable Master National SNI Database Repository
# ---------------------------------------------------------------------------
SNI_DATABASE: Dict[str, Dict[str, Any]] = {
    "SNI 6897:2008": {
        "title": "Tata cara perhitungan harga satuan pekerjaan dinding",
        "publisher": "Badan Standardisasi Nasional (BSN)",
        "year": 2008,
        "status": SNIDocumentStatus.ACTIVE,
        "items_covered": ["Pasangan Bata Merah", "Plesteran", "Acian", "Pasangan Bata Ringan"],
        "key_coefficients": {
            "Pasangan Bata Merah 1:4 (per m2)": {
                "materials": [
                    {"name": "Bata Merah", "coefficient": 70.0, "unit": "buah", "waste": 1.05},
                    {"name": "Semen Portland", "coefficient": 9.0, "unit": "kg", "waste": 1.02},
                    {"name": "Pasir Pasang", "coefficient": 0.02, "unit": "m3", "waste": 1.05},
                ],
                "labor": [
                    {"name": "Pekerja", "coefficient": 0.3, "unit": "OH"},
                    {"name": "Tukang Batu", "coefficient": 0.1, "unit": "OH"},
                    {"name": "Kepala Tukang", "coefficient": 0.01, "unit": "OH"},
                    {"name": "Mandor", "coefficient": 0.015, "unit": "OH"},
                ],
            }
        },
    },
    "SNI 7394:2008": {
        "title": "Tata cara perhitungan harga satuan pekerjaan beton",
        "publisher": "BSN",
        "year": 2008,
        "status": SNIDocumentStatus.ACTIVE,
        "items_covered": ["Bekisting", "Pembesian", "Pengecoran"],
        "key_coefficients": {
            "Beton K-225 Ready Mix (per m3)": {
                "materials": [
                    {"name": "Semen Portland", "coefficient": 371.0, "unit": "kg", "waste": 1.02},
                    {"name": "Pasir Beton", "coefficient": 698.0, "unit": "kg", "waste": 1.05},
                    {"name": "Split", "coefficient": 1047.0, "unit": "kg", "waste": 1.05},
                ],
                "labor": [
                    {"name": "Pekerja", "coefficient": 1.65, "unit": "OH"},
                    {"name": "Tukang Batu", "coefficient": 0.275, "unit": "OH"},
                    {"name": "Kepala Tukang", "coefficient": 0.028, "unit": "OH"},
                    {"name": "Mandor", "coefficient": 0.083, "unit": "OH"},
                ],
            }
        },
    },
    "SNI 7395:2008": {
        "title": "Tata cara perhitungan harga satuan pekerjaan penutup lantai dan dinding",
        "publisher": "BSN",
        "year": 2008,
        "status": SNIDocumentStatus.ACTIVE,
        "items_covered": ["Keramik Lantai", "Granit Lantai"],
    },
    "SNI 2835:2008": {
        "title": "Tata cara perhitungan harga satuan pekerjaan tanah",
        "publisher": "BSN",
        "year": 2008,
        "status": SNIDocumentStatus.ACTIVE,
        "items_covered": ["Galian Tanah", "Urugan Tanah", "Pemadatan"],
    },
    "SNI 2836:2008": {
        "title": "Tata cara perhitungan harga satuan pekerjaan pondasi",
        "publisher": "BSN",
        "year": 2008,
        "status": SNIDocumentStatus.ACTIVE,
        "items_covered": ["Pondasi Batu Kali", "Pondasi Footplate"],
    },
    "SNI 2837:2008": {
        "title": "Tata cara perhitungan harga satuan pekerjaan pengecatan",
        "publisher": "BSN",
        "year": 2008,
        "status": SNIDocumentStatus.ACTIVE,
        "items_covered": ["Cat Tembok", "Cat Kayu", "Cat Besi"],
    },
    "SNI 3434:2008": {
        "title": "Tata cara perhitungan harga satuan pekerjaan kayu",
        "publisher": "BSN",
        "year": 2008,
        "status": SNIDocumentStatus.ACTIVE,
        "items_covered": ["Kusen Kayu", "Pintu Kayu", "Jendela Kayu"],
    },
    "SNI 2839:2008": {
        "title": "Tata cara perhitungan harga satuan pekerjaan plafon",
        "publisher": "BSN",
        "year": 2008,
        "status": SNIDocumentStatus.ACTIVE,
        "items_covered": ["Rangka Plafon", "Penutup Plafon Gypsum"],
    },
    "SNI 2840:2008": {
        "title": "Tata cara perhitungan harga satuan pekerjaan atap",
        "publisher": "BSN",
        "year": 2008,
        "status": SNIDocumentStatus.ACTIVE,
        "items_covered": ["Rangka Atap", "Penutup Genteng"],
    },
    "SNI 7973:2013": {
        "title": "Spesifikasi desain baja ringan untuk bangunan gedung",
        "publisher": "BSN",
        "year": 2013,
        "status": SNIDocumentStatus.ACTIVE,
        "items_covered": ["Rangka Atap Baja Ringan", "Kuda-kuda Baja Ringan"],
    },
}


# ---------------------------------------------------------------------------
# Core National SNI Query & Audit Logic – Pure Verification (QS-Safe)
# ---------------------------------------------------------------------------
def get_sni_for_item(work_item_name: str) -> List[str]:
   
    query_dto = SNIItemQueryDTO(work_item_name=work_item_name)
    cleaned_name = query_dto.work_item_name.lower().strip()

    matching_sni: List[str] = []

    for sni_code, sni_data in SNI_DATABASE.items():
        items_covered = sni_data.get("items_covered", []) or []
        for item in items_covered:
            if str(item).lower().strip() == cleaned_name or cleaned_name in str(item).lower():
                matching_sni.append(sni_code)
                break

    result = sorted(set(matching_sni))
    if not result:
        logger.info("Tidak ada SNI cocok untuk pekerjaan '%s'", work_item_name)
    return result


def validate_coefficient(
    work_item_name: str,
    material_name: str,
    coefficient: float,
) -> Dict[str, Any]:
    
    query_dto = SNICoeffValidationQueryDTO(
        work_item_name=work_item_name,
        material_name=material_name,
        coefficient=coefficient,
    )

    cleaned_wi = query_dto.work_item_name.lower().strip()
    cleaned_mat = query_dto.material_name.lower().strip()
    coef_input_dec = _to_decimal(query_dto.coefficient, "coefficient")
   
    for sni_code, sni_data in SNI_DATABASE.items():
        key_coefficients = sni_data.get("key_coefficients", {}) or {}

        for item_name, item_data in key_coefficients.items():
           
            if cleaned_wi not in item_name.lower():
                continue

            materials_list = item_data.get("materials", []) or []
            for mat in materials_list:
                if cleaned_mat not in mat.get("name", "").lower():
                    continue

                expected_dec = _to_decimal(mat["coefficient"], "sni_expected_coefficient")
               
                deviation_dec = abs(coef_input_dec - expected_dec) / expected_dec
                deviation_pct_dec = deviation_dec * Decimal("100.00")
                is_valid_range = deviation_dec <= Decimal("0.10")

                report_payload = {
                    "valid": is_valid_range,
                    "sni": sni_code,
                    "expected": float(expected_dec),
                    "actual": float(coef_input_dec),
                    "deviation_pct": float(deviation_pct_dec.quantize(Decimal("0.01"))),
                    "message": (
                        "Koefisien memenuhi ambang batas toleransi juknis SNI resmi."
                        if is_valid_range
                        else "Koefisien melanggar ambang batas toleransi SNI nasional (> 10%)."
                    ),
                }

                validated_report = SNIAuditReportDTO.model_validate(report_payload)
                return validated_report.model_dump(exclude_none=True)
   
    logger.info(
        "Tidak ditemukan standar SNI untuk pekerjaan '%s' material '%s'",
        work_item_name,
        material_name,
    )
    fallback_payload = {
        "valid": None,
        "message": "Audit dihentikan: Tidak ditemukan basis data kecocokan standar juknis SNI nasional.",
    }
    validated_fallback = SNIAuditReportDTO.model_validate(fallback_payload)
    return validated_fallback.model_dump(exclude_none=True)