"""Domain Work Item: Gudang & Logistik"""
def load_wi_gudang(kg):
    from fastra_core.knowledge.nodes import WorkItemNode
    items = [
        ("wi-superflat-floor", "GUD.001", "Pengecoran Lantai Beton Heavy Duty (Superflat Floor) FF/FL 50+ Forklift", "m²", "Standar Gudang", "GUDANG"),
        ("wi-armored-joint", "GUD.002", "Pemasangan Sambungan Lantai Gudang (Armored Joint) Pelat Baja Tahan Forklift", "m'", "Standar Gudang", "GUDANG"),
        ("wi-loading-dock", "GUD.003", "Pembangunan Loading Dock / Platform Bongkar Muat 1.2m + Bumper Karet", "unit", "Standar Gudang", "GUDANG"),
        ("wi-rolling-door-besar", "GUD.004", "Pemasangan Pintu Gudang Rolling Door Elektrik Ukuran Besar 5m x 5m + Remote", "unit", "Standar Gudang", "GUDANG"),
        ("wi-dock-leveler", "GUD.005", "Pemasangan Dock Leveler Hidrolik (Jembatan Besi Otomatis Sambung Truk)", "unit", "Standar Gudang", "GUDANG"),
        ("wi-dock-shelter", "GUD.006", "Pemasangan Dock Shelter / Weather Seal (Bantalan Karet Penutup Celah Truk)", "unit", "Standar Gudang", "GUDANG"),
        ("wi-pallet-racking", "GUD.007", "Pemasangan Rak Palet Bertingkat (Heavy Duty Pallet Racking) Struktur Baja", "unit", "Standar Gudang", "GUDANG"),
        ("wi-turbine-ventilator", "GUD.008", "Pemasangan Ventilasi Industri Atap Gudang (Turbine Ventilator) Tanpa Listrik", "unit", "Standar Gudang", "GUDANG"),
        ("wi-exhaust-fan-industri", "GUD.009", "Pemasangan Exhaust Fan Industri Dinding Kapasitas Besar (Minimal 30 inch)", "unit", "Standar Gudang", "GUDANG"),
        ("wi-marka-epoxy-gudang", "GUD.010", "Pengecatan Garis Marka Jalur Forklift & Zona Penyimpanan Gudang (Epoxy)", "m'", "Standar Gudang", "GUDANG"),
    ]
    for args in items:
        kg.add_work_item(WorkItemNode(*args))
    print(f"  Gudang: {len(items)} item pekerjaan dimuat")