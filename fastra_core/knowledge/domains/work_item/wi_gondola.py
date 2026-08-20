"""Domain Work Item: Gondola & Akses Fasad"""
def load_wi_gondola(kg):
    from fastra_core.knowledge.nodes import WorkItemNode
    items = [
        ("wi-rel-gondola-atap", "GON.001", "Pemasangan Rel Gondola Atap Gedung (Permanent Davit Arm System)", "m'", "SNI 03-3985", "GONDOLA"),
        ("wi-mesin-gondola", "GON.002", "Pemasangan Mesin Gondola Elektrik (Traction Hoist)", "unit", "SNI 03-3985", "GONDOLA"),
        ("wi-bracket-gondola", "GON.003", "Pemasangan Bracket Penyangga Gondola Fasad Kaca", "unit", "SNI 03-3985", "GONDOLA"),
        ("wi-keranjang-gondola", "GON.004", "Pemasangan Keranjang Gondola (Suspended Cradle Platform)", "unit", "SNI 03-3985", "GONDOLA"),
        ("wi-safety-rope-gondola", "GON.005", "Pemasangan Sistem Pengaman Gondola Independent Safety Rope", "unit", "SNI 03-3985", "GONDOLA"),
    ]
    for args in items:
        kg.add_work_item(WorkItemNode(*args))
    print(f"  Gondola: {len(items)} item pekerjaan dimuat")