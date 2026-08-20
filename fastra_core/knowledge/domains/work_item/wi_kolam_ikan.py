"""Domain Work Item: Kolam Ikan Koi / Eco-Fish Pond"""
def load_wi_kolam_ikan(kg):
    from fastra_core.knowledge.nodes import WorkItemNode
    items = [
        ("wi-galian-kolam-ikan", "KOL.036", "Galian Tanah Kolam Ikan (Kedalaman 1-1.5m)", "m³", "AHSP PUPR", "KOLAM_IKAN"),
        ("wi-tulangan-kolam-ikan", "KOL.037", "Pemasangan Tulangan Besi Anyam Ganda Kolam Ikan", "kg", "SNI 2847", "KOLAM_IKAN"),
        ("wi-bottom-drain", "KOL.038", "Pemasangan Pipa Saluran Bawah Kolam (Bottom Drain) PVC 3 inci", "titik", "Standar Koi", "KOLAM_IKAN"),
        ("wi-surface-skimmer", "KOL.039", "Pemasangan Pipa Penyedot Permukaan (Surface Skimmer) Kolam", "titik", "Standar Koi", "KOLAM_IKAN"),
        ("wi-multi-chamber", "KOL.040", "Pembuatan Kamar Filter Multi-Chamber (3-4 Sekat) Beton", "unit", "Standar Koi", "KOLAM_IKAN"),
        ("wi-overflow-pipe", "KOL.041", "Pemasangan Pipa Penghubung Antar Chamber (Underflow/Overflow)", "titik", "Standar Koi", "KOLAM_IKAN"),
        ("wi-cor-kolam-ikan", "KOL.042", "Pengecoran Beton Mutu Tinggi Kolam Ikan (Waterproof Admixture)", "m³", "SNI 2847", "KOLAM_IKAN"),
        ("wi-waterproofing-kolam-ikan", "KOL.043", "Pekerjaan Waterproofing Kolam Tipe Cementitious Premium (Aman Ikan)", "m²", "AHSP PUPR", "KOLAM_IKAN"),
        ("wi-plester-kolam-ikan", "KOL.044", "Pekerjaan Plesteran Halus Dinding Dalam Kolam (Corner Rounded)", "m²", "AHSP PUPR", "KOLAM_IKAN"),
        ("wi-waterfall-lip", "KOL.045", "Pembuatan Saluran Air Terjun Dekoratif (Waterfall Lip Stainless)", "unit", "Standar Koi", "KOLAM_IKAN"),
        ("wi-venturi-jet", "KOL.046", "Pemasangan Pipa Pancuran Udara (Venturi Jet System) Bawah Air", "unit", "Standar Koi", "KOLAM_IKAN"),
        ("wi-backwash-drain", "KOL.047", "Instalasi Pipa Pembuangan Lumpur Chamber (Backwash Drain System)", "titik", "Standar Koi", "KOLAM_IKAN"),
        ("wi-brush-filter", "KOL.048", "Pemasangan Media Filter Mekanis (Jaring Nelayan/Brush) Chamber 1", "set", "Standar Koi", "KOLAM_IKAN"),
        ("wi-mat-jepang", "KOL.049", "Pemasangan Media Filter Biologis (Mat Jepang / Batu Gombong) Chamber 2", "set", "Standar Koi", "KOLAM_IKAN"),
        ("wi-zeolit", "KOL.050", "Pemasangan Media Kimiawi (Batu Zeolit / Karbon Aktif) Chamber 3", "set", "Standar Koi", "KOLAM_IKAN"),
        ("wi-uv-sterilizer", "KOL.051", "Instalasi Rumah Lampu UV (Ultraviolet Sterilizer) Chamber Terakhir", "unit", "Standar Koi", "KOLAM_IKAN"),
        ("wi-eco-pump", "KOL.052", "Pemasangan Pompa Celup Sirkulasi Kolam (Submersible Eco Pump)", "unit", "Standar Koi", "KOLAM_IKAN"),
        ("wi-hi-blow-aerator", "KOL.053", "Instalasi Mesin Gelembung Udara (Hi-Blow Aerator Pump) Luar", "unit", "Standar Koi", "KOLAM_IKAN"),
        ("wi-rubber-diffuser", "KOL.054", "Pemasangan Pipa Piringan Aerasi (Rubber Air Diffuser Diaphragm) Dasar Kolam", "unit", "Standar Koi", "KOLAM_IKAN"),
        ("wi-batu-alam-kolam-ikan", "KOL.055", "Pemasangan Batu Alam Pelapis Dinding Kolam (Andesit/Candi) Atas Air", "m²", "AHSP PUPR", "KOLAM_IKAN"),
        ("wi-cat-kolam-ikan", "KOL.056", "Pengecatan Dinding Dalam Kolam Warna Hitam/Hijau Tua (Kontras Ikan)", "m²", "Standar Koi", "KOLAM_IKAN"),
        ("wi-kaca-intip", "KOL.057", "Pemasangan Kaca Intip Samping Kolam (Glass Viewing Window) Tempered 15mm", "unit", "Standar Koi", "KOLAM_IKAN"),
        ("wi-auto-refill", "KOL.058", "Pemasangan Pipa Air Otomatis (Auto Refill Float Valve) Filter", "unit", "Standar Koi", "KOLAM_IKAN"),
        ("wi-rendam-test-ikan", "KOL.059", "Pengujian Kebocoran Kolam 7 Hari (Rendam Penuh)", "unit", "AHSP PUPR", "KOLAM_IKAN"),
        ("wi-netralisasi-kolam-ikan", "KOL.060", "Pekerjaan Netralisasi Semen Beton Kolam (Curing Water Treatment)", "unit", "Standar Koi", "KOLAM_IKAN"),
    ]
    for args in items:
        kg.add_work_item(WorkItemNode(*args))
    print(f"  Kolam Ikan Koi: {len(items)} item pekerjaan dimuat")