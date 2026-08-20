"""Domain Work Item: Lapangan Terbang / Airside Works"""
def load_wi_lapangan_terbang(kg):
    from fastra_core.knowledge.nodes import WorkItemNode
    items = [
        ("wi-subgrade-landasan", "AP.001", "Galian & Pembentukan Subgrade Landasan Pacu", "m²", "ICAO Annex 14", "LAPANGAN_TERBANG"),
        ("wi-ctb-course", "AP.002", "Penghamparan Lapisan Base Course Cement Treated Base (CTB)", "m³", "ICAO Annex 14", "LAPANGAN_TERBANG"),
        ("wi-rigid-pavement-fs45", "AP.003", "Pengecoran Beton Rigid Pavement Mutu FS 45 / K-400 (Slipform Paver)", "m³", "ICAO Annex 14", "LAPANGAN_TERBANG"),
        ("wi-grooving-landasan", "AP.004", "Pembuatan Alur Grooving Landasan Pacu (Drainase & Cengkeraman Roda)", "m²", "ICAO Annex 14", "LAPANGAN_TERBANG"),
        ("wi-joint-sealant-pu", "AP.005", "Pemasangan Joint Sealant Polyurethane Landasan (Tahan Panas Jet Engine)", "m'", "ICAO Annex 14", "LAPANGAN_TERBANG"),
        ("wi-dowel-bar-epoxy", "AP.006", "Pemasangan Dowel Bar Landasan (Baja Epoxy Coated) Transfer Beban", "batang", "ICAO Annex 14", "LAPANGAN_TERBANG"),
        ("wi-runway-marking", "AP.007", "Pengecatan Marka Landasan Pacu (Runway Threshold Marking) Aviation Grade", "m²", "ICAO Annex 14", "LAPANGAN_TERBANG"),
        ("wi-taxiway-marking", "AP.008", "Pengecatan Marka Taxiway & Holding Position", "m²", "ICAO Annex 14", "LAPANGAN_TERBANG"),
        ("wi-runway-guard-light", "AP.009", "Pemasangan Runway Guard Light (Lampu Pelindung Landasan) Kuning Berkedip", "unit", "ICAO Annex 14", "LAPANGAN_TERBANG"),
        ("wi-papi-system", "AP.010", "Pemasangan Precision Approach Path Indicator (PAPI) Navigasi Pendaratan", "unit", "ICAO Annex 14", "LAPANGAN_TERBANG"),
        ("wi-runway-edge-light", "AP.011", "Pemasangan Lampu Runway Edge Light (Lampu Tepi Landasan) Omni Putih/Kuning", "unit", "ICAO Annex 14", "LAPANGAN_TERBANG"),
        ("wi-taxiway-centerline-light", "AP.012", "Pemasangan Taxiway Centerline Light (Lampu Garis Tengah Taxiway) Inset Hijau", "unit", "ICAO Annex 14", "LAPANGAN_TERBANG"),
        ("wi-wind-cone", "AP.013", "Pemasangan Wind Cone (Alat Penunjuk Arah Angin) Tepi Landasan", "unit", "ICAO Annex 14", "LAPANGAN_TERBANG"),
        ("wi-apron-cor", "AP.014", "Pengecoran Apron Beton Mutu Tinggi (K-400) Parkir Pesawat", "m³", "ICAO Annex 14", "LAPANGAN_TERBANG"),
        ("wi-air-terminal-lightning", "AP.015", "Pemasangan Tiang Penangkal Petir Apron (Air Terminal Lightning Rod)", "unit", "ICAO Annex 14", "LAPANGAN_TERBANG"),
        ("wi-apron-grounding", "AP.016", "Pemasangan Sistem Grounding Apron & Fueling Pit (Pembumian Listrik Statis)", "unit", "ICAO Annex 14", "LAPANGAN_TERBANG"),
        ("wi-jet-blast-deflector", "AP.017", "Pemasangan Jet Blast Deflector Fence (Pagar Penahan Semburan Jet)", "m'", "ICAO Annex 14", "LAPANGAN_TERBANG"),
        ("wi-hydrant-fuel-pit", "AP.018", "Pemasangan Hydrant Fuel Pit System Apron (Saluran Bahan Bakar Bawah Tanah)", "unit", "ICAO Annex 14", "LAPANGAN_TERBANG"),
    ]
    for args in items:
        kg.add_work_item(WorkItemNode(*args))
    print(f"  Lapangan Terbang: {len(items)} item pekerjaan dimuat")