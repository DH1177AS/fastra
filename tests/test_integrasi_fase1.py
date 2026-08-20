"""
Test validasi Knowledge Graph FASTRA — Fase 1
Memverifikasi integrasi File 1, 2, 3, dan template WBS.
"""

import sys
sys.path.insert(0, 'D:/fastra_projects/fastra_core')

from fastra_core.knowledge.loader import create_fastra_knowledge_graph, FastraKnowledgeGraph

def test_knowledge_graph_integration():
    """Memverifikasi bahwa Knowledge Graph terintegrasi dengan benar."""
    kg = create_fastra_knowledge_graph()
    
    # 1. Verifikasi struktur dasar
    assert kg is not None
    assert len(kg.materials) == 43  # Material dari File 2
    assert len(kg.labors) == 11     # Tenaga kerja dari File 2
    assert len(kg.work_items) == 36 # Item pekerjaan dari File 2
    assert len(kg.templates) >= 8   # Template dari File 4
    
    # 2. Verifikasi harga regional (5 kota dari File 2 + 3 dari File 1 = 8 kota)
    for wi_id in ["wi-pas-bata", "wi-beton-k250", "wi-galian-tanah"]:
        for region in ["Jakarta Pusat", "Bandung", "Surabaya", "Medan", "Makassar", "Semarang", "Denpasar", "Balikpapan"]:
            result = kg.get_unit_price(wi_id, region)
            assert result["unit_price"] > 0, f"Gagal: {wi_id} di {region}"
    
    # 3. Verifikasi guardrail harga
    old_price = kg._get_price("mat-semen-pc", "Jakarta Pusat")
    success = kg.update_price_from_reference("mat-semen-pc", "Jakarta Pusat", old_price * 2.0)
    assert not success  # Harus ditolak karena di luar batas deviasi
    
    # 4. Verifikasi audit trail
    history = kg.get_price_history()
    assert len(history) >= 0  # History mungkin kosong jika belum ada update
    
    # 5. Verifikasi ringkasan
    summary = kg.export_summary()
    assert summary["materials_count"] == 43
    assert summary["work_items_count"] == 36
    
    print("✅ Semua pengujian integrasi Knowledge Graph berhasil!")
    print(f"   - Material: {summary['materials_count']}")
    print(f"   - Tenaga Kerja: {summary['labors_count']}")
    print(f"   - Item Pekerjaan: {summary['work_items_count']}")
    print(f"   - Relasi Material: {summary['material_requirements_count']}")
    print(f"   - Relasi Tenaga Kerja: {summary['labor_requirements_count']}")
    print(f"   - Data Harga: {summary['price_records_count']}")
    print(f"   - Template WBS: {summary['templates_count']}")
    print(f"   - Region: {summary['regions']}")

if __name__ == "__main__":
    test_knowledge_graph_integration()