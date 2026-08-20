"""
Benchmark pipeline untuk CCM besar.
Mode default: full (membutuhkan Excel + psutil).
Mode --ci: knowledge graph minimal, tanpa Excel, tanpa psutil.
Hasil benchmark disimpan ke dev_tools/benchmark_results_10k.json
"""
import sys, os, time, json, uuid, random, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastra_core.knowledge.loader import create_fastra_knowledge_graph
from fastra_core.knowledge.graph import KnowledgeGraph
from fastra_core.knowledge.nodes import MaterialNode, LaborNode, WorkItemNode
from fastra_core.knowledge.edges import MaterialRequirement, LaborRequirement
from decimal import Decimal
from fastra_core.primitives.currency import Currency
from fastra_core.compiler.compiler_pipeline import QuantityCompilerPipeline

try:
    import psutil
except ImportError:
    psutil = None


def make_wall(uid, length=5.0, height=3.5, thickness=0.15):
    return {
        "uuid": uid, "entity_type":"Physical", "type":"Wall", "name":"BenchWall",
        "geometry":{"axis_line":{"points":[{"x":0,"y":0,"z":0},{"x":length,"y":0,"z":0}]},
                    "height":height,"thickness":thickness},
        "construction_type":"BATA_MERAH", "openings":[]
    }

def make_column(uid, w=0.3, d=0.3, h=3.5):
    return {"uuid": uid, "entity_type":"Physical", "type":"Column", "name":"BenchCol",
            "geometry":{"width":w,"depth":d,"height":h}}

def make_beam(uid, w=0.25, d=0.4, l=5.0, start=None, end=None):
    return {"uuid": uid, "entity_type":"Physical", "type":"Beam", "name":"BenchBeam",
            "geometry":{"width":w,"depth":d,"length":l},
            "start_connection":start,"end_connection":end}

def make_slab(uid, thickness=0.12):
    pts=[{"x":0,"y":0,"z":0},{"x":5,"y":0,"z":0},{"x":5,"y":4,"z":0},{"x":0,"y":4,"z":0},{"x":0,"y":0,"z":0}]
    return {"uuid": uid, "entity_type":"Physical", "type":"Slab", "name":"BenchSlab",
            "geometry":{"boundary":{"points":pts},"thickness":thickness},
            "supports":["dummy-support"]}

def make_room(uid):
    pts=[{"x":0,"y":0,"z":0},{"x":4,"y":0,"z":0},{"x":4,"y":3,"z":0},{"x":0,"y":3,"z":0},{"x":0,"y":0,"z":0}]
    return {"uuid": uid, "entity_type":"Spatial", "type":"Room", "name":"BenchRoom",
            "room_type":"BEDROOM", "geometry":{"boundary":{"points":pts}}}

def generate_large_ccm(n=10000):
    entities = []
    relationships = []
    for i in range(n):
        uid = str(uuid.uuid4())
        kind = i % 4
        if kind == 0:
            entities.append(make_wall(uid, length=random.uniform(1,20), height=random.uniform(2,5)))
        elif kind == 1:
            col_uid = str(uuid.uuid4())
            beam_uid = str(uuid.uuid4())
            col = make_column(col_uid, w=random.uniform(0.2,0.6), d=random.uniform(0.2,0.6), h=random.uniform(2,5))
            beam = make_beam(beam_uid, l=random.uniform(2,10), start=col_uid, end=col_uid)
            entities.append(col)
            entities.append(beam)
            relationships.append({"source": col_uid, "target": beam_uid, "type":"SUPPORTS"})
        elif kind == 2:
            entities.append(make_slab(uid, thickness=random.uniform(0.1,0.2)))
        else:
            entities.append(make_room(uid))
    return {
        "ccm_version":"1.0.0",
        "project_uuid": str(uuid.uuid4()),
        "entities": entities,
        "relationships": relationships
    }


def create_ci_knowledge_graph():
    """Knowledge graph minimal untuk CI - tanpa Excel."""
    kg = KnowledgeGraph()
    for mid in ["mat-semen", "mat-bata", "mat-beton"]:
        kg.add_material(MaterialNode(id=mid, name=mid, category="Material", unit="kg"))
    for lid in ["lab-tukang", "lab-kuli"]:
        kg.add_labor(LaborNode(id=lid, name=lid, role='Tukang', daily_rate=Currency(Decimal('100000'))))
    kg.add_work_item(WorkItemNode(id="wi-bata-merah-taman", code="DIN.005", name="Bata Merah", unit="m2", category="DINDING"))
    kg.add_work_item(WorkItemNode(id="wi-kolom-cor-lt1", code="STR.029", name="Kolom Cor", unit="m2", category="STRUKTUR"))
    kg.add_material_requirement("wi-bata-merah-taman", MaterialRequirement(material_id="mat-bata", coefficient=1.0))
    kg.add_labor_requirement("wi-bata-merah-taman", LaborRequirement(labor_id="lab-tukang", coefficient=0.5))
    return kg


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ci", action="store_true", help="Jalankan benchmark CI-safe tanpa Excel.")
    args = parser.parse_args()

    random.seed(42)
    if args.ci:
        print("Mode CI: knowledge graph minimal.")
        kg = create_ci_knowledge_graph()
        n = 5000
        ccm = generate_large_ccm(n)
    else:
        print("Memuat knowledge graph full...")
        kg = create_fastra_knowledge_graph()
        print(f"KG: {kg.export_summary()['materials_count']} materials, {kg.export_summary()['work_items_count']} work items")
        n = 10000
        ccm = generate_large_ccm(n)

    print(f"Membangun CCM {n} entitas...")
    pipeline = QuantityCompilerPipeline(kg, generated_at="2026-08-19T00:00:00+00:00")
    t0 = time.perf_counter()
    r = pipeline.compile(ccm, "JAKARTA")
    t1 = time.perf_counter()
    elapsed = t1 - t0

    peak_memory_mb = None
    if not args.ci and psutil is not None:
        process = psutil.Process()
        peak_memory_mb = round(process.memory_info().rss / (1024 * 1024), 2)

    result = {
        "mode": "ci" if args.ci else "full",
        "n_entities": len(ccm["entities"]),
        "n_relationships": len(ccm["relationships"]),
        "compilation_status": r["compilation_status"],
        "total_time_seconds": round(elapsed, 4),
        "peak_memory_mb": peak_memory_mb,
        "warnings_count": len(r.get("warnings", [])),
        "errors_count": len(r.get("errors", [])),
        "boq_total_items": r["boq"]["total_items"] if r["boq"] else 0,
        "boq_project_total": r["boq"]["project_total"] if r["boq"] else 0,
    }
    print(json.dumps(result, indent=2))
    outfile = os.path.join(os.path.dirname(__file__), "benchmark_results_10k.json")
    with open(outfile, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Hasil disimpan ke {outfile}")

if __name__ == "__main__":
    main()
