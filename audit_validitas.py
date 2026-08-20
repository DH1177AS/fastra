import re
import sys
sys.path.insert(0, r'D:\fastra_projects\fastra_core')

# Load semua domain untuk referensi
from fastra_core.knowledge.graph import KnowledgeGraph
from fastra_core.knowledge.domains.work_item import load_all_work_items
from fastra_core.knowledge.domains.material import load_all_materials
from import_material_excel import import_materials_from_excel
from import_tenaga_excel import import_tenaga_from_excel

kg = KnowledgeGraph()
load_all_materials(kg)
import_materials_from_excel(kg)
import_tenaga_from_excel(kg)
load_all_work_items(kg)
from fastra_core.knowledge.domains.work_item.wi_tambahan_relasi import load_wi_tambahan_relasi
from fastra_core.knowledge.domains.work_item.wi_auto_generated import load_wi_auto_generated
load_wi_tambahan_relasi(kg)
load_wi_auto_generated(kg)

valid_wi_ids = set(kg.work_items.keys())
valid_mat_ids = set(kg.materials.keys())
valid_lab_ids = set(kg.labors.keys())

print(f"Domain siap: {len(valid_wi_ids)} WI, {len(valid_mat_ids)} Mat, {len(valid_lab_ids)} Lab")

# Baca file relasi
with open('integrasi_relasi_sni.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Parse semua relasi
mat_pattern = r'mat\("(wi-[^"]+)",\s*"([^"]+)",\s*([\d.]+),\s*([\d.]+),\s*"([^"]+)"\)'
lab_pattern = r'lab\("(wi-[^"]+)",\s*"([^"]+)",\s*([\d.]+),\s*"([^"]+)"\)'

mat_rels = re.findall(mat_pattern, content)
lab_rels = re.findall(lab_pattern, content)

print(f"\nRelasi Material di file: {len(mat_rels)}")
print(f"Relasi Labor di file: {len(lab_rels)}")

# AUDIT 1: Referensi valid
invalid_wi = []
invalid_mat = []
invalid_lab = []
placeholder_count = 0
no_source = []

for wi_id, mat_id, coef, waste, source in mat_rels:
    if wi_id not in valid_wi_ids:
        invalid_wi.append(("material", wi_id, mat_id))
    if mat_id not in valid_mat_ids:
        invalid_mat.append((wi_id, mat_id))
    if float(coef) <= 0.001:
        placeholder_count += 1
    if not source or source.strip() == "":
        no_source.append(("material", wi_id, mat_id))

for wi_id, lab_id, coef, source in lab_rels:
    if wi_id not in valid_wi_ids:
        invalid_wi.append(("labor", wi_id, lab_id))
    if lab_id not in valid_lab_ids:
        invalid_lab.append((wi_id, lab_id))
    if float(coef) <= 0.001:
        placeholder_count += 1
    if not source or source.strip() == "":
        no_source.append(("labor", wi_id, lab_id))

# Hasil
print("\n" + "="*60)
print("AUDIT VALIDITAS RELASI")
print("="*60)

print(f"\n1. REFERENSI TIDAK VALID:")
print(f"   WorkItem tidak dikenal: {len(invalid_wi)}")
if invalid_wi:
    for tipe, wi, rid in invalid_wi[:5]:
        print(f"     [{tipe}] {wi} -> {rid}")

print(f"   Material tidak dikenal: {len(invalid_mat)}")
if invalid_mat:
    for wi, mat in invalid_mat[:5]:
        print(f"     {wi} -> {mat}")

print(f"   Labor tidak dikenal: {len(invalid_lab)}")
if invalid_lab:
    for wi, lab in invalid_lab[:5]:
        print(f"     {wi} -> {lab}")

print(f"\n2. KOEFISIEN PLACEHOLDER (<=0.001):")
print(f"   Jumlah: {placeholder_count} dari {len(mat_rels) + len(lab_rels)} total relasi")
print(f"   Persentase: {placeholder_count / (len(mat_rels) + len(lab_rels)) * 100:.1f}%")

print(f"\n3. TANPA SUMBER STANDAR:")
print(f"   Jumlah: {len(no_source)}")
if no_source:
    for tipe, wi, rid in no_source[:5]:
        print(f"     [{tipe}] {wi} -> {rid}")

# Skor validitas
total = len(mat_rels) + len(lab_rels)
invalid_total = len(invalid_wi) + len(invalid_mat) + len(invalid_lab)
valid_score = ((total - invalid_total - placeholder_count) / total) * 100
print(f"\n4. SKOR VALIDITAS:")
print(f"   Relasi valid (referensi benar + koefisien wajar): {total - invalid_total - placeholder_count}")
print(f"   Total relasi: {total}")
print(f"   Skor: {valid_score:.1f}%")
print("="*60)
