import pandas as pd
import re
import sys
sys.path.insert(0, r"D:\fastra_projects\fastra_core")

def slugify(text):
    text = str(text).lower().strip()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', '-', text)
    return text[:60]

def import_equipment_from_excel(kg):
    """Import alat berat dari Excel ke Knowledge Graph."""
    filepath = r"d:\fastra_projects\Database Equipment.xlsx"
    df = pd.read_excel(filepath, sheet_name="Database Equipment", header=2)
    
    print(f"Jumlah alat di Excel: {len(df)}")
    
    kg.equipments.clear()
    
    count = 0
    for idx, row in df.iterrows():
        try:
            no = row.get('No', None)
            if pd.isna(no):
                continue
            
            nama = str(row.get('Nama Alat Berat Konstruksi', '')).strip()
            kategori = str(row.get('Rumpun Kategori Alat', '')).strip()
            model = str(row.get('Model / Kode Seri Acuan Pabrikan', '')).strip()
            spesifikasi = str(row.get('Spesifikasi & Kapasitas Teknis Lapangan', '')).strip()
            satuan = str(row.get('Jenis Satuan', '')).strip()
            kapasitas = str(row.get('Koefisien Kapasitas Produksi Efektif / Jam Kerja', '')).strip()
            
            tarif = row.get('Tarif Sewa Dasar Jakarta (Rp)', 0)
            if pd.isna(tarif):
                tarif = 0.0
            else:
                tarif = float(tarif)
            
            eq_id = f"eq-{slugify(nama)}-{slugify(model)}"[:100]
            
            from fastra_core.knowledge.nodes import EquipmentNode
            
            kg.add_equipment(EquipmentNode(
                id=eq_id,
                name=f"{nama} - {model}",
                unit=satuan,
                rate_per_day=tarif if satuan in ["Hari", "Jam"] else None,
                rate_per_month=tarif if satuan == "Bulan" else None,
                category=kategori,
                specifications={
                    'model': model,
                    'spesifikasi': spesifikasi,
                    'kapasitas': kapasitas,
                    'kategori': kategori,
                    'sumber': 'Excel Database Equipment'
                }
            ))
            count += 1
        except Exception as e:
            print(f"  Baris {idx}: {str(row.get('Nama Alat Berat Konstruksi', '?'))} - Error: {e}")
    
    print(f"Total equipment baru: {len(kg.equipments)}")
    return count

if __name__ == "__main__":
    from fastra_core.knowledge.graph import KnowledgeGraph
    kg = KnowledgeGraph()
    import_equipment_from_excel(kg)
