from typing import Dict, Any
# sni_reference.py - ACES-300 Layer 5: Regulation Layer
# Database referensi SNI untuk validasi koefisien

SNI_DATABASE: Dict[str, Any] = {
    "SNI 6897:2008": {
        "title": "Tata cara perhitungan harga satuan pekerjaan dinding",
        "publisher": "Badan Standardisasi Nasional (BSN)",
        "year": 2008,
        "status": "ACTIVE",
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
                ]
            }
        }
    },
    "SNI 7394:2008": {
        "title": "Tata cara perhitungan harga satuan pekerjaan beton",
        "publisher": "BSN",
        "year": 2008,
        "status": "ACTIVE",
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
                ]
            }
        }
    },
    "SNI 7395:2008": {
        "title": "Tata cara perhitungan harga satuan pekerjaan penutup lantai dan dinding",
        "publisher": "BSN",
        "year": 2008,
        "status": "ACTIVE",
        "items_covered": ["Keramik Lantai", "Granit Lantai"],
    },
    "SNI 2835:2008": {
        "title": "Tata cara perhitungan harga satuan pekerjaan tanah",
        "publisher": "BSN",
        "year": 2008,
        "status": "ACTIVE",
        "items_covered": ["Galian Tanah", "Urugan Tanah", "Pemadatan"],
    },
    "SNI 2836:2008": {
        "title": "Tata cara perhitungan harga satuan pekerjaan pondasi",
        "publisher": "BSN",
        "year": 2008,
        "status": "ACTIVE",
        "items_covered": ["Pondasi Batu Kali", "Pondasi Footplate"],
    },
    "SNI 2837:2008": {
        "title": "Tata cara perhitungan harga satuan pekerjaan pengecatan",
        "publisher": "BSN",
        "year": 2008,
        "status": "ACTIVE",
        "items_covered": ["Cat Tembok", "Cat Kayu", "Cat Besi"],
    },
    "SNI 3434:2008": {
        "title": "Tata cara perhitungan harga satuan pekerjaan kayu",
        "publisher": "BSN",
        "year": 2008,
        "status": "ACTIVE",
        "items_covered": ["Kusen Kayu", "Pintu Kayu", "Jendela Kayu"],
    },
    "SNI 2839:2008": {
        "title": "Tata cara perhitungan harga satuan pekerjaan plafon",
        "publisher": "BSN",
        "year": 2008,
        "status": "ACTIVE",
        "items_covered": ["Rangka Plafon", "Penutup Plafon Gypsum"],
    },
    "SNI 2840:2008": {
        "title": "Tata cara perhitungan harga satuan pekerjaan atap",
        "publisher": "BSN",
        "year": 2008,
        "status": "ACTIVE",
        "items_covered": ["Rangka Atap", "Penutup Genteng"],
    },
    "SNI 7973:2013": {
        "title": "Spesifikasi desain baja ringan untuk bangunan gedung",
        "publisher": "BSN",
        "year": 2013,
        "status": "ACTIVE",
        "items_covered": ["Rangka Atap Baja Ringan", "Kuda-kuda Baja Ringan"],
    },
}

def get_sni_for_item(work_item_name: str) -> list:
    """Mengembalikan daftar SNI yang relevan untuk suatu item pekerjaan."""
    matching_sni = []
    for sni_code, sni_data in SNI_DATABASE.items():
        for item in sni_data.get("items_covered", []):
            if item.lower() in work_item_name.lower():
                matching_sni.append(sni_code)
    return matching_sni

def validate_coefficient(work_item_name: str, material_name: str, coefficient: float) -> dict:
    """Memvalidasi koefisien material terhadap standar SNI."""
    for sni_code, sni_data in SNI_DATABASE.items():
        for item_name, item_data in sni_data.get("key_coefficients", {}).items():
            if work_item_name.lower() in item_name.lower():
                for mat in item_data.get("materials", []):
                    if material_name.lower() in mat["name"].lower():
                        expected = mat["coefficient"]
                        deviation = abs(coefficient - expected) / expected
                        if deviation <= 0.1:
                            return {"valid": True, "sni": sni_code, "expected": expected, "actual": coefficient}
                        else:
                            return {"valid": False, "sni": sni_code, "expected": expected, "actual": coefficient, "deviation": deviation}
    return {"valid": None, "message": "Tidak ada standar SNI yang cocok"}
