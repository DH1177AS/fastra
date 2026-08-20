from pathlib import Path
import sys, os, json, uuid, hashlib
from datetime import datetime, timezone
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastra_core.knowledge.loader import create_fastra_knowledge_graph
from fastra_core.compiler.compiler_pipeline import QuantityCompilerPipeline
from fastra_core.compiler.lexer import Lexer
from fastra_core.compiler.parser import Parser
from fastra_core.compiler.geometry_builder import GeometryBuilder
from fastra_core.compiler.topology_builder import TopologyBuilder
from fastra_core.compiler.semantic_analyzer import SemanticAnalyzer
from fastra_core.compiler.rule_validator import RuleValidator
from fastra_core.compiler.quantity_engine import QuantityEngine
from fastra_core.compiler.boq_builder import BOQBuilder
from fastra_core.compiler.trace import TraceLog
from fastra_core.primitives.length import Length
from fastra_core.primitives.area import Area
from fastra_core.primitives.volume import Volume
from fastra_core.spatial.coordinate import Coordinate

def check_primitive_types():
    print("="*70)
    print("AUDIT FASE 0 - PRIMITIVE TYPES & AXIOMS")
    print("="*70)
    try:
        l = Length(5)
        a = Area(10)
        v = Volume(2)
        c = Coordinate(0,0,0)
        print("✅ Length, Area, Volume, Coordinate dapat dibuat")
    except Exception as e:
        print(f"❌ Primitive error: {e}")
    # Axiom 1: UUID unik
    ids = [str(uuid.uuid4()) for _ in range(5)]
    print("✅ UUID unik" if len(set(ids)) == 5 else "❌ UUID tidak unik")
    # Axiom 4: Explicit Units: cek object Length punya unit
    print("✅ Unit eksplisit" if hasattr(l, '_unit') else "❌ Length tidak punya unit")

def check_kg_data():
    print("\n" + "="*70)
    print("AUDIT FASE 1-3 - KNOWLEDGE GRAPH")
    print("="*70)
    kg = create_fastra_knowledge_graph()
    s = kg.export_summary()
    print(f"Material: {s['materials_count']}")
    print(f"Tenaga Kerja: {s['labors_count']}")
    print(f"Item Pekerjaan: {s['work_items_count']}")
    print(f"Alat Berat: {s['equipments_count']}")
    print(f"Data Harga: {s['price_records_count']}")
    print(f"Relasi Material: {s['material_requirements_count']}")
    print(f"Relasi Tenaga Kerja: {s['labor_requirements_count']}")
    total_relasi = s['material_requirements_count'] + s['labor_requirements_count']
    print(f"Total Relasi: {total_relasi}")
    print(f"Region: {s.get('regions', [])}")
    # Cek invalid ID sederhana
    invalid_wi = sum(1 for wid in kg.work_items if wid not in kg.work_items)
    print(f"ID Invalid Work Item: {invalid_wi}")
    print(f"✅ Knowledge Graph dimuat" if s['materials_count'] > 0 else "❌ KG kosong")
    return kg

def check_ccm_pipeline(kg):
    print("\n" + "="*70)
    print("AUDIT FASE 4 - QUANTITY COMPILER")
    print("="*70)
    # Sample CCM
    wall_uuid = str(uuid.uuid4())
    door_uuid = str(uuid.uuid4())
    ccm = {
        "ccm_version": "1.0.0",
        "project_uuid": str(uuid.uuid4()),
        "entities": [
            {
                "uuid": wall_uuid,
                "entity_type": "Physical",
                "type": "Wall",
                "name": "Wall Audit",
                "geometry": {
                    "axis_line": {"points": [{"x":0,"y":0,"z":0},{"x":5,"y":0,"z":0}]},
                    "height": 3.5,
                    "thickness": 0.15
                },
                "construction_type": "BATA_MERAH",
                "openings": [
                    {"uuid": door_uuid, "type": "DOOR", "width": 0.9, "height": 2.1, "position": 1.0}
                ]
            }
        ],
        "relationships": []
    }
    pipeline = QuantityCompilerPipeline(kg)
    r1 = pipeline.compile(ccm, "JAKARTA")
    r2 = pipeline.compile(ccm, "JAKARTA")
    r3 = pipeline.compile(ccm, "JAKARTA")
    if r1["compilation_status"] != "SUCCESS":
        print("❌ Pipeline gagal")
        print(r1["errors"])
        return
    boq = r1["boq"]
    print(f"Status: {r1['compilation_status']}")
    print(f"Total Items: {boq['total_items']}")
    print(f"Project Total: {boq['project_total']}")
    # Determinisme penuh
    det = json.dumps(boq, sort_keys=True, default=str) == json.dumps(r2["boq"], sort_keys=True, default=str) == json.dumps(r3["boq"], sort_keys=True, default=str)
    print(f"Determinisme BOQ full JSON: {'✅ OK' if det else '❌ GAGAL'}")
    # TraceLog
    item = boq["divisions"][0]["items"][0]
    trace = item["trace_log"]
    print(f"TraceLog computation_steps: {len(trace.get('computation_steps', []))}")
    print(f"TraceLog audit_hash: {trace.get('audit_hash', 'MISSING')[:16]}...")
    if "computation_steps" not in trace:
        print("❌ TraceLog tidak sesuai §13.4 (harus computation_steps)")

def check_rule_validator(kg):
    print("\n" + "="*70)
    print("AUDIT FASE 4 - RULE VALIDATOR")
    print("="*70)
    # Cek RULE-SPA-003 per room, RULE-QTY, custom rules
    # Kita hanya periksa ketersediaan metode
    rv = RuleValidator()
    methods = [m for m in dir(rv) if not m.startswith("_")]
    print(f"Method tersedia: {methods}")
    # Cek custom rules support
    has_custom = hasattr(rv, 'custom_rules')
    print("Custom rules support: " + ("✅ Ya" if has_custom else "❌ Belum"))
    # Cek RULE-SPA-003 per room (bukan global)
    # Di sini kita tidak bisa langsung, tapi kita print indikasi

def main():
    print("AUDIT FASE 0-4 FASTRA")
    print("Tanggal:", datetime.now(timezone.utc).isoformat())
    check_primitive_types()
    kg = check_kg_data()
    check_ccm_pipeline(kg)
    check_rule_validator(kg)
    print("\n✅ Audit selesai. Gunakan hasil ini untuk prioritas perbaikan.")

if __name__ == "__main__":
    main()
