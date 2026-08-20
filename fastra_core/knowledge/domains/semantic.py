# semantic.py - ACES-300 Layer 2: Semantic Layer
# Kamus Sinonim untuk menangani variasi istilah lapangan (§7.4)

SYNONYM_DICTIONARY = {
    # Dinding & Pasangan
    "Pasangan Bata Merah": [
        "Pasangan batu bata", "Tembok bata", "Dinding bata",
        "Pasangan bata", "Pemasangan batu bata"
    ],
    "Bata Ringan": [
        "Hebel", "AAC Block", "Bata putih", "Bata ringan AAC",
        "Lightweight brick"
    ],
    "Plesteran": [
        "Lepa", "Plaster", "Plester", "Plasteran"
    ],
    "Acian": [
        "Semen halus", "Skim coat", "Aci", "Acian halus"
    ],

    # Beton & Struktur
    "Beton Ready Mix": [
        "Beton cor", "Beton jadi", "Ready mix concrete",
        "Beton ready mix", "Concrete ready mix"
    ],
    "Bekisting": [
        "Cetakan", "Formwork", "Mal cor", "Bekisting kayu",
        "Form work"
    ],
    "Ring Balk": [
        "Balok latei", "Balok keliling", "Top beam",
        "Ring balok", "Ring beam"
    ],
    "Sloof": [
        "Balok pondasi", "Tie beam", "Sloof beton",
        "Balok sloof"
    ],
    "Pembesian": [
        "Penulangan", "Rebar", "Pemasangan besi",
        "Pekerjaan besi", "Steel reinforcement"
    ],

    # Atap
    "Rangka Atap Baja Ringan": [
        "Rangka atap galvalum", "Truss atap", "Kuda-kuda baja ringan",
        "Rangka baja ringan"
    ],
    "Genteng Beton": [
        "Genteng beton flat", "Concrete tile", "Genteng semen"
    ],
    "Lisplang": [
        "Lisplank", "Fascia board", "Papan lisplang"
    ],

    # Lantai
    "Keramik Lantai": [
        "Tile lantai", "Ubin keramik", "Keramik",
        "Lantai keramik"
    ],
    "Granit Lantai": [
        "Granite tile", "Lantai granit", "Homogeneous tile"
    ],

    # MEP
    "Instalasi Listrik": [
        "Pemasangan listrik", "Electrical installation",
        "Pekerjaan elektrikal"
    ],
    "Instalasi Plumbing": [
        "Pemasangan pipa", "Plumbing work", "Pekerjaan plumbing",
        "Instalasi pipa"
    ],

    # Umum
    "Pekerja": [
        "Labour", "Buruh", "Kenek", "Helper", "Unskilled worker"
    ],
    "Tukang": [
        "Craftsman", "Skilled worker", "Artisan"
    ],
    "Mandor": [
        "Foreman", "Supervisor lapangan", "Overseer"
    ],
}

def get_standard_term(term: str) -> str:
    """Mengembalikan istilah standar dari sinonim lapangan."""
    term_lower = term.lower().strip()
    for standard, synonyms in SYNONYM_DICTIONARY.items():
        if term_lower in [s.lower() for s in synonyms] or term_lower == standard.lower():
            return standard
    return term

def get_synonyms(standard_term: str) -> list:
    """Mengembalikan daftar sinonim untuk istilah standar."""
    return SYNONYM_DICTIONARY.get(standard_term, [])
