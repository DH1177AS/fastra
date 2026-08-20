from pathlib import Path

p = Path("tests/test_compliance_aces400.py")
s = p.read_text(encoding="utf-8")
s = s.replace("import pytest, uuid, json, random", "import pytest, uuid, json, random\nfrom hypothesis import given, settings, strategies as st")
new_test = '''

@settings(max_examples=50)
@given(st.floats(min_value=1.0, max_value=10.0), st.floats(min_value=2.0, max_value=5.0))
def test_054_hypothesis_wall(length, height):
    """Property-based testing: wall area = length * height."""
    wall = make_wall_entity(length=length, height=height)
    ccm = {"ccm_version":"1.0.0","project_uuid":str(uuid.uuid4()),
           "entities":[wall],"relationships":[]}
    r = QuantityCompilerPipeline(create_fastra_knowledge_graph()).compile(ccm, "JAKARTA")
    assert r["compilation_status"] == "SUCCESS"
    for d in r["boq"]["divisions"]:
        for it in d["items"]:
            if it["item_code"] == "DIN.005":
                assert it["quantity"] == pytest.approx(length * height, 0.001)
'''
s = s.rstrip() + "\n" + new_test
p.write_text(s, encoding="utf-8")
print("✅ test_054 hypothesis ditambahkan")
