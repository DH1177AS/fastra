"""
ACTS Runner
Menjalankan pytest per level berdasarkan acts_compliance_matrix.json dan menghasilkan laporan.
"""
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

MATRIX_FILE = Path(__file__).parent / "acts_compliance_matrix.json"

def run_pytest(test_files):
    if not test_files:
        return 0, 0, 0, []
    cmd = [sys.executable, "-m", "pytest", "-q", "--tb=no", "--disable-warnings"] + test_files
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
    output = result.stdout + result.stderr
    # Parse summary line dengan regex: "X passed, Y failed, Z errors" atau "X passed" saja
    passed = failed = errors = 0
    match = re.search(r'(\d+)\s+passed', output)
    if match:
        passed = int(match.group(1))
    match = re.search(r'(\d+)\s+failed', output)
    if match:
        failed = int(match.group(1))
    match = re.search(r'(\d+)\s+errors?', output)
    if match:
        errors = int(match.group(1))

    # Jika tidak ada summary, anggap collected 0, tapi tampilkan output pendek
    if passed == 0 and failed == 0 and errors == 0:
        # cari "collected 0 items" atau error
        if "collected 0 items" in output:
            print(f"  No tests collected. Output snippet:\n{output[:500]}")
        elif "ERROR" in output:
            print(f"  Pytest error. Output snippet:\n{output[:500]}")
    return passed, failed, errors, output.splitlines()

def main():
    matrix = json.loads(MATRIX_FILE.read_text(encoding="utf-8-sig"))
    levels = matrix["levels"]
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "runner_version": "1.0.0",
        "results": {}
    }
    total_pass = 0
    total_tests = 0
    for level_id, level_data in levels.items():
        print(f"\n=== {level_id} - {level_data['name']} ===")
        passed, failed, errors, output_lines = run_pytest(level_data["test_files"])
        total = passed + failed + errors
        pass_rate = (passed / total * 100) if total > 0 else 0.0
        required = level_data["required_pass_rate"]
        passed_condition = pass_rate >= required and failed == 0 and errors == 0
        print(f"Passed: {passed}, Failed: {failed}, Errors: {errors}, Total: {total}, Pass Rate: {pass_rate:.1f}%")
        print(f"Required: {required}%, Condition Met: {passed_condition}")
        report["results"][level_id] = {
            "name": level_data["name"],
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "total": total,
            "pass_rate": round(pass_rate, 2),
            "required_pass_rate": required,
            "condition_met": passed_condition,
            "critical_count": level_data.get("critical_count", 0),
            "high_count": level_data.get("high_count", 0),
            "medium_count": level_data.get("medium_count", 0),
            "low_count": level_data.get("low_count", 0),
        }
        total_pass += passed
        total_tests += total
    report["summary"] = {
        "total_tests": total_tests,
        "total_passed": total_pass,
        "overall_pass_rate": round((total_pass / total_tests * 100) if total_tests > 0 else 0.0, 2),
        "levels": len(levels)
    }
    out_file = Path(__file__).parent / "acts_report.json"
    out_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nReport saved to {out_file}")

if __name__ == "__main__":
    main()

