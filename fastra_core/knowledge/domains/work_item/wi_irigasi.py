"""Domain Work Item: Irigasi / Saluran Air - Kelompok XXV"""
def load_wi_irigasi(kg):
    from fastra_core.knowledge.nodes import WorkItemNode
    items = [
        ("wi-levelling-air", "IRG.001", "Survei Elevasi Kemiringan Aliran Air (Levelling Waterflow) Waterpas", "m'", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi-galian-irigasi", "IRG.002", "Galian Tanah Jalur Saluran Irigasi Long Arm Excavator", "m³", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi-rapian-galian-irigasi", "IRG.003", "Pekerjaan Perapian Dinding Galian Tanah Saluran Secara Manual", "m²", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi-tanggul-irigasi", "IRG.004", "Pembuatan Struktur Tanggul Tanah Pembatas Saluran Irigasi", "m³", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi-pasir-alas-irigasi", "IRG.005", "Urugan Pasir Alas Saluran Tebal 10 cm", "m³", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi-lantai-kerja-b0-irigasi", "IRG.006", "Pemasangan Lapisan Lantai Kerja Beton Kurus B0 Dasar Saluran", "m²", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi-cerucuk-bambu", "IRG.007", "Pemasangan Konstruksi Pondasi Cerucuk Bambu (Jika Tanah Saluran Lembek)", "batang", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi-u-ditch-concrete", "IRG.008", "Pemasangan Saluran Beton Pracetak Bentuk U (U-Ditch Concrete) Truck Crane", "m'", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi-nat-u-ditch", "IRG.009", "Pekerjaan Penyambungan Antar Nat U-Ditch Mortar Semen Warna", "m'", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi-cover-u-ditch", "IRG.010", "Pemasangan Plat Beton Penutup Saluran U-Ditch (Cover U-Ditch Floor)", "m'", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi-rcp-buis", "IRG.011", "Pemasangan Saluran Pipa Beton Bulat Pracetak (Buis Beton / RCP)", "m'", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi-concrete-bedding", "IRG.012", "Pekerjaan Cor Beton Selimut Pembungkus Pipa Beton (Concrete Cradle)", "m³", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi-pasangan-batu-kali-irigasi", "IRG.013", "Pemasangan Konstruksi Dinding Saluran Pasangan Batu Kali 1:4", "m³", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi-siar-batu-kali", "IRG.014", "Pekerjaan Plesteran Siar Kepala Pasangan Batu Kali Saluran", "m²", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi-weep-hole", "IRG.015", "Pekerjaan Pembuatan Lubang Sulingan Air Dinding Saluran (Weep Hole PVC)", "titik", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi-geotextile-nonwoven", "IRG.016", "Pemasangan Lapisan Geotextile Non-Woven di Belakang Dinding Pasangan Batu", "m²", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi-urugan-balik-irigasi", "IRG.017", "Urugan Tanah Sela Belakang Dinding Saluran Air Lalu Dipadatkan", "m³", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi-manhole-drain", "IRG.018", "Pembuatan Konstruksi Bak Kontrol Pertemuan Saluran Air (Manhole Drain)", "unit", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi-trash-rack", "IRG.019", "Pemasangan Grill Besi Saringan Sampah Tangkapan Bak Kontrol (Trash Rack)", "unit", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi-sluice-gate", "IRG.020", "Pembuatan Pintu Air Irigasi Kontrol Sistem Angkat Manual (Sluice Gate Steel)", "unit", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi-stilling-basin", "IRG.021", "Pembuatan Konstruksi Bak Pelepas Tekan Aliran Air (Stilling Basin)", "unit", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi-division-box", "IRG.022", "Pembuatan Bangunan Pembagi Aliran Air Irigasi (Division Box Concrete)", "unit", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi-acian-kedap-irigasi", "IRG.023", "Pekerjaan Plesteran Acian Kedap Air Dinding Dalam Bak Pembagi", "m²", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi-cat-waterproofing-irigasi", "IRG.024", "Pelapisan Cat Waterproofing Khusus Kolam/Air pada Dinding Beton Irigasi", "m²", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi-box-culvert", "IRG.025", "Pemasangan Pipa Gorong-Gorong Menembus Bawah Jalan (Box Culvert Precast)", "m'", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi-wing-wall", "IRG.026", "Pengecoran Konstruksi Tembok Sayap Gorong-Gorong (Wing Wall Concrete)", "m³", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi-sludge-dredging", "IRG.027", "Pekerjaan Pengerukan Endapan Lumpur Awal Saluran Eksisting (Sludge Dredging)", "m³", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi-water-commissioning", "IRG.028", "Pengujian Pengaliran Air Sempurna Beban Maksimal Saluran (Water Commissioning)", "Ls", "Spesifikasi Irigasi", "IRIGASI"),
        ("wi-patok-sempadan", "IRG.029", "Pemasangan Patok Batas Tanah Sempadan Saluran Irigasi Pemerintah", "buah", "Spesifikasi Irigasi", "IRIGASI"),
    ]
    for args in items:
        kg.add_work_item(WorkItemNode(*args))
    print(f"  ✅ Irigasi: {len(items)} item pekerjaan dimuat")
