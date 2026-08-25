# Panduan Audit QS Independen

## Tujuan
Validasi koefisien SNI/AHSP, harga, dan kalkulasi RAB FASTRA.

## Ruang Lingkup
1. Review koefisien 100 item pekerjaan utama
2. Validasi harga material 5 kota
3. Uji perhitungan RAB pada 3 sampel
4. Review traceability

## Langkah
1. Jalankan: `python dev_tools\export_for_qs_audit.py`
2. Kirim file hasil `FASTRA_QS_Audit_Package.xlsx` ke auditor
3. Minta auditor cek sheet:
   - Materials
   - Labor
   - Equipment
   - WorkItems
   - Prices
   - Material_Req
   - Labor_Req
4. Auditor memberikan rekomendasi

## Keamanan
- Kirim melalui NDA
- Jangan commit file hasil export