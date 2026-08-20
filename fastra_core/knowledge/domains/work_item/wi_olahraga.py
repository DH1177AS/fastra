"""Domain Work Item: Lapangan Olahraga Outdoor"""
def load_wi_olahraga(kg):
    from fastra_core.knowledge.nodes import WorkItemNode
    items = [
        ("wi-subgrade-olahraga", "OLA.001", "Penggalian & Pembentukan Sub-grade Lapangan Olahraga", "m²", "Standar Olahraga", "OLAHRAGA"),
        ("wi-macadam-drainase", "OLA.002", "Pemasangan Lapisan Drainase Kerikil Bawah Lapangan (Macadam)", "m³", "Standar Olahraga", "OLAHRAGA"),
        ("wi-drainase-lateral", "OLA.003", "Pemasangan Pipa Drainase Lateral Bawah Permukaan Lapangan", "m'", "Standar Olahraga", "OLAHRAGA"),
        ("wi-turf-grass-instan", "OLA.004", "Penghamparan Rumput Alami Sistem Roll/Instan (Turf Grass Instant)", "m²", "Standar Olahraga", "OLAHRAGA"),
        ("wi-rumput-sintetis-fifa", "OLA.005", "Penghamparan Rumput Sintetis Standar FIFA + Rubber Granule", "m²", "Standar Olahraga", "OLAHRAGA"),
        ("wi-ball-catch-net", "OLA.006", "Pemasangan Tiang & Jaring Pengaman Lapangan (Ball Catch Net)", "set", "Standar Olahraga", "OLAHRAGA"),
        ("wi-tiang-ring-basket", "OLA.007", "Pemasangan Tiang Basket Portable/Cor Tanam + Ring Basket", "unit", "Standar Olahraga", "OLAHRAGA"),
        ("wi-tiang-net-voli", "OLA.008", "Pemasangan Tiang Net Voli / Bulutangkis Outdoor + Net", "set", "Standar Olahraga", "OLAHRAGA"),
        ("wi-stadion-mini-lamp", "OLA.009", "Pemasangan Lampu Sorot Stadion Mini Tiang Tinggi (4-6 Tiang)", "unit", "Standar Olahraga", "OLAHRAGA"),
        ("wi-tribun-beton", "OLA.010", "Pembangunan Tribun Penonton Beton Bertingkat + Kanopi Atap", "m²", "Standar Olahraga", "OLAHRAGA"),
    ]
    for args in items:
        kg.add_work_item(WorkItemNode(*args))
    print(f"  Olahraga: {len(items)} item pekerjaan dimuat")