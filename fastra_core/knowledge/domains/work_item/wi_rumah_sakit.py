"""Domain Work Item: Rumah Sakit & Puskesmas"""
def load_wi_rumah_sakit(kg):
    from fastra_core.knowledge.nodes import WorkItemNode
    items = [
        ("wi-gas-medis-oksigen", "RS.001", "Instalasi Pipa Gas Medis (Oksigen Sentral) Tembaga Bebas Minyak", "m'", "Standar Kemenkes", "RUMAH_SAKIT"),
        ("wi-suction-central", "RS.002", "Instalasi Pipa Vakum Medis (Suction Central) Ruang Operasi", "m'", "Standar Kemenkes", "RUMAH_SAKIT"),
        ("wi-bed-head-unit", "RS.003", "Instalasi Outlet Gas Medis Bed Head Unit (OHU) Panel Ranjang", "unit", "Standar Kemenkes", "RUMAH_SAKIT"),
        ("wi-nurse-call", "RS.004", "Instalasi Nurse Call System (Tombol Panggil Perawat) Ruang Rawat", "unit", "Standar Kemenkes", "RUMAH_SAKIT"),
        ("wi-surgical-light", "RS.005", "Pemasangan Lampu Operasi (Surgical Light) Ceiling Mount", "unit", "Standar Kemenkes", "RUMAH_SAKIT"),
        ("wi-laminar-air-flow", "RS.006", "Pemasangan Panel Laminar Air Flow (LAF) HEPA Filter Kamar Operasi", "unit", "Standar Kemenkes", "RUMAH_SAKIT"),
        ("wi-hermetic-door", "RS.007", "Pemasangan Pintu Hermetic Otomatis Kamar Operasi Stainless Steel Sensor", "unit", "Standar Kemenkes", "RUMAH_SAKIT"),
        ("wi-gas-nitrogen-co2", "RS.008", "Instalasi Sistem Gas Nitrogen / CO2 Ruang Operasi Laparoskopi", "unit", "Standar Kemenkes", "RUMAH_SAKIT"),
        ("wi-holding-tank-infeksius", "RS.009", "Instalasi Pipa Pembuangan Air Limbah Infeksius (Holding Tank) Medis", "m'", "Standar Kemenkes", "RUMAH_SAKIT"),
        ("wi-ipal-medis", "RS.010", "Pembangunan Instalasi Pengolahan Air Limbah (IPAL) Medis Aerasi Klorinasi", "unit", "Standar Kemenkes", "RUMAH_SAKIT"),
        ("wi-incinerator", "RS.011", "Instalasi Incinerator / Mesin Pembakar Limbah Padat Medis (B3)", "unit", "Standar Kemenkes", "RUMAH_SAKIT"),
        ("wi-steam-cssd", "RS.012", "Instalasi Pipa Uap Panas (Steam) Sentral Sterilisasi (CSSD) Boiler", "m'", "Standar Kemenkes", "RUMAH_SAKIT"),
        ("wi-xray-shielding", "RS.013", "Pemasangan X-Ray Shielding (Timbal) Ruang Radiologi Timah Hitam", "m²", "Standar BAPETEN", "RUMAH_SAKIT"),
        ("wi-essential-power", "RS.014", "Instalasi Sistem Elektrikal Essential Power (Generator Medis) ICU/OK", "unit", "Standar Kemenkes", "RUMAH_SAKIT"),
        ("wi-tekanan-negatif", "RS.015", "Pemasangan Sistem Tata Udara Tekanan Negatif Ruang Isolasi HEPA Filter", "unit", "Standar Kemenkes", "RUMAH_SAKIT"),
    ]
    for args in items:
        kg.add_work_item(WorkItemNode(*args))
    print(f"  Rumah Sakit: {len(items)} item pekerjaan dimuat")