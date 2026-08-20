"""Domain Work Item: Kolam Renang / Swimming Pool - Kelompok XXI"""
def load_wi_kolam_renang(kg):
    from fastra_core.knowledge.nodes import WorkItemNode
    items = [
        ("wi-galian-kolam-renang", "KOL.001", "Pekerjaan Galian Tanah Kolam Renang Skala Besar (Excavator)", "m³", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi-shoring-kolam", "KOL.002", "Pemasangan Dinding Penahan Tanah Darurat (Wooden Shoring) Galian Kolam", "m²", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi-lantai-kerja-b0", "KOL.003", "Pembuatan Lantai Kerja Beton Kurus (B0) Dasar Kolam", "m²", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi-batako-keliling", "KOL.004", "Pemasangan Batako Keliling Badan Kolam (Bekisting Luar Permanen)", "m²", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi-pembesian-layer-bawah", "KOL.005", "Pembesian Kolam Renang - Layer Bawah (D10/D12)", "kg", "SNI 2847", "KOLAM_RENANG"),
        ("wi-cakar-ayam-kolam", "KOL.006", "Pemasangan Besi Cakar Ayam Penyangga Struktur Lantai Kolam", "buah", "SNI 2847", "KOLAM_RENANG"),
        ("wi-pembesian-layer-atas", "KOL.007", "Pembesian Kolam Renang - Layer Atas (Struktur Ganda Tebal 20cm)", "kg", "SNI 2847", "KOLAM_RENANG"),
        ("wi-sparing-maindrain", "KOL.008", "Pemasangan Pipa Sparing Maindrain (Lantai Terdalam Kolam)", "titik", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi-sparing-inlet", "KOL.009", "Pemasangan Pipa Sparing Inlet Fitting (Multi-Titik Dinding Atas)", "titik", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi-sparing-vacuum", "KOL.010", "Pemasangan Pipa Sparing Vacuum Fitting (Colokan Selang Debu)", "titik", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi-overflow-gutter", "KOL.011", "Pembuatan Jalur Selokan Keliling Kolam (Overflow Gutter) Beton", "m'", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi-balancing-tank", "KOL.012", "Pembuatan Kamar Penampungan Air Limpahan (Balancing Tank) Beton", "unit", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi-pump-room", "KOL.013", "Pembuatan Ruang Mesin Kolam (Pump Room) Bawah Tanah Bertangga Besi", "unit", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi-waterstop-pvc", "KOL.014", "Pemasangan Karet Penyumbat Air (Waterstop PVC Strip) Sambungan Cor", "m'", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi-cor-monolitik", "KOL.015", "Pengecoran Monolitik Beton Kolam Renang (K-350/K-400 Waterproof)", "m³", "SNI 2847", "KOLAM_RENANG"),
        ("wi-shotcrete", "KOL.016", "Pekerjaan Semprot Beton Tekan (Shotcrete) Kolam Lengkung (Alternatif)", "m²", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi-bongkar-bekisting-kolam", "KOL.017", "Pekerjaan Pembongkaran Bekisting Dalam Kolam (Setelah 14-21 Hari)", "m²", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi-plester-siku-kolam", "KOL.018", "Pekerjaan Plesteran Akurasi Siku Dinding Kolam (Corner Rounded)", "m²", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi-waterproofing-pu", "KOL.019", "Pekerjaan Waterproofing Kolam Renang Polyurethane (PU) Base 3 Lapis", "m²", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi-hydrotest-pool", "KOL.020", "Pengujian Rendam Air (Hydrotest Pool) 14 Hari Penuh Anti Bocor", "unit", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi-mosaic-tile", "KOL.021", "Pemasangan Ubin Mozaik Kolam Renang (Mosaic Tile 5x5/10x10) Biru Muda", "m²", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi-pool-coping", "KOL.022", "Pemasangan Batu Alam Bibir Kolam (Pool Coping) Andesit/Kerobokan", "m'", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi-epoxy-grout-pool", "KOL.023", "Pekerjaan Pengisian Nat Mozaik Bahan Epoksi (Epoxy Grout) Anti Lumut", "m²", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi-tangga-stainless-pool", "KOL.024", "Pemasangan Tangga Kolam Stainless Steel SUS 316 Anti Karat", "unit", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi-underwater-light-niche", "KOL.025", "Pemasangan Rumah Lampu Kolam Tanam Dinding (Underwater Light Niche)", "unit", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi-led-underwater", "KOL.026", "Pemasangan Lampu LED Kolam Renang LED Underwater (12V) RGB", "unit", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi-transformer-12v", "KOL.027", "Pemasangan Trafo Penurun Tegangan Listrik (Step-down Transformer IP65)", "unit", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi-centrifugal-pump", "KOL.028", "Pemasangan Mesin Pompa Kolam Renang Khusus (Centrifugal Pool Pump)", "unit", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi-sand-filter", "KOL.029", "Pemasangan Tabung Filter Pasir Besar (Sand Filter) Fiberglass", "unit", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi-media-pasir-filter", "KOL.030", "Pengisian Media Pasir Silika / Glass Media ke Tabung Filter", "unit", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi-multiport-valve", "KOL.031", "Pemasangan Katup Kontrol Multiport (Multiport Selector Valve) Filter", "unit", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi-salt-chlorinator", "KOL.032", "Instalasi Sistem Klorinator Garam (Salt Chlorinator Generator) Air Asin", "unit", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi-pool-heat-pump", "KOL.033", "Pemasangan Alat Pemanas Air Kolam (Pool Heat Pump Generator) Hangat", "unit", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi-gutter-grating", "KOL.034", "Pemasangan Kisi-Kisi Tutup Parit (Gutter Overflow Grating) Plastik/ABS", "m'", "AHSP PUPR", "KOLAM_RENANG"),
        ("wi-chemical-shock", "KOL.035", "Pekerjaan Pengisian Air Pertama & Penjernihan Kimiawi (Chemical Shock)", "unit", "AHSP PUPR", "KOLAM_RENANG"),
    ]
    for args in items:
        kg.add_work_item(WorkItemNode(*args))
    print(f"  ✅ Kolam Renang: {len(items)} item pekerjaan dimuat")
