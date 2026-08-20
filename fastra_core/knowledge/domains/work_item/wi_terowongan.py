"""Domain Work Item: Terowongan / Tunnel"""
def load_wi_terowongan(kg):
    from fastra_core.knowledge.nodes import WorkItemNode
    items = [
        ("wi-natm-excavation", "TER.001", "Penggalian Terowongan Metode NATM (Drill & Blast / Roadheader)", "m³", "Standar Terowongan", "TEROWONGAN"),
        ("wi-tbm-excavation", "TER.002", "Penggalian Terowongan Metode TBM (Tunnel Boring Machine)", "m'", "Standar Terowongan", "TEROWONGAN"),
        ("wi-steel-rib", "TER.003", "Pemasangan Penyangga Baja Awal (Steel Rib + Wiremesh)", "kg", "Standar Terowongan", "TEROWONGAN"),
        ("wi-shotcrete", "TER.004", "Penyemprotan Beton Shotcrete Dinding Terowongan", "m³", "Standar Terowongan", "TEROWONGAN"),
        ("wi-rockbolt", "TER.005", "Pemasangan Rockbolt / Angkur Batuan (Rock Reinforcement)", "batang", "Standar Terowongan", "TEROWONGAN"),
        ("wi-tunnel-waterproofing", "TER.006", "Pemasangan Lapisan Waterproofing Membran Terowongan (Tunnel Lining)", "m²", "Standar Terowongan", "TEROWONGAN"),
        ("wi-final-concrete-lining", "TER.007", "Pengecoran Beton Lining Permanen Terowongan (Final Concrete Lining)", "m³", "Standar Terowongan", "TEROWONGAN"),
        ("wi-tunnel-lighting", "TER.008", "Pemasangan Lampu Penerangan Linear Dalam Terowongan (Tunnel Lighting)", "m'", "Standar Terowongan", "TEROWONGAN"),
        ("wi-jet-fan", "TER.009", "Pemasangan Kipas Ventilasi Jet Fan Terowongan (Tunnel Ventilation)", "unit", "Standar Terowongan", "TEROWONGAN"),
        ("wi-tunnel-monitoring", "TER.010", "Pemasangan Panel Kontrol Keamanan Terowongan (Tunnel Safety Monitoring)", "unit", "Standar Terowongan", "TEROWONGAN"),
    ]
    for args in items:
        kg.add_work_item(WorkItemNode(*args))
    print(f"  Terowongan: {len(items)} item pekerjaan dimuat")