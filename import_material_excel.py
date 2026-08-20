import pandas as pd
import os
import re

def slugify(text):
    text = str(text).lower().strip()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', '-', text)
    return text[:60]

def import_materials_from_excel(kg):
    excel_path = r"d:\fastra_projects\Database_Material_Bangunan.xlsx"
    df = pd.read_excel(excel_path, sheet_name="Database Material")
    
    existing_ids = set(kg.materials.keys())
    count = 0
    skipped = 0
    
    for idx, row in df.iterrows():
        merek = str(row.get('Merek / Brand', ''))
        tipe = str(row.get('Tipe / Grade', ''))
        ukuran = str(row.get('Spesifikasi / Ukuran', ''))
        
        kat_slug = slugify(str(row.get('Kategori', '')))
        merek_slug = slugify(merek)
        tipe_slug = slugify(tipe)
        ukuran_slug = slugify(ukuran)
        mat_id = f"mat-{kat_slug}-{merek_slug}-{tipe_slug}-{ukuran_slug}"[:120]
        
        if mat_id in existing_ids:
            skipped += 1
            continue
        
        harga_str = str(row.get('Harga Estimasi (Rp)', '0')).replace('Rp', '').replace('.', '').replace(',', '').strip()
        try:
            harga = float(harga_str)
        except:
            harga = 0.0
        
        from fastra_core.knowledge.nodes import MaterialNode
        kg.add_material(MaterialNode(
            id=mat_id,
            name=f"{merek} {tipe} - {ukuran}",
            unit=row.get('Satuan', ''),
            category=row.get('Kategori', ''),
            specifications={
                'sub_kategori': row.get('Sub Kategori', ''),
                'merek': merek,
                'tipe': tipe,
                'ukuran': ukuran,
                'harga_patokan': harga,
                'sumber': 'Excel Database',
                'catatan': str(row.get('Catatan', ''))
            }
        ))
        count += 1
        
        if count % 1000 == 0:
            print(f"   {count} material terproses...")
    
    print(f"Material baru dari Excel: {count}")
    print(f"Duplikat dilewati: {skipped}")
    return count

if __name__ == "__main__":
    from fastra_core.knowledge.graph import KnowledgeGraph
    kg = KnowledgeGraph()
    import_materials_from_excel(kg)
    print(f"Total material di KG: {len(kg.materials)}")
