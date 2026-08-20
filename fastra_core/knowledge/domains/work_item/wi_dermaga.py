"""Domain Work Item: Dermaga & Pelabuhan"""
def load_wi_dermaga(kg):
    from fastra_core.knowledge.nodes import WorkItemNode
    items = [
        ("wi-pile-driving-dermaga", "DER.001", "Pemancangan Tiang Pancang Baja Dermaga (Marine Pile Driving)", "m'", "Standar Pelabuhan", "DERMAGA"),
        ("wi-quay-deck-cor", "DER.002", "Pengecoran Beton Plat Lantai Dermaga (Quay Deck Concrete)", "m³", "Standar Pelabuhan", "DERMAGA"),
        ("wi-marine-bollard", "DER.003", "Pemasangan Bollard / Penambat Kapal (Marine Bollard)", "unit", "Standar Pelabuhan", "DERMAGA"),
        ("wi-rubber-fender", "DER.004", "Pemasangan Fender Karet Pelindung Dermaga (Rubber Dock Fender)", "unit", "Standar Pelabuhan", "DERMAGA"),
        ("wi-gangway", "DER.005", "Pemasangan Tangga Turun Air / Gangway (Access Gangway)", "unit", "Standar Pelabuhan", "DERMAGA"),
        ("wi-marine-water-supply", "DER.006", "Pemasangan Pipa Air Bersih Dermaga (Marine Water Supply)", "m'", "Standar Pelabuhan", "DERMAGA"),
        ("wi-shore-power", "DER.007", "Pemasangan Panel Listrik Tepi Dermaga (Shore Power Panel)", "unit", "Standar Pelabuhan", "DERMAGA"),
        ("wi-navigation-light", "DER.008", "Pemasangan Lampu Navigasi Tepi Dermaga (Marine Navigation Light)", "unit", "Standar Pelabuhan", "DERMAGA"),
        ("wi-navigation-buoy", "DER.009", "Pemasangan Pelampung Batas Alur Pelabuhan (Navigation Buoy)", "unit", "Standar Pelabuhan", "DERMAGA"),
        ("wi-safety-barrier", "DER.010", "Pemasangan Pagar Pengaman Tepi Dermaga (Safety Barrier)", "m'", "Standar Pelabuhan", "DERMAGA"),
        ("wi-crane-rail-foundation", "DER.011", "Pengecoran Dudukan Crane Pelabuhan (Crane Rail Foundation)", "m³", "Standar Pelabuhan", "DERMAGA"),
        ("wi-underground-drain", "DER.012", "Pemasangan Drainase Bawah Permukaan Dermaga (Underground Drain)", "m'", "Standar Pelabuhan", "DERMAGA"),
    ]
    for args in items:
        kg.add_work_item(WorkItemNode(*args))
    print(f"  Dermaga: {len(items)} item pekerjaan dimuat")