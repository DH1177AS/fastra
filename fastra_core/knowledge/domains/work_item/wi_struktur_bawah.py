"""
Domain Work Item: Pekerjaan Struktur Bawah (Sub-Structure)
Mencakup galian dalam, pondasi, pile cap, sloof, dan proteksi lantai dasar.
"""

def load_wi_struktur_bawah(kg):
    """Load item pekerjaan struktur bawah ke Knowledge Graph."""
    
    from fastra_core.knowledge.nodes import WorkItemNode
    
    items = [
        # Galian & Proteksi
        ("wi-galian-pondasi-spesifik", "SUB.001", "Galian Tanah Pondasi Spesifik (Manual Presisi)", "m³", "SNI 2835:2008", "STRUKTUR_BAWAH"),
        ("wi-sheet-pile", "SUB.002", "Pemasangan Dinding Penahan Tanah (Sheet Pile)", "m²", "AHSP PUPR", "STRUKTUR_BAWAH"),
        ("wi-dewatering-pump", "SUB.003", "Instalasi Sistem Pengeringan (Dewatering Pump)", "unit", "AHSP PUPR", "STRUKTUR_BAWAH"),
        ("wi-soil-improvement", "SUB.004", "Pekerjaan Perbaikan Tanah (Soil Improvement)", "m³", "AHSP PUPR", "STRUKTUR_BAWAH"),
        
        # Pondasi Dalam
        ("wi-pemancangan-spun-pile", "SUB.005", "Pemancangan Tiang Pancang (Mini Pile / Spun Pile)", "m'", "SNI 8460:2017", "STRUKTUR_BAWAH"),
        ("wi-welding-joint-pile", "SUB.006", "Penyambungan Tiang Pancang (Welding Joints)", "titik", "SNI 8460:2017", "STRUKTUR_BAWAH"),
        ("wi-bored-pile-drilling", "SUB.007", "Pengeboran Pondasi Bored Pile", "m'", "SNI 8460:2017", "STRUKTUR_BAWAH"),
        ("wi-slurry-cleaning", "SUB.008", "Pembersihan Lumpur Bore Pile (Slurry Cleaning)", "titik", "SNI 8460:2017", "STRUKTUR_BAWAH"),
        ("wi-bore-pile-rebar-cage", "SUB.009", "Fabrikasi & Penurunan Keranjang Besi Bore Pile", "kg", "SNI 8460:2017", "STRUKTUR_BAWAH"),
        ("wi-bore-pile-tremie", "SUB.010", "Pengecoran Beton Bore Pile Sistem Pipa Tremie", "m³", "SNI 8460:2017", "STRUKTUR_BAWAH"),
        ("wi-pit-test", "SUB.011", "Pengujian Integritas Tiang Pancang (Pile Integrity Test - PIT)", "titik", "ASTM D5882", "STRUKTUR_BAWAH"),
        ("wi-static-load-test", "SUB.012", "Pengujian Beban Statis (Static Load Test)", "titik", "ASTM D1143", "STRUKTUR_BAWAH"),
        
        # Pile Cap & Pondasi Dangkal
        ("wi-pile-chipping", "SUB.013", "Pemotongan Kepala Tiang (Pile Chipping)", "titik", "AHSP PUPR", "STRUKTUR_BAWAH"),
        ("wi-pasir-alas-pondasi", "SUB.014", "Penghamparan Pasir Alas Pondasi (10 cm)", "m³", "AHSP PUPR", "STRUKTUR_BAWAH"),
        ("wi-lean-concrete", "SUB.015", "Pembuatan Lantai Kerja (Lean Concrete K-100)", "m³", "AHSP PUPR", "STRUKTUR_BAWAH"),
        ("wi-aanstanding", "SUB.016", "Pemasangan Pondasi Batu Kosong (Aanstanding)", "m³", "AHSP PUPR", "STRUKTUR_BAWAH"),
        ("wi-pondasi-batu-kali", "SUB.017", "Pemasangan Pondasi Batu Kali Belah 1:4", "m³", "SNI 2836:2008", "STRUKTUR_BAWAH"),
        ("wi-pile-cap-rebar", "SUB.018", "Fabrikasi Tulangan Besi Pile Cap / Footplat", "kg", "SNI 2847:2019", "STRUKTUR_BAWAH"),
        ("wi-pile-cap-bekisting", "SUB.019", "Pemasangan Bekisting Pile Cap / Footplat", "m²", "AHSP PUPR", "STRUKTUR_BAWAH"),
        ("wi-pile-cap-cor", "SUB.020", "Pengecoran Beton Struktur Pondasi (Ready Mix K-250/K-300)", "m³", "SNI 2847:2019", "STRUKTUR_BAWAH"),
        ("wi-bekisting-bongkar-pondasi", "SUB.021", "Pembongkaran Bekisting Pondasi (Setelah 24 Jam)", "m²", "AHSP PUPR", "STRUKTUR_BAWAH"),
    ]
    
    for args in items:
        kg.add_work_item(WorkItemNode(*args))
    
    print(f"  ✅ Struktur Bawah: {len(items)} item pekerjaan dimuat")

