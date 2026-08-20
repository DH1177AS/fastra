import sys, os, uuid
sys.path.insert(0, os.getcwd())
from fastra_core.knowledge.loader import create_fastra_knowledge_graph
from fastra_core.compiler.compiler_pipeline import QuantityCompilerPipeline
from fastra_core.compiler.cost_engine import CostEngine

def create_demo_kg():
    kg = create_fastra_knowledge_graph()
    if not hasattr(kg, 'physical_entities'):
        kg.physical_entities = {}
    if not hasattr(kg, 'relationships'):
        kg.relationships = []
    def ent(id, name, t, **kwargs):
        d = {'id': id, 'name': name, 'type': t, 'uuid': str(uuid.uuid4()),
             'entity_type': None, 'status': None}
        d.update(kwargs)
        return d
    kg.physical_entities['ph-001'] = ent('ph-001','Wall Demo 1','Wall')
    kg.physical_entities['ph-002'] = ent('ph-002','Column Demo 1','Column')
    kg.physical_entities['ph-003'] = ent('ph-003','Beam Demo 1','Beam')
    kg.physical_entities['ph-004'] = ent('ph-004','Slab Demo 1','Slab')
    kg.physical_entities['ph-005'] = ent('ph-005','Foundation Demo 1','Foundation')
    kg.physical_entities['ph-006'] = ent('ph-006','Roof Demo 1','Roof')
    kg.physical_entities['dr-001'] = ent('dr-001','Door Demo 1','Door', width=0.9, height=2.1, door_type='SINGLE', material='Kayu')
    kg.physical_entities['wd-001'] = ent('wd-001','Window Demo 1','Window', width=1.2, height=1.5, window_type='CASEMENT', sill_height=0.9, material='Aluminium')
    # relasi
    kg.relationships.append({"source":"ph-002","target":"ph-003","type":"SUPPORTS"})
    kg.relationships.append({"source":"ph-005","target":"ph-002","type":"SUPPORTS"})
    kg.relationships.append({"source":"ph-001","target":"ph-004","type":"SUPPORTS"})
    kg.relationships.append({"source":"ph-003","target":"ph-004","type":"SUPPORTS"})
    kg.relationships.append({"source":"ph-006","target":"ph-004","type":"SUPPORTS"})
    return kg

def build_ccm(kg):
    # Sama seperti di api_secure
    entities = []
    for pid,p in kg.physical_entities.items():
        t=p["type"]
        if t=="Wall":
            entities.append({"uuid":p["uuid"],"entity_type":"Physical","type":"Wall","name":p.get("name","Wall"),"geometry":{"axis_line":{"points":[{"x":0,"y":0,"z":0},{"x":5,"y":0,"z":0}]},"height":3.5,"thickness":0.15},"construction_type":"BATA_MERAH","openings":[]})
        elif t=="Column":
            entities.append({"uuid":p["uuid"],"entity_type":"Physical","type":"Column","name":p.get("name","Column"),"geometry":{"width":0.3,"depth":0.3,"height":3.5}})
        elif t=="Beam":
            col_uuid = next(ep["uuid"] for ep in kg.physical_entities.values() if ep["type"]=="Column")
            entities.append({"uuid":p["uuid"],"entity_type":"Physical","type":"Beam","name":p.get("name","Beam"),"geometry":{"width":0.25,"depth":0.4,"length":5.0},"start_connection":col_uuid,"end_connection":col_uuid})
        elif t=="Slab":
            entities.append({"uuid":p["uuid"],"entity_type":"Physical","type":"Slab","name":p.get("name","Slab"),"geometry":{"boundary":{"points":[{"x":0,"y":0,"z":0},{"x":5,"y":0,"z":0},{"x":5,"y":4,"z":0},{"x":0,"y":4,"z":0},{"x":0,"y":0,"z":0}]},"thickness":0.12},"supports":["ph-001","ph-003","ph-006"]})
        elif t=="Foundation":
            entities.append({"uuid":p["uuid"],"entity_type":"Physical","type":"Foundation","name":p.get("name","Foundation"),"geometry":{"footprint":{"points":[{"x":0,"y":0,"z":0},{"x":1,"y":0,"z":0},{"x":1,"y":1,"z":0},{"x":0,"y":1,"z":0},{"x":0,"y":0,"z":0}]},"depth":1.0},"foundation_type":"FOOTPLATE"})
        elif t=="Roof":
            entities.append({"uuid":p["uuid"],"entity_type":"Physical","type":"Roof","name":p.get("name","Roof"),"geometry":{"footprint":{"points":[{"x":0,"y":0,"z":0},{"x":5,"y":0,"z":0},{"x":5,"y":4,"z":0},{"x":0,"y":4,"z":0},{"x":0,"y":0,"z":0}]},"slope":30.0}})
    return {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),"entities":entities,"relationships":kg.relationships}

if __name__ == "__main__":
    kg = create_demo_kg()
    ccm = build_ccm(kg)
    pipeline = QuantityCompilerPipeline(kg)
    result = pipeline.compile(ccm, "JAKARTA")
    if result["compilation_status"] != "SUCCESS":
        print("FAILED", result["errors"])
        sys.exit(1)
    print("Total Items:", result["boq"]["total_items"])
    print("Project Total:", result["boq"]["project_total"])
    engine = CostEngine(kg)
    rab = engine.generate_rab(result["boq"], "JAKARTA")
    print("Grand Total:", rab["grand_total"])
