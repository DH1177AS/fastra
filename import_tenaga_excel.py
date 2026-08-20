import pandas as pd
import re

def slugify(text):
    text = str(text).lower().strip()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', '-', text)
    return text[:60]

def import_tenaga_from_excel(kg):
    """Import 170 tenaga kerja nasional dari Excel, ganti semua data lama."""
    filepath = r"d:\fastra_projects\Database Tenaga Kerja Konstruksi Nasional.xlsx"
    df = pd.read_excel(filepath, sheet_name="Database Tenaga Kerja")
    
    print(f"Jumlah baris di Excel: {len(df)}")
    
    # Kosongkan tenaga kerja lama
    kg.labors.clear()
    
    count = 0
    errors = 0
    
    for idx, row in df.iterrows():
        try:
            nama = str(row['Klasifikasi Tenaga Kerja']).strip()
            bidang = str(row['Rumpun Bidang Pekerjaan']).strip()
            jenis_upah = str(row['Jenis Upah']).strip()
            
            # Bersihkan angka - tangani berbagai format
            bawah = row['Batas Bawah (Rp)']
            atas = row['Batas Atas (Rp)']
            
            # Jika angka sudah numerik
            if isinstance(bawah, (int, float)):
                batas_bawah = float(bawah)
            else:
                batas_bawah = float(str(bawah).replace(',', '').replace('Rp', '').strip())
            
            if isinstance(atas, (int, float)):
                batas_atas = float(atas)
            else:
                batas_atas = float(str(atas).replace(',', '').replace('Rp', '').strip())
            
            # Rata-rata upah
            upah_rata = (batas_bawah + batas_atas) / 2
            
            # Jika Bulanan, konversi ke harian
            if 'Bulan' in jenis_upah:
                upah_rata = upah_rata / 22
            
            # Generate ID
            lab_id = f"lab-{slugify(nama)}"[:80]
            
            from fastra_core.knowledge.nodes import LaborNode
            from fastra_core.primitives.currency import Currency
            
            kg.add_labor(LaborNode(
                id=lab_id,
                name=nama,
                role=bidang,
                daily_rate=Currency.from_float(upah_rata)
            ))
            count += 1
        except Exception as e:
            errors += 1
            if errors <= 3:
                print(f"  Baris {idx+2}: {str(row.get('Klasifikasi Tenaga Kerja', '?'))} - Error: {e}")
    
    print(f"Total tenaga kerja baru: {count}")
    if errors > 0:
        print(f"Gagal: {errors}")
    return count

if __name__ == "__main__":
    from fastra_core.knowledge.graph import KnowledgeGraph
    kg = KnowledgeGraph()
    import_tenaga_from_excel(kg)
