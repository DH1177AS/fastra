"""Domain Work Item: Tambahan untuk Relasi SNI"""
def load_wi_tambahan_relasi(kg):
    from fastra_core.knowledge.nodes import WorkItemNode
    items = [
        ("wi-pasang-partisi-gypsum-double", "DIN.009", "Pasangan Partisi Gypsum Double", "m²", "AHSP PUPR", "DINDING"),
        ("wi-pemadatan", "TAN.005", "Pemadatan Tanah", "m²", "SNI 2835:2008", "TANAH"),
        ("wi-pasang-gorden-blackout", "INT.017", "Pemasangan Gorden Blackout", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi-pasang-railing-tangga-stainless", "INT.018", "Pemasangan Railing Tangga Stainless", "m'", "AHSP PUPR", "INTERIOR"),
        ("wi-carbon-frp", "REN.004", "Perkuatan Carbon FRP", "m²", "SNI 2847:2013", "RENOVASI"),
        ("wi-pasang-karpet-roll", "INT.019", "Pemasangan Karpet Roll", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi-perbaikan-instalasi-air", "REN.016", "Perbaikan Instalasi Air Bocor", "titik", "AHSP PUPR", "RENOVASI"),
        ("wi-besi-polos", "STR.003", "Pembesian dengan Besi Polos", "kg", "SNI 7394:2008", "STRUKTUR"),
        ("wi-pasang-partisi-kantor", "INT.020", "Pemasangan Partisi Kantor", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi-pasang-lantai-vinyl-sheet", "INT.021", "Pemasangan Lantai Vinyl Sheet", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi-pasang-cermin-bevel", "INT.022", "Pemasangan Cermin Bevel", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi-pasang-roller-blind", "INT.023", "Pemasangan Roller Blind", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi-pasang-panel-wpc", "INT.024", "Pemasangan Panel Dinding WPC", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi-pasang-wall-moulding", "INT.025", "Pemasangan Wall Moulding", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi-pasang-fluted-panel", "INT.026", "Pemasangan Fluted Panel", "m²", "AHSP PUPR", "INTERIOR"),
        ("wi-pasang-top-table-kuarsa", "INT.027", "Pemasangan Top Table Kuarsa", "m'", "AHSP PUPR", "INTERIOR"),
        ("wi-pasang-siku-pinggul", "INT.028", "Pemasangan Siku Pinggul Granit", "m'", "AHSP PUPR", "INTERIOR"),
        ("wi-pasang-led-strip-lemari", "INT.029", "Pemasangan LED Strip Lemari", "unit", "AHSP PUPR", "INTERIOR"),
        ("wi-pasang-led-kolong-kabinet", "INT.030", "Pemasangan LED Kolong Kabinet", "m'", "AHSP PUPR", "INTERIOR"),
        ("wi-pasang-rel-laci-undermount", "INT.031", "Pemasangan Rel Laci Undermount", "set", "AHSP PUPR", "INTERIOR"),
        ("wi-pasang-engsel-softclose", "INT.032", "Pemasangan Engsel Soft-Close", "set", "AHSP PUPR", "INTERIOR"),
    ]
    for args in items:
        kg.add_work_item(WorkItemNode(*args))
    print(f"  ✅ Tambahan Relasi: {len(items)} item pekerjaan dimuat")
