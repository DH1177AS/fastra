
"""
Unit test untuk fastra_core/compiler/ccm_validator.py.
Fokus: parsing multi?part JSON, merge ProjectID, validasi framing, report.
"""
import json
import pytest

from fastra_core.compiler.ccm_validator import (
    parse_multi_json,
    merge_ccm_parts,
    run_pipeline,
    validate_structural_framing,
    validate_element_geometry,
    validate_mep_paths,
    validate_space_boundaries,
    validate_project_level_data,
    CCMMergeError,
    CCMParseError,
)


def _make_part(project_id: str, building_id: str = "BLDG-01"):
    return {
        "ConstructionCanonicalModel_Part1": {
            "ModelMetadata": {
                "SchemaVersion": "CCM-RES-2026.V4",
                "ProjectContext": {
                    "ProjectID": project_id,
                    "ProjectName": "Test House",
                    "Phase": "Detailed Design",
                    "Currency": "IDR",
                },
            },
            "BuildingEntities": [
                {
                    "BuildingID": building_id,
                    "BuildingName": "Test Building",
                    "GrossFloorArea_m2": 100.0,
                    "Storeys": [
                        {
                            "StoreyID": "ST-01",
                            "StoreyName": "Ground",
                            "Elevation_Level_m": 0.0,
                            "ClearHeight_m": 3.0,
                            "SpatialZones": [
                                {
                                    "ZoneID": "ZONE-01",
                                    "Name": "Public",
                                    "Spaces": [
                                        {
                                            "SpaceID": "SP-01",
                                            "Name": "Living",
                                            "Dimensions": {"Area_m2": 30.0, "Perimeter_m": 22.0},
                                            "Boundary": {"Points": None},
                                            "WBS_Code": "WBS-1.02.01",
                                            "FinishesSchedule": {
                                                "Floor": {"Material": "Tile", "Quantity_m2": 30.0},
                                                "Wall": {"Material": "Plaster", "Quantity_m2": 50.0},
                                                "Ceiling": {"Material": "Gypsum", "Quantity_m2": 30.0},
                                            },
                                            "BuildingElements": [
                                                {
                                                    "ElementID": "WAL-01",
                                                    "Type": "Wall",
                                                    "ParentSpaceID": "SP-01",
                                                    "geometry": {
                                                        "axis_line": {"points": None},
                                                        "height": None,
                                                        "thickness": 0.15,
                                                    },
                                                }
                                            ],
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
            "InfrastructureSystems": {
                "StructuralSystem": {
                    "Foundation": {"Type": "Batu Kali"},
                    "Framing": {
                        "Sloof_Dimensions_mm": None,
                        "Column_Main_Dimensions_mm": None,
                        "RingBalk_Dimensions_mm": [150, 200],
                    },
                }
            },
        }
    }


def test_parse_multi_json_dua_objek():
    raw = json.dumps(_make_part("PRJ-1")) + "\n" + json.dumps(_make_part("PRJ-1"))
    parts = parse_multi_json(raw)
    assert len(parts) == 2


def test_merge_project_id_sama():
    parts = [_make_part("PRJ-1"), _make_part("PRJ-1")]
    merged, notes = merge_ccm_parts(parts)
    assert len(notes) == 2
    assert merged["BuildingEntities"]


def test_merge_project_id_beda_ditolak():
    parts = [_make_part("PRJ-1"), _make_part("PRJ-2")]
    with pytest.raises(CCMMergeError):
        merge_ccm_parts(parts)


def test_run_pipeline_menghasilkan_validation_report():
    raw = json.dumps(_make_part("PRJ-1"))
    result = run_pipeline(raw)
    report = result["ConstructionCanonicalModel"]["ValidationReport"]
    assert "OverallStatus" in report
    assert report["BlockingIssuesCount"] >= 1  # Sloof & Column kosong


def test_run_pipeline_parse_error():
    with pytest.raises(CCMParseError):
        run_pipeline("ini bukan json")

# ===== TAMBAHAN PENGUJIAN VALIDASI =====

def test_parse_multi_json_dengan_whitespace_ekstrem():
    raw = '\n\t' + json.dumps(_make_part("PRJ-1")) + '\n\n' + json.dumps(_make_part("PRJ-1")) + '\n'
    parts = parse_multi_json(raw)
    assert len(parts) == 2

def test_merge_part_tanpa_project_id_tidak_menghentikan_merge():
    parts = [_make_part("PRJ-1"), {"UnknownRoot": {"SomeData": True}}]
    merged, notes = merge_ccm_parts(parts)
    assert merged["BuildingEntities"]
    assert len(notes) == 2

def test_validate_structural_framing_blocking():
    parts = [_make_part("PRJ-1")]
    merged, _ = merge_ccm_parts(parts)
    findings = validate_structural_framing(merged)
    blocking = [f for f in findings if f.severity == "BLOCKING_ISSUE"]
    assert len(blocking) >= 2  # Sloof & Column kosong

def test_validate_element_geometry_detects_missing_axis_line():
    parts = [_make_part("PRJ-1")]
    merged, _ = merge_ccm_parts(parts)
    findings = validate_element_geometry(merged)
    # Harus ada minimal satu temuan untuk Wall WAL-01
    assert any("WAL-01" in f.path and "geometry" in f.path for f in findings)

def test_validate_mep_paths_detects_missing():
    merged = {
        "BuildingEntities": [{
            "BuildingID": "B-1",
            "Storeys": [{
                "SpatialZones": [{
                    "Spaces": [{
                        "SpaceID": "SP-X",
                        "MEP_DistributionPoints": {
                            "Electrical": [
                                {"FixtureID": "EL-01", "CircuitPath": {"length_m": None, "estimated_length_m": None}}
                            ],
                            "PlumbingFixtures": [
                                {"FixtureID": "PL-01", "PipeRun": {"cold_water_length_m": None, "waste_length_m": None}}
                            ]
                        }
                    }]
                }]
            }]
        }]
    }
    findings = validate_mep_paths(merged)
    assert len(findings) >= 2

def test_run_pipeline_incomplete_ccm_status():
    raw = json.dumps(_make_part("PRJ-1"))
    result = run_pipeline(raw)
    report = result["ConstructionCanonicalModel"]["ValidationReport"]
    assert report["OverallStatus"] != "READY — SEMUA VALIDASI TERPENUHI"
    assert report["NeedsClientInputCount"] > 0
