"""Domain Work Item: Pasar Tradisional / Modern"""
def load_wi_pasar(kg):
    from fastra_core.knowledge.nodes import WorkItemNode
    items = [
        ("wi-kios-modular", "PAS.001", "Pembangunan Kios Modular Beton / Baja Ringan", "unit", "Standar Pasar", "PASAR"),
        ("wi-rolling-door-kios", "PAS.002", "Pemasangan Rolling Door Kios Pasar (Kecil) 2m", "unit", "Standar Pasar", "PASAR"),
        ("wi-kwh-per-kios", "PAS.003", "Instalasi Listrik & KWH Meter Individual Per Kios", "unit", "Standar Pasar", "PASAR"),
        ("wi-air-bersih-per-kios", "PAS.004", "Instalasi Pipa Air Bersih & Kran Per Kios (Pasar Basah)", "unit", "Standar Pasar", "PASAR"),
        ("wi-center-drain", "PAS.005", "Pembangunan Saluran Drainase Tengah Pasar (Center Drain) + Grill Besi", "m'", "Standar Pasar", "PASAR"),
        ("wi-compactor-house", "PAS.006", "Pembangunan Tempat Pembuangan Sampah Terpusat (Compactor House)", "unit", "Standar Pasar", "PASAR"),
        ("wi-bongkar-muat", "PAS.007", "Pembangunan Area Bongkar Muat & Parkir Gerobak", "m²", "Standar Pasar", "PASAR"),
        ("wi-smoke-extractor", "PAS.008", "Pemasangan Sistem Exhaust/Blower Penghisap Asap Daging (Smoke Extractor)", "unit", "Standar Pasar", "PASAR"),
        ("wi-lantai-anti-slip-pasar", "PAS.009", "Pemasangan Lantai Anti-Slip Tekstur Kasar Lorong Pasar", "m²", "Standar Pasar", "PASAR"),
        ("wi-toilet-umum-pasar", "PAS.010", "Pemasangan Toilet Umum Pasar Kapasitas Besar (Kloset Jongkok, Wastafel, Floor Drain)", "unit", "Standar Pasar", "PASAR"),
    ]
    for args in items:
        kg.add_work_item(WorkItemNode(*args))
    print(f"  Pasar: {len(items)} item pekerjaan dimuat")