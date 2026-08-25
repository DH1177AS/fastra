
import json
from pathlib import Path
from fastra_core.compiler.ccm_validator import run_pipeline


def test_demo_fixture_ready():
    raw = Path("tests/fixtures/ccm_demo_complete.json").read_text(encoding="utf-8")
    result = run_pipeline(raw)
    report = result["ConstructionCanonicalModel"]["ValidationReport"]
    assert report["OverallStatus"].startswith("READY")
    assert report["BlockingIssuesCount"] == 0
    assert report["NeedsClientInputCount"] == 0
    assert report["NeedsClientConfirmationCount"] == 0
