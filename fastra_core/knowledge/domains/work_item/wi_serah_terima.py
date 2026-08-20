"""Domain Work Item: Fase Akhir Hukum, Serah Terima & As-Built - Kelompok XV"""
def load_wi_serah_terima(kg):
    from fastra_core.knowledge.nodes import WorkItemNode
    items = [
        ("wi-as-built-drawing", "ST.001", "Pembuatan Gambar Akhir Terpasang (As-Built Drawing) Rekaman Lapangan", "Ls", "UU Jasa Konstruksi", "SERAH_TERIMA"),
        ("wi-om-manual", "ST.002", "Penyusunan Buku Manual Dokumen MEP (Operation & Maintenance Manual)", "Ls", "UU Jasa Konstruksi", "SERAH_TERIMA"),
        ("wi-punch-list", "ST.003", "Pekerjaan Inspeksi Cacat Bersama (Punch List / Defect List) Arsitek-Kontraktor", "Ls", "Kontrak Kerja", "SERAH_TERIMA"),
        ("wi-perbaikan-punch", "ST.004", "Perbaikan Item Punch List (Cat Kurang Rata, Ubin Pecah, Pintu Seret)", "Ls", "Kontrak Kerja", "SERAH_TERIMA"),
        ("wi-fire-clearance", "ST.005", "Inspeksi Dinas Kebakaran (Fire Clearance Approval) Sertifikat Kelaikan", "unit", "Peraturan Damkar", "SERAH_TERIMA"),
        ("wi-slf", "ST.006", "Pengurusan Sertifikat Laik Fungsi (SLF) Pemerintah Daerah", "unit", "UU Bangunan Gedung", "SERAH_TERIMA"),
        ("wi-bast1", "ST.007", "Serah Terima Kunci Pertama (First Handover - BAST 1) Penandatanganan Berita Acara", "unit", "Kontrak Kerja", "SERAH_TERIMA"),
        ("wi-meter-awal", "ST.008", "Pencatatan Angka KWH Meter Pertama (Listrik PLN & Air PDAM) Awal", "unit", "Peraturan PLN/PDAM", "SERAH_TERIMA"),
        ("wi-maintenance-period", "ST.009", "Fase Masa Pemeliharaan (Maintenance Period / Retention) 3-6 Bulan", "Ls", "Kontrak Kerja", "SERAH_TERIMA"),
        ("wi-demobilisasi-total", "ST.010", "Pengosongan Area Proyek (Demobilisasi Total) Bongkar Barak & Pagar", "Ls", "AHSP PUPR", "SERAH_TERIMA"),
        ("wi-bersih-fasum", "ST.011", "Pembersihan Fasilitas Umum Sekitar (Lumpur Jalan & Selokan Warga)", "Ls", "AHSP PUPR", "SERAH_TERIMA"),
        ("wi-turun-papan-proyek", "ST.012", "Pelepasan Papan Nama Proyek & PBG (Tanda Proyek Resmi Ditutup)", "unit", "UU Jasa Konstruksi", "SERAH_TERIMA"),
        ("wi-garansi-material", "ST.013", "Penyerahan Garansi Material Resmi (AC, Pompa, Waterproofing, Genset, Atap)", "Ls", "Kontrak Kerja", "SERAH_TERIMA"),
        ("wi-bast2", "ST.014", "Serah Terima Akhir (Final Handover - BAST 2) Pencairan Retensi 5%", "unit", "Kontrak Kerja", "SERAH_TERIMA"),
        ("wi-audit-akhir", "ST.015", "Audit Finansial Proyek Akhir (Rekonsiliasi RAB + Addendum + Nota)", "Ls", "Kontrak Kerja", "SERAH_TERIMA"),
    ]
    for args in items:
        kg.add_work_item(WorkItemNode(*args))
    print(f"  Serah Terima: {len(items)} item pekerjaan dimuat")