from fastra_core.knowledge.loader import create_fastra_knowledge_graph
from integrasi_relasi_sni import integrasikan_relasi_sni

kg = create_fastra_knowledge_graph()
integrasikan_relasi_sni(kg)

invalid_material = []
invalid_labor = []
invalid_equipment = []
invalid_work_item = set()

# Periksa material_requirements (dict[work_item_id] -> list[MaterialRequirement])
for wi_id, req_list in kg.material_requirements.items():
    if wi_id not in kg.work_items:
        invalid_work_item.add(wi_id)
    for req in req_list:
        if req.material_id not in kg.materials:
            invalid_material.append((wi_id, req.material_id))

for wi_id, req_list in kg.labor_requirements.items():
    if wi_id not in kg.work_items:
        invalid_work_item.add(wi_id)
    for req in req_list:
        if req.labor_id not in kg.labors:
            invalid_labor.append((wi_id, req.labor_id))

for wi_id, req_list in kg.equipment_requirements.items():
    if wi_id not in kg.work_items:
        invalid_work_item.add(wi_id)
    for req in req_list:
        if req.equipment_id not in kg.equipments:
            invalid_equipment.append((wi_id, req.equipment_id))

total_mat = sum(len(v) for v in kg.material_requirements.values())
total_lab = sum(len(v) for v in kg.labor_requirements.values())
total_eq = sum(len(v) for v in kg.equipment_requirements.values())
total_relasi = total_mat + total_lab + total_eq
total_invalid = len(invalid_material) + len(invalid_labor) + len(invalid_equipment) + len(invalid_work_item)

print("=== AUDIT KONEKTIVITAS RELASI (FINAL) ===")
print(f"Total material_requirements: {total_mat}")
print(f"Total labor_requirements:   {total_lab}")
print(f"Total equipment_requirements: {total_eq}")
print(f"Total relasi: {total_relasi}\n")

if invalid_material:
    print(f"❌ Material ID tidak valid: {len(invalid_material)}")
    for wi, mid in invalid_material[:10]:
        print(f"   Work Item: {wi} -> Material: {mid}")
else:
    print("✅ Semua Material ID valid.")

if invalid_labor:
    print(f"❌ Labor ID tidak valid: {len(invalid_labor)}")
    for wi, lid in invalid_labor[:10]:
        print(f"   Work Item: {wi} -> Labor: {lid}")
else:
    print("✅ Semua Labor ID valid.")

if invalid_equipment:
    print(f"❌ Equipment ID tidak valid: {len(invalid_equipment)}")
    for wi, eid in invalid_equipment[:10]:
        print(f"   Work Item: {wi} -> Equipment: {eid}")
else:
    print("✅ Semua Equipment ID valid.")

if invalid_work_item:
    print(f"❌ Work Item ID tidak dikenal: {len(invalid_work_item)}")
    for wid in list(invalid_work_item)[:10]:
        print(f"   - {wid}")
else:
    print("✅ Semua Work Item ID valid.")

print(f"\nTOTAL ID TIDAK VALID: {total_invalid}")
if total_invalid == 0:
    print("🎉 SEMUA RELASI VALID. Ekspansi bisa dimulai.")
else:
    print("⚠️  Harap perbaiki ID di integrasi_relasi_sni.py sebelum ekspansi.")
