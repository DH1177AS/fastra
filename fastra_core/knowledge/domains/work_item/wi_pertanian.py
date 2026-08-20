"""Domain Work Item: Bangunan Pertanian & Peternakan"""
def load_wi_pertanian(kg):
    from fastra_core.knowledge.nodes import WorkItemNode
    items = [
        ("wi-closed-house", "TAN.001", "Pembangunan Kandang Ternak Baja Ringan Sistem Closed House", "m²", "Standar Peternakan", "PERTANIAN"),
        ("wi-slatted-floor", "TAN.002", "Pemasangan Lantai Slat Beton Kandang (Slatted Floor)", "m²", "Standar Peternakan", "PERTANIAN"),
        ("wi-cooling-pad", "TAN.003", "Pemasangan Sistem Ventilasi Kandang (Exhaust Fan + Cooling Pad)", "unit", "Standar Peternakan", "PERTANIAN"),
        ("wi-steel-silo", "TAN.004", "Pemasangan Silo Penyimpanan Pakan Ternak (Steel Silo)", "unit", "Standar Peternakan", "PERTANIAN"),
        ("wi-auto-feeder", "TAN.005", "Pemasangan Tempat Pakan & Minum Otomatis Ternak", "set", "Standar Peternakan", "PERTANIAN"),
        ("wi-bioflok-kolam", "TAN.006", "Pembangunan Kolam Terpal / Beton Bioflok Lele (Intensive Fish Pond)", "m²", "Standar Perikanan", "PERTANIAN"),
        ("wi-paddle-wheel", "TAN.007", "Pemasangan Aerator Kincir Air Kolam Ikan (Paddle Wheel Aerator)", "unit", "Standar Perikanan", "PERTANIAN"),
        ("wi-greenhouse", "TAN.008", "Pembangunan Rumah Kaca / Greenhouse Baja Ringan + UV Plastic", "m²", "Standar Pertanian", "PERTANIAN"),
        ("wi-drip-irrigation", "TAN.009", "Pemasangan Jaringan Irigasi Tetes Greenhouse (Drip Irrigation System)", "m²", "Standar Pertanian", "PERTANIAN"),
        ("wi-cold-storage", "TAN.010", "Pembangunan Ruang Pendingin & Penyimpanan Hasil Panen (Cold Storage)", "unit", "Standar Pertanian", "PERTANIAN"),
    ]
    for args in items:
        kg.add_work_item(WorkItemNode(*args))
    print(f"  Pertanian: {len(items)} item pekerjaan dimuat")