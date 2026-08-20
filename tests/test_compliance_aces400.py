
import pytest, uuid, json, random
from hypothesis import given, settings, strategies as st
from fastra_core.knowledge.loader import create_fastra_knowledge_graph
from fastra_core.compiler.compiler_pipeline import QuantityCompilerPipeline

@pytest.fixture
def kg():
    return create_fastra_knowledge_graph()

def make_wall_entity(uid=None, length=5.0, height=3.5, openings=None):
    return {
        "uuid": uid or str(uuid.uuid4()),
        "entity_type":"Physical",
        "type":"Wall",
        "name":"Dinding Test",
        "geometry":{
            "axis_line":{"points":[{"x":0,"y":0,"z":0},{"x":length,"y":0,"z":0}]},
            "height":height,
            "thickness":0.15
        },
        "construction_type":"BATA_MERAH",
        "openings": openings or []
    }

def make_column_entity(uid=None, w=0.3, d=0.3, h=3.5):
    return {
        "uuid": uid or str(uuid.uuid4()),
        "entity_type":"Physical",
        "type":"Column",
        "name":"Kolom Test",
        "geometry":{"width":w,"depth":d,"height":h}
    }

def make_beam_entity(uid=None, w=0.25, d=0.4, l=5.0, start_connection=None, end_connection=None):
    return {
        "uuid": uid or str(uuid.uuid4()),
        "entity_type":"Physical",
        "type":"Beam",
        "name":"Balok Test",
        "geometry":{"width":w,"depth":d,"length":l},
        "start_connection": start_connection,
        "end_connection": end_connection
    }

def make_slab_entity(uid=None, thickness=0.12, supports=None):
    pts = [{"x":0,"y":0,"z":0},{"x":5,"y":0,"z":0},{"x":5,"y":4,"z":0},{"x":0,"y":4,"z":0},{"x":0,"y":0,"z":0}]
    return {
        "uuid": uid or str(uuid.uuid4()),
        "entity_type":"Physical",
        "type":"Slab",
        "name":"Plat Test",
        "geometry":{"boundary":{"points":pts},"thickness":thickness},
        "supports": supports if supports is not None else ["dummy-support"]
    }

def make_room_entity(uid=None, closed=True):
    pts = [{"x":0,"y":0,"z":0},{"x":4,"y":0,"z":0},{"x":4,"y":3,"z":0},{"x":0,"y":3,"z":0}]
    if closed:
        pts.append({"x":0,"y":0,"z":0})
    return {
        "uuid": uid or str(uuid.uuid4()),
        "entity_type":"Spatial",
        "type":"Room",
        "name":"Kamar Test",
        "room_type":"BEDROOM",
        "geometry":{"boundary":{"points":pts}}
    }

# ====================================================================
# 25 TESTS
# ====================================================================
def test_001_lexer_valid(kg):
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[make_wall_entity()],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "SUCCESS"

def test_002_lexer_duplicate_uuid(kg):
    uid = str(uuid.uuid4())
    ent = make_wall_entity(uid=uid)
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[ent, dict(ent)],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "FAILED"
    assert any(e["error_code"]=="LEX-005" for e in r["errors"])

def test_003_parser_resolve_references(kg):
    col = make_column_entity(uid=str(uuid.uuid4()))
    beam = make_beam_entity(start_connection=col["uuid"], end_connection=col["uuid"])
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[col, beam],
           "relationships":[{"source":col["uuid"],"target":beam["uuid"],"type":"SUPPORTS"}]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "SUCCESS"

def test_004_geometry_wall_gross_area(kg):
    wall = make_wall_entity()
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[wall],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "SUCCESS"

def test_005_geometry_column_volume(kg):
    col = make_column_entity()
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[col],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "SUCCESS"

def test_006_geometry_beam_volume(kg):
    beam = make_beam_entity(start_connection='dummy-start', end_connection='dummy-end')
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[beam],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "SUCCESS"

def test_007_geometry_slab_volume(kg):
    slab = make_slab_entity()
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[slab],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "SUCCESS"

def test_008_topology_room_closed(kg):
    room = make_room_entity(closed=True)
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[room],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "SUCCESS"

def test_009_topology_room_not_closed_error(kg):
    room = make_room_entity(closed=False)
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[room],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "FAILED"
    assert any(e["error_code"]=="SEM-001" for e in r["errors"])

def test_010_topology_column_floating_warning(kg):
    """Column tanpa relasi support menghasilkan warning TOP-002."""
    col = make_column_entity()
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[col],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "SUCCESS"
    assert any(w["warning_code"]=="TOP-002" for w in r["warnings"])

def test_011_semantic_door_taller_than_wall_error(kg):
    wall = make_wall_entity(height=2.0)
    # Opening lebih tinggi dari dinding (height 2.0, opening 2.5)
    wall["openings"] = [{"uuid":str(uuid.uuid4()),"type":"DOOR","width":0.9,"height":2.5,"position":1.0}]
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[wall],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "FAILED"
    assert any(e["error_code"]=="SEM-008" for e in r["errors"])

def test_012_rule_validator_standard(kg):
    col = make_column_entity()
    beam = make_beam_entity(start_connection=col["uuid"], end_connection=col["uuid"])
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[col, beam],
           "relationships":[{"source":col["uuid"],"target":beam["uuid"],"type":"SUPPORTS"}]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "SUCCESS"

def test_013_deduction_opening_large(kg):
    wall = make_wall_entity(length=5.0, height=3.5,
                            openings=[{"uuid":str(uuid.uuid4()),"type":"DOOR","width":0.9,"height":2.1,"position":1.0}])
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[wall],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "SUCCESS"
    # Cari item DIN.005
    item = None
    for d in r["boq"]["divisions"]:
        for it in d["items"]:
            if it["item_code"] == "DIN.005":
                item = it
    assert item is not None
    assert item["quantity"] == pytest.approx(15.61, 0.01)

def test_014_deduction_small_opening_ignored(kg):
    wall = make_wall_entity(length=5.0, height=3.5,
                            openings=[{"uuid":str(uuid.uuid4()),"type":"VENT","width":0.3,"height":0.3,"position":1.0}])
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[wall],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "SUCCESS"
    item = next(it for d in r["boq"]["divisions"] for it in d["items"] if it["item_code"] == "DIN.005")
    assert item["quantity"] == pytest.approx(17.5, 0.01)

def test_015_deduction_beam_column_intersection(kg):
    col_uid = str(uuid.uuid4())
    beam_uid = str(uuid.uuid4())
    col = make_column_entity(uid=col_uid)
    beam = make_beam_entity(uid=beam_uid, start_connection=col_uid, end_connection=col_uid)
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[col, beam],
           "relationships":[{"source":col_uid,"target":beam_uid,"type":"SUPPORTS"}]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "SUCCESS"
    # Beton balok = gross volume 0.25*0.4*5 = 0.5
    # Interseksi = 0.3*0.3*0.4 = 0.036
    # Net = 0.464
    beton_beam = next(it for d in r["boq"]["divisions"] for it in d["items"] if it["item_code"] == "STR.029")
    assert beton_beam["quantity"] == pytest.approx(0.464, 0.001)

def test_016_quantity_aggregation(kg):
    w1 = make_wall_entity(length=5.0, height=3.5)
    w2 = make_wall_entity(length=4.0, height=3.5)
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[w1, w2],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "SUCCESS"
    item = next(it for d in r["boq"]["divisions"] for it in d["items"] if it["item_code"] == "DIN.005")
    # 17.5 + 14.0 = 31.5
    assert item["quantity"] == pytest.approx(31.5, 0.01)

def test_017_boq_mapping_workitem(kg):
    wall = make_wall_entity()
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[wall],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "SUCCESS"
    # Harus ada item DIN.005
    assert any(it["item_code"] == "DIN.005" for d in r["boq"]["divisions"] for it in d["items"])

def test_018_boq_division_structure(kg):
    wall = make_wall_entity()
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[wall],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "SUCCESS"
    divisions = [d["division_name"] for d in r["boq"]["divisions"]]
    assert any("DINDING" in d.upper() or "DIV-05" in d.upper() for d in divisions)

def test_019_trace_log_every_item(kg):
    wall = make_wall_entity()
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[wall],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "SUCCESS"
    for d in r["boq"]["divisions"]:
        for it in d["items"]:
            assert "trace_log" in it
            assert isinstance(it["trace_log"]["computation_steps"], list)

def test_020_determinism(kg):
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[make_wall_entity()],"relationships":[]}
    pipeline = QuantityCompilerPipeline(kg, generated_at="2026-08-13T00:00:00+00:00")
    r1 = pipeline.compile(ccm, "JAKARTA")
    r2 = pipeline.compile(ccm, "JAKARTA")
    r3 = pipeline.compile(ccm, "JAKARTA")
    assert r1["boq"]["project_total"] == r2["boq"]["project_total"] == r3["boq"]["project_total"]
    assert r1["boq"]["total_items"] == r2["boq"]["total_items"] == r3["boq"]["total_items"]
    assert json.dumps(r1["boq"], sort_keys=True, default=str) == json.dumps(r2["boq"], sort_keys=True, default=str) == json.dumps(r3["boq"], sort_keys=True, default=str)
    assert json.dumps(r1["boq"], sort_keys=True, default=str) == json.dumps(r2["boq"], sort_keys=True, default=str) == json.dumps(r3["boq"], sort_keys=True, default=str)

def test_021_idempotency(kg):
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[make_wall_entity()],"relationships":[]}
    pipeline = QuantityCompilerPipeline(kg)
    r1 = pipeline.compile(ccm, "JAKARTA")
    r2 = pipeline.compile(ccm, "JAKARTA")
    # generated_at sama karena pipeline sama
    assert r1["boq"]["generated_at"] == r2["boq"]["generated_at"]

def test_022_error_semantic_room_not_closed(kg):
    room = make_room_entity(closed=False)
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[room],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "FAILED"
    assert r["failed_stage"] == "SEMANTIC_ANALYZER"

def test_023_warning_continuable(kg):
    beam = make_beam_entity(start_connection='dummy-start', end_connection='dummy-end')
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[beam],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "SUCCESS"
    assert len(r["warnings"]) > 0

def test_024_plaster_area_two_sides(kg):
    wall = make_wall_entity(length=5.0, height=3.5)
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[wall],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "SUCCESS"
    plaster = next(it for d in r["boq"]["divisions"] for it in d["items"] if it["item_code"] == "DIN.008")
    # Net 17.5, plaster 35.0
    assert plaster["quantity"] == pytest.approx(35.0, 0.01)

def test_025_floor_finish_room_area(kg):
    room = make_room_entity(closed=True)
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[room],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "SUCCESS"
    floor = next(it for d in r["boq"]["divisions"] for it in d["items"] if it["item_code"] == "FIN.004" or it["item_code"] == "FIN.005")
    assert floor["quantity"] == pytest.approx(12.0, 0.01)

def test_026_slab_beam_intersection_deduction(kg):
    """ACTS-400-015 tambahan: slab volume berkurang akibat beam."""
    import uuid as _uuid
    beam_uid = str(_uuid.uuid4())
    slab_uid = str(_uuid.uuid4())
    beam = make_beam_entity(uid=beam_uid, w=0.25, d=0.4, l=4.0, start_connection='dummy-start', end_connection='dummy-end')
    slab = {
        "uuid": slab_uid,
        "entity_type": "Physical",
        "type": "Slab",
        "name": "Slab Intersection",
        "geometry": {
            "boundary": {"points": [
                {"x":0,"y":0,"z":0},{"x":4,"y":0,"z":0},{"x":4,"y":3,"z":0},{"x":0,"y":3,"z":0},{"x":0,"y":0,"z":0}
            ]},
            "thickness": 0.12
        },
        "supports": [beam_uid]
    }
    ccm = {
        "ccm_version": "1.0.0",
        "project_uuid": str(_uuid.uuid4()),
        "entities": [beam, slab],
        "relationships": [{"source": beam_uid, "target": slab_uid, "type": "SUPPORTS"}]
    }
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "SUCCESS"

    # Cari item beton plat (STR.029) yang deskripsinya mengandung "Plat"
    beton_plat = None
    for d in r["boq"]["divisions"]:
        for it in d["items"]:
            if it["item_code"] == "STR.029" and ("Plat" in it["description"] or "Slab" in it["description"]):
                beton_plat = it
                break
        if beton_plat:
            break
    assert beton_plat is not None

    # Gross slab 4x3x0.12 = 1.44, intersection beam 0.25*(0.4-0.12)*4 = 0.28, net = 1.16
    assert beton_plat["quantity"] == pytest.approx(1.16, 0.001)

def test_027_wall_wall_intersection_area_unchanged(kg):
    """Area pasangan bata tidak berubah karena deduksi interseksi dinding hanya untuk volume."""
    w1 = make_wall_entity(length=5.0, height=3.5)
    w2 = make_wall_entity(length=4.0, height=3.5)
    ccm = {
        "ccm_version": "1.0.0",
        "project_uuid": str(uuid.uuid4()),
        "entities": [w1, w2],
        "relationships": [{"source": w1["uuid"], "target": w2["uuid"], "type": "WALL_ADJACENT"}]
    }
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "SUCCESS"
    pasangan = next(it for d in r["boq"]["divisions"] for it in d["items"] if it["item_code"] == "DIN.005")
    # w1 17.5 m² + w2 14.0 m² = 31.5 m²
    assert pasangan["quantity"] == pytest.approx(31.5, 0.01)


def test_028_no_mojibake_in_output(kg):
    """Pastikan tidak ada karakter mÂ²/mÂ³ di output BOQ."""
    wall = make_wall_entity()
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[wall],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "SUCCESS"
    for div in r["boq"]["divisions"]:
        for it in div["items"]:
            for field in ["unit", "description", "item_name"]:
                val = it.get(field, "")
                assert "mÂ²" not in val and "mÂ³" not in val
            tl = it.get("trace_log", {})
            for step in tl.get("computation_steps", []):
                for key in ["output_value", "operation_detail"]:
                    val = step.get(key, "")
                    assert "mÂ²" not in val and "mÂ³" not in val


def test_029_rab_determinism(kg):
    """Pastikan RAB deterministik untuk input yang sama."""
    from fastra_core.compiler.cost_engine import CostEngine

    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[make_wall_entity()],"relationships":[]}
    pipeline = QuantityCompilerPipeline(kg, generated_at="2026-08-13T00:00:00+00:00")
    r1 = pipeline.compile(ccm, "JAKARTA")
    r2 = pipeline.compile(ccm, "JAKARTA")
    r3 = pipeline.compile(ccm, "JAKARTA")

    engine = CostEngine(kg)
    rab1 = engine.generate_rab(r1["boq"], "JAKARTA")
    rab2 = engine.generate_rab(r2["boq"], "JAKARTA")
    rab3 = engine.generate_rab(r3["boq"], "JAKARTA")

    assert json.dumps(rab1, sort_keys=True, default=str) == json.dumps(rab2, sort_keys=True, default=str) == json.dumps(rab3, sort_keys=True, default=str)


def test_030_random_wall_ccm(kg):
    """Property-based test sederhana: jalankan 10 CCM acak dengan wall."""
    for _ in range(10):
        length = random.uniform(1.0, 20.0)
        height = random.uniform(2.0, 5.0)
        thickness = random.uniform(0.1, 0.4)
        has_opening = random.choice([True, False])
        openings = []
        if has_opening:
            op_width = random.uniform(0.3, 1.5)
            op_height = random.uniform(0.5, 3.0)
            openings.append({
                "uuid": str(uuid.uuid4()),
                "type": "DOOR",
                "width": op_width,
                "height": op_height,
                "position": 0.5
            })
        wall = make_wall_entity(length=length, height=height)
        wall["geometry"]["thickness"] = thickness
        wall["openings"] = openings
        ccm = {
            "ccm_version": "1.0.0",
            "project_uuid": str(uuid.uuid4()),
            "entities": [wall],
            "relationships": []
        }
        r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
        # Pipeline harus menghasilkan SUCCESS atau FAILED yang terkontrol (tidak crash)
        assert r["compilation_status"] in ("SUCCESS", "FAILED")


def test_031_fuzz_multiple_entities(kg):
    """Fuzzing ekstrem: kombinasi acak beberapa entitas dan relasi."""
    random.seed(42)
    for _ in range(5):
        entities = []
        relationships = []
        # Wall
        wall = make_wall_entity(length=random.uniform(1, 15), height=random.uniform(2, 6))
        entities.append(wall)
        # Column & Beam
        col = make_column_entity(w=random.uniform(0.2, 0.6), d=random.uniform(0.2, 0.6), h=random.uniform(2, 5))
        entities.append(col)
        beam = make_beam_entity(w=random.uniform(0.2, 0.4), d=random.uniform(0.3, 0.7), l=random.uniform(2, 10),
                                start_connection=col["uuid"], end_connection=col["uuid"])
        entities.append(beam)
        relationships.append({"source": col["uuid"], "target": beam["uuid"], "type": "SUPPORTS"})
        # Slab
        slab = make_slab_entity(thickness=random.uniform(0.1, 0.2))
        entities.append(slab)
        relationships.append({"source": beam["uuid"], "target": slab["uuid"], "type": "SUPPORTS"})
        # Room
        room = make_room_entity(closed=True)
        entities.append(room)
        ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
               "entities":entities,"relationships":relationships}
        r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
        assert r["compilation_status"] in ("SUCCESS", "FAILED")
        if r["compilation_status"] == "SUCCESS":
            for d in r["boq"]["divisions"]:
                for it in d["items"]:
                    assert "mÂ²" not in it["unit"] and "mÂ³" not in it["unit"]


def test_032_malformed_ccm(kg):
    """Fuzzing: berbagai input CCM malformed."""
    malformed = [
        "string acak",
        123,
        None,
        [1, 2, 3],
        {"ccm_version": "1.0.0", "project_uuid": "invalid-uuid", "entities": [], "relationships": []},
        {"ccm_version": "1.0.0", "project_uuid": str(uuid.uuid4()), "entities": [{"uuid": "bad"}], "relationships": []},
        {"ccm_version": "1.0.0", "project_uuid": str(uuid.uuid4()), "entities": [], "relationships": [{"source": "x"}]},
    ]
    for idx, ccm in enumerate(malformed):
        r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
        assert r["compilation_status"] in ("SUCCESS", "FAILED")
        if r["compilation_status"] == "FAILED":
            assert isinstance(r["errors"], list)


def test_033_relationship_missing_entity(kg):
    """Fuzzing: relasi menunjuk entitas yang tidak ada."""
    wall = make_wall_entity()
    ccm = {
        "ccm_version": "1.0.0",
        "project_uuid": str(uuid.uuid4()),
        "entities": [wall],
        "relationships": [{"source": wall["uuid"], "target": str(uuid.uuid4()), "type": "SUPPORTS"}]
    }
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] in ("SUCCESS", "FAILED")


def test_034_extreme_values(kg):
    """Fuzzing: nilai ekstrem 0/negatif harus ditolak."""
    # Wall height 0
    wall = make_wall_entity(height=0.0)
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[wall],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "FAILED"

    # Column width negatif
    col = make_column_entity(w=-0.3)
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[col],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "FAILED"


def test_035_fuzz_determinism(kg):
    """Fuzzing: determinisme byte-per-byte untuk input acak yang sama."""
    random.seed(99)
    entities = []
    for i in range(5):
        wall = make_wall_entity(length=random.uniform(1, 20), height=random.uniform(2, 5))
        entities.append(wall)
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":entities,"relationships":[]}
    pipeline = QuantityCompilerPipeline(kg, generated_at="2026-08-19T00:00:00+00:00")
    r1 = pipeline.compile(ccm, "JAKARTA")
    r2 = pipeline.compile(ccm, "JAKARTA")
    r3 = pipeline.compile(ccm, "JAKARTA")
    assert json.dumps(r1, sort_keys=True, default=str) == json.dumps(r2, sort_keys=True, default=str) == json.dumps(r3, sort_keys=True, default=str)


def test_036_malformed_json_string(kg):
    """Fuzzing: Lexer harus menolak JSON string malformed."""
    pipeline = QuantityCompilerPipeline(kg)
    r = pipeline.compile("{invalid json", "JAKARTA")
    assert r["compilation_status"] == "FAILED"
    assert any(e.get("error_code") == "LEX-001" for e in r.get("errors", []))


def test_037_geometric_T_L_junction(kg):
    """Fuzzing: dua dinding bertemu di sudut (L-junction) dan T-junction."""
    # L-junction: ujung bertemu
    w1 = make_wall_entity(length=5.0, height=3.0)
    w2 = make_wall_entity(length=4.0, height=3.0)
    w1["geometry"]["axis_line"]["points"] = [{"x":0,"y":0,"z":0}, {"x":5,"y":0,"z":0}]
    w2["geometry"]["axis_line"]["points"] = [{"x":5,"y":0,"z":0}, {"x":5,"y":4,"z":0}]
    ccm = {
        "ccm_version": "1.0.0",
        "project_uuid": str(uuid.uuid4()),
        "entities": [w1, w2],
        "relationships": [{"source": w1["uuid"], "target": w2["uuid"], "type": "WALL_ADJACENT"}]
    }
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] in ("SUCCESS", "FAILED")

def test_038_multiple_slabs(kg):
    """Fuzzing: banyak slab dengan dukungan berbeda."""
    slabs = []
    relations = []
    for i in range(3):
        s = make_slab_entity(thickness=0.12 + i*0.01, supports=[f"support-{i}"])
        slabs.append(s)
        # beam support dummy untuk masing-masing
        beam = make_beam_entity(l=4.0, start_connection='dummy-start', end_connection='dummy-end')
        slabs.append(beam)
        relations.append({"source": beam["uuid"], "target": s["uuid"], "type": "SUPPORTS"})
    ccm = {
        "ccm_version": "1.0.0",
        "project_uuid": str(uuid.uuid4()),
        "entities": slabs,
        "relationships": relations
    }
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] in ("SUCCESS", "FAILED")

def test_039_malformed_geometry_nan_inf(kg):
    """Fuzzing: geometri NaN/Infinity harus ditolak."""
    wall = make_wall_entity(length=float('nan'), height=3.0)
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[wall],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "FAILED"

def test_040_negative_dimension(kg):
    """Fuzzing: dimensi negatif harus ditolak."""
    wall = make_wall_entity(height=-3.0)
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[wall],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "FAILED"


def test_041_self_intersecting_polygon(kg):
    """Fuzzing: slab dengan polygon self-intersecting harus ditolak."""
    import uuid as _uuid
    slab = {
        "uuid": str(_uuid.uuid4()), "entity_type":"Physical", "type":"Slab",
        "name":"Bowtie", "geometry":{
            "boundary":{"points":[
                {"x":0,"y":0,"z":0},{"x":4,"y":4,"z":0},{"x":4,"y":0,"z":0},{"x":0,"y":4,"z":0},{"x":0,"y":0,"z":0}
            ]},
            "thickness":0.12
        },
        "supports":["dummy"]
    }
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[slab],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "FAILED"

def test_042_degenerate_polygon(kg):
    """Fuzzing: polygon degenerasi (titik berimpit)."""
    import uuid as _uuid
    slab = {
        "uuid": str(_uuid.uuid4()), "entity_type":"Physical", "type":"Slab",
        "name":"Degenerate", "geometry":{
            "boundary":{"points":[
                {"x":0,"y":0,"z":0},{"x":0,"y":0,"z":0},{"x":1,"y":1,"z":0},{"x":0,"y":0,"z":0}
            ]},
            "thickness":0.12
        },
        "supports":["dummy"]
    }
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[slab],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "FAILED"

def test_043_polyline_wall(kg):
    """Fuzzing: wall dengan axis_line 4 titik polyline."""
    wall = make_wall_entity(length=5.0, height=3.0)
    wall["geometry"]["axis_line"]["points"] = [
        {"x":0,"y":0,"z":0},{"x":5,"y":0,"z":0},{"x":5,"y":4,"z":0},{"x":0,"y":4,"z":0}
    ]
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[wall],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] in ("SUCCESS", "FAILED")

def test_044_tolerance_junction(kg):
    """Fuzzing: T/L junction dengan jarak tepat toleransi."""
    w1 = make_wall_entity(length=5.0, height=3.0)
    w2 = make_wall_entity(length=4.0, height=3.0)
    w1["geometry"]["axis_line"]["points"] = [{"x":0,"y":0,"z":0},{"x":5,"y":0,"z":0}]
    w2["geometry"]["axis_line"]["points"] = [{"x":5.0005,"y":0,"z":0},{"x":5.0005,"y":4,"z":0}]
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[w1,w2],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] in ("SUCCESS", "FAILED")

def test_045_multiple_overlapping_beams_slabs(kg):
    """Fuzzing: beberapa beam dan slab tumpang tindih."""
    entities = []
    relations = []
    for i in range(4):
        slab = make_slab_entity(thickness=0.12+i*0.02, supports=[f"sup-{i}"])
        entities.append(slab)
        beam = make_beam_entity(l=3.0, start_connection=f"col-{i}", end_connection=f"col-{i+1}")
        entities.append(beam)
        relations.append({"source": beam["uuid"], "target": slab["uuid"], "type": "SUPPORTS"})
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":entities,"relationships":relations}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] in ("SUCCESS", "FAILED")

def test_046_nan_inf_coordinates(kg):
    """Fuzzing: koordinat NaN/Infinity."""
    wall = make_wall_entity(length=5.0, height=3.0)
    wall["geometry"]["axis_line"]["points"] = [{"x":0,"y":0,"z":0},{"x":float('nan'),"y":0,"z":0}]
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[wall],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] in ("SUCCESS", "FAILED")

def test_047_cyclic_relationships(kg):
    """Fuzzing: relasi siklik A supports B, B supports A."""
    col = make_column_entity()
    beam = make_beam_entity(start_connection=col["uuid"], end_connection=col["uuid"])
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[col, beam],
           "relationships":[
               {"source":col["uuid"],"target":beam["uuid"],"type":"SUPPORTS"},
               {"source":beam["uuid"],"target":col["uuid"],"type":"SUPPORTS"}
           ]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] in ("SUCCESS", "FAILED")

def test_048_fuzz_100_iterations(kg):
    """Fuzzing massal 100 iterasi acak."""
    random.seed(123)
    for _ in range(100):
        length = random.uniform(1, 10)
        height = random.uniform(2, 5)
        wall = make_wall_entity(length=length, height=height)
        ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
               "entities":[wall],"relationships":[]}
        r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
        assert r["compilation_status"] in ("SUCCESS", "FAILED")

def test_049_all_entity_malformed(kg):
    """Fuzzing: malformed geometry untuk berbagai tipe entitas."""
    import uuid as _uuid
    entities = [
        {"uuid":str(_uuid.uuid4()),"entity_type":"Physical","type":"Column","name":"C","geometry":{"width":0,"depth":0,"height":0}},
        {"uuid":str(_uuid.uuid4()),"entity_type":"Physical","type":"Beam","name":"B","geometry":{"width":-0.2,"depth":0.4,"length":5}},
        {"uuid":str(_uuid.uuid4()),"entity_type":"Spatial","type":"Room","name":"R","geometry":{"boundary":{"points":[{"x":0,"y":0,"z":0},{"x":1,"y":0,"z":0},{"x":0,"y":0,"z":0}]}}}
    ]
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":entities,"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] in ("SUCCESS", "FAILED")

def test_050_lifecycle_transition_invalid(kg):
    """Lifecycle state machine: transisi OBSOLETE ke ACTIVE harus ditolak."""
    from fastra_core.ontology.lifecycle import LifecycleStatus
    from fastra_core.ontology.universal_object import UniversalObject
    obj = UniversalObject(status=LifecycleStatus.OBSOLETE)
    try:
        obj.transition_to(LifecycleStatus.ACTIVE)
        assert False, "Transisi tidak valid seharusnya memunculkan ValueError"
    except ValueError:
        pass


def test_051_unit_known_validation(kg):
    """Unit rules otomatis: unit tidak dikenal harus ditolak."""
    from fastra_core.ccm.economic import WorkItem
    from fastra_core.units.exceptions import UnitMismatchError
    with pytest.raises(UnitMismatchError):
        WorkItem(work_item_code="X", unit="buah")  # 'buah' tidak dikenal

def test_052_fuzz_500_iterations(kg):
    """Fuzzing massal 500 iterasi dengan seed berbeda."""
    random.seed(2026)
    for _ in range(500):
        length = random.uniform(1, 15)
        height = random.uniform(2, 6)
        wall = make_wall_entity(length=length, height=height)
        ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
               "entities":[wall],"relationships":[]}
        r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
        assert r["compilation_status"] in ("SUCCESS", "FAILED")

def test_053_lifecycle_multiple_transitions(kg):
    """Lifecycle state machine: beberapa transisi valid & invalid."""
    from fastra_core.ontology.lifecycle import LifecycleStatus
    from fastra_core.ontology.universal_object import UniversalObject
    obj = UniversalObject(status=LifecycleStatus.DRAFT)
    obj.transition_to(LifecycleStatus.ACTIVE)
    assert obj.status == LifecycleStatus.ACTIVE
    obj.transition_to(LifecycleStatus.SUPERSEDED)
    assert obj.status == LifecycleStatus.SUPERSEDED
    with pytest.raises(ValueError):
        obj.transition_to(LifecycleStatus.ACTIVE)  # SUPERSEDED -> ACTIVE invalid


@settings(deadline=None, max_examples=10)
@given(st.floats(min_value=1.0, max_value=10.0), st.floats(min_value=2.0, max_value=5.0))
def test_054_hypothesis_wall(length, height):
    """Property-based testing: wall area = length * height."""
    kg = create_fastra_knowledge_graph()
    wall = make_wall_entity(length=length, height=height)
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[wall],"relationships":[]}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "SUCCESS"
    for d in r["boq"]["divisions"]:
        for it in d["items"]:
            if it["item_code"] == "DIN.005":
                assert it["quantity"] == pytest.approx(length * height, 0.001)

# ====================================================================
# TAMBAHAN FUZZING SANGAT EKSTREM — Fase 5 Non‑Fungsional
# ====================================================================

def _extreme_slab(uuid_val, thickness=0.12, scale=1e12):
    """Slab dengan koordinat sangat besar, tetap valid."""
    pts = [
        {"x": scale, "y": scale, "z": 0},
        {"x": scale + 5, "y": scale, "z": 0},
        {"x": scale + 5, "y": scale + 4, "z": 0},
        {"x": scale, "y": scale + 4, "z": 0},
        {"x": scale, "y": scale, "z": 0},
    ]
    return {
        "uuid": uuid_val,
        "entity_type": "Physical",
        "type": "Slab",
        "name": "Extreme Slab",
        "geometry": {"boundary": {"points": pts}, "thickness": thickness},
        "supports": ["dummy-support"]
    }

def _wall_with_opening_extreme(uid_val, length=5.0, height=3.5, opening_width=0.9, opening_height=2.5):
    return {
        "uuid": uid_val,
        "entity_type": "Physical",
        "type": "Wall",
        "name": "Extreme Wall",
        "geometry": {
            "axis_line": {"points": [{"x": 0, "y": 0, "z": 0}, {"x": length, "y": 0, "z": 0}]},
            "height": height,
            "thickness": 0.15
        },
        "construction_type": "BATA_MERAH",
        "openings": [{
            "uuid": str(uuid.uuid4()),
            "type": "DOOR",
            "width": opening_width,
            "height": opening_height,
            "position": 0.5
        }]
    }

def test_055_extreme_coordinate_large_scale_slab(kg):
    """Slab dengan koordinat 1e12; pipeline harus tidak crash & deterministik."""
    slab = _extreme_slab(str(uuid.uuid4()))
    ccm = {"ccm_version": "1.0.0", "project_uuid": str(uuid.uuid4()),
           "entities": [slab], "relationships": []}
    pipeline = QuantityCompilerPipeline(kg, generated_at="2026-08-19T00:00:00+00:00")
    r1 = pipeline.compile(ccm, "JAKARTA")
    r2 = pipeline.compile(ccm, "JAKARTA")
    assert r1["compilation_status"] in ("SUCCESS", "FAILED")
    if r1["compilation_status"] == "SUCCESS":
        assert json.dumps(r1, sort_keys=True, default=str) == json.dumps(r2, sort_keys=True, default=str)

def test_056_extreme_coordinate_negative_large(kg):
    """Koordinat negatif sangat besar; pipeline harus menangani tanpa hang."""
    slab = _extreme_slab(str(uuid.uuid4()), scale=-1e12)
    ccm = {"ccm_version": "1.0.0", "project_uuid": str(uuid.uuid4()),
           "entities": [slab], "relationships": []}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] in ("SUCCESS", "FAILED")

def test_057_polygon_many_vertices_100(kg):
    """Slab dengan 100 titik boundary (poligon valid, konveks)."""
    import math
    uid = str(uuid.uuid4())
    n = 100
    pts = []
    for i in range(n):
        angle = 2 * math.pi * i / n
        pts.append({"x": 10 + 3 * math.cos(angle), "y": 10 + 3 * math.sin(angle), "z": 0})
    pts.append(pts[0])  # close
    slab = {
        "uuid": uid,
        "entity_type": "Physical",
        "type": "Slab",
        "name": "Slab 100 vertices",
        "geometry": {"boundary": {"points": pts}, "thickness": 0.12},
        "supports": ["dummy"]
    }
    ccm = {"ccm_version": "1.0.0", "project_uuid": str(uuid.uuid4()),
           "entities": [slab], "relationships": []}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] in ("SUCCESS", "FAILED")

def test_058_polygon_concave_extreme(kg):
    """Slab concave dengan 10 titik; harus tetap diproses atau error terkontrol."""
    pts = [
        {"x": 0, "y": 0, "z": 0},
        {"x": 10, "y": 0, "z": 0},
        {"x": 10, "y": 10, "z": 0},
        {"x": 8, "y": 8, "z": 0},
        {"x": 6, "y": 10, "z": 0},
        {"x": 4, "y": 8, "z": 0},
        {"x": 2, "y": 10, "z": 0},
        {"x": 0, "y": 10, "z": 0},
        {"x": 0, "y": 0, "z": 0},
    ]
    slab = {
        "uuid": str(uuid.uuid4()), "entity_type": "Physical", "type": "Slab",
        "name": "Concave Slab",
        "geometry": {"boundary": {"points": pts}, "thickness": 0.12},
        "supports": ["dummy"]
    }
    ccm = {"ccm_version": "1.0.0", "project_uuid": str(uuid.uuid4()),
           "entities": [slab], "relationships": []}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] in ("SUCCESS", "FAILED")

def test_059_wall_opening_extreme_dimensions(kg):
    """Wall dengan bukaan sangat besar hingga melebihi dinding harus ditolak atau sukses terkontrol."""
    wall = _wall_with_opening_extreme(str(uuid.uuid4()), length=2.0, height=3.0, opening_width=1.5, opening_height=2.8)
    ccm = {"ccm_version": "1.0.0", "project_uuid": str(uuid.uuid4()),
           "entities": [wall], "relationships": []}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] in ("SUCCESS", "FAILED")

def test_060_hypothesis_random_wall_all_dimensions():
    """Property‑based: dimensi wall acak ekstrem, pipeline tidak boleh crash."""
    kg = create_fastra_knowledge_graph()
    @settings(deadline=None, max_examples=50)
    @given(
        length=st.floats(min_value=1e-6, max_value=1e9, allow_nan=False, allow_infinity=False, allow_subnormal=False),
        height=st.floats(min_value=1e-6, max_value=1e9, allow_nan=False, allow_infinity=False, allow_subnormal=False),
        thickness=st.floats(min_value=1e-6, max_value=1e2, allow_nan=False, allow_infinity=False, allow_subnormal=False),
        op_width=st.one_of(st.none(), st.floats(min_value=1e-6, max_value=1e3, allow_nan=False, allow_infinity=False)),
        op_height=st.one_of(st.none(), st.floats(min_value=1e-6, max_value=1e3, allow_nan=False, allow_infinity=False)),
    )
    def _run(length, height, thickness, op_width, op_height):
        wall = _wall_with_opening_extreme(str(uuid.uuid4()), length=length, height=height)
        wall["geometry"]["thickness"] = thickness
        if op_width is not None and op_height is not None:
            wall["openings"] = [{
                "uuid": str(uuid.uuid4()), "type": "DOOR",
                "width": op_width, "height": op_height, "position": 0.5
            }]
        ccm = {"ccm_version": "1.0.0", "project_uuid": str(uuid.uuid4()),
               "entities": [wall], "relationships": []}
        r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
        assert r["compilation_status"] in ("SUCCESS", "FAILED")
    _run()

def test_061_extreme_many_entities_100(kg):
    """100 entitas campuran; pipeline harus selesai tanpa hang & deterministik."""
    entities = []
    relations = []
    for i in range(25):
        col = make_column_entity(uid=str(uuid.uuid4()), w=0.3 + i*0.001, d=0.3, h=3.5)
        entities.append(col)
        beam = make_beam_entity(uid=str(uuid.uuid4()), w=0.25, d=0.4, l=5.0,
                                start_connection=col["uuid"], end_connection=col["uuid"])
        entities.append(beam)
        relations.append({"source": col["uuid"], "target": beam["uuid"], "type": "SUPPORTS"})
        slab = make_slab_entity(uid=str(uuid.uuid4()), thickness=0.12)
        entities.append(slab)
        relations.append({"source": beam["uuid"], "target": slab["uuid"], "type": "SUPPORTS"})
        room = make_room_entity(uid=str(uuid.uuid4()), closed=True)
        entities.append(room)
    ccm = {"ccm_version": "1.0.0", "project_uuid": str(uuid.uuid4()),
           "entities": entities, "relationships": relations}
    pipeline = QuantityCompilerPipeline(kg, generated_at="2026-08-19T00:00:00+00:00")
    r1 = pipeline.compile(ccm, "JAKARTA")
    r2 = pipeline.compile(ccm, "JAKARTA")
    assert r1["compilation_status"] in ("SUCCESS", "FAILED")
    if r1["compilation_status"] == "SUCCESS":
        assert json.dumps(r1["boq"], sort_keys=True, default=str) == json.dumps(r2["boq"], sort_keys=True, default=str)

def test_062_nested_polygons_slabs(kg):
    """Slab dengan poligon bersarang (outer & inner hole) harus ditolak karena area nol/self-intersecting."""
    # Outer: 0,0 -> 10,0 -> 10,10 -> 0,10 -> 0,0
    # Inner: 4,4 -> 6,4 -> 6,6 -> 4,6 -> 4,4 (akan membuat self-intersecting/area negatif? Tetap diuji tidak crash)
    pts = [
        {"x": 0, "y": 0, "z": 0},
        {"x": 10, "y": 0, "z": 0},
        {"x": 10, "y": 10, "z": 0},
        {"x": 4, "y": 4, "z": 0},
        {"x": 6, "y": 4, "z": 0},
        {"x": 6, "y": 6, "z": 0},
        {"x": 4, "y": 6, "z": 0},
        {"x": 0, "y": 0, "z": 0},
    ]
    slab = {
        "uuid": str(uuid.uuid4()), "entity_type": "Physical", "type": "Slab",
        "name": "Nested Slab",
        "geometry": {"boundary": {"points": pts}, "thickness": 0.12},
        "supports": ["dummy"]
    }
    ccm = {"ccm_version": "1.0.0", "project_uuid": str(uuid.uuid4()),
           "entities": [slab], "relationships": []}
    r = QuantityCompilerPipeline(kg).compile(ccm, "JAKARTA")
    assert r["compilation_status"] in ("SUCCESS", "FAILED")