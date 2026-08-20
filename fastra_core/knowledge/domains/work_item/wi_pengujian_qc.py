"""Domain Work Item: Pengujian Teknis & QA/QC - Kelompok XIII"""
def load_wi_pengujian_qc(kg):
    from fastra_core.knowledge.nodes import WorkItemNode
    items = [
        ("wi-slump-test", "QC.001", "Pengujian Kuat Tekan Beton (Slump Test & Compression Test) Lab 28 Hari", "sampel", "SNI 1974", "QAQC"),
        ("wi-tensile-test", "QC.002", "Pengujian Tarik Besi Beton (Tensile Test) Lab", "sampel", "SNI 2052", "QAQC"),
        ("wi-flood-test", "QC.003", "Pengujian Kebocoran Atap (Flood Test Plafon/Dak) Genangan 5cm 2x24 Jam", "unit", "AHSP PUPR", "QAQC"),
        ("wi-megger-test", "QC.004", "Pengujian Tahanan Isolasi Kabel (Megger Test) Sirkuit Listrik", "sirkuit", "PUIL", "QAQC"),
        ("wi-earth-test", "QC.005", "Pengujian Tahanan Tanah (Earth Grounding Test) Earth Tester", "titik", "PUIL", "QAQC"),
        ("wi-nitrogen-test", "QC.006", "Pengujian Tekanan Udara Pipa AC (Nitrogen Leak Test) Deteksi Bocor", "unit", "AHSP PUPR", "QAQC"),
        ("wi-flow-test", "QC.007", "Pengujian Aliran Air Bersih (Flow Test) Debit Keran & Shower", "titik", "SNI Plumbing", "QAQC"),
        ("wi-load-test-lift", "QC.008", "Pengujian Beban Angkat Lift (Load Test Elevator) Beban Pasir/Besi", "unit", "SNI Lift", "QAQC"),
        ("wi-smoke-test", "QC.009", "Pengujian Fungsi Pemadam Kamar (Smoke & Heat Detector Test) Asap Buatan", "unit", "Standar NFPA", "QAQC"),
        ("wi-slo", "QC.010", "Sertifikasi Kelaikan Struktur Kelistrikan (SLO) Inspeksi LIT", "unit", "Peraturan PLN", "QAQC"),
        ("wi-bakteri-test", "QC.011", "Pengujian Bakteriologis Air Bersih (E.Coli Lab) Sampel Air", "sampel", "Standar Kemenkes", "QAQC"),
        ("wi-dft-test", "QC.012", "Pengujian Ketebalan Cat (Dry Film Thickness Test) Alat Ukur Digital", "titik", "SNI Cat", "QAQC"),
        ("wi-heat-soak-test", "QC.013", "Pengujian Kaca Tempered (Heat Soak Test) Minimalkan Pecah Spontan", "unit", "SNI Kaca", "QAQC"),
        ("wi-acoustic-test", "QC.014", "Pengujian Kebisingan Ruangan (Acoustic DB Test) Sound Level Meter", "unit", "Standar Akustik", "QAQC"),
        ("wi-floor-flatness", "QC.015", "Pemeriksaan Kerataan Lantai (Floor Flatness Test) Jidar Laser", "m²", "AHSP PUPR", "QAQC"),
    ]
    for args in items:
        kg.add_work_item(WorkItemNode(*args))
    print(f"  Pengujian QA/QC: {len(items)} item pekerjaan dimuat")