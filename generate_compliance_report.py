"""
Generate Compliance Report dari acts_report.json.
"""
import json
from pathlib import Path

REPORT_FILE = Path(__file__).parent / "acts_report.json"

def main():
    if not REPORT_FILE.exists():
        print("acts_report.json not found. Run acts_runner.py first.")
        return
    report = json.loads(REPORT_FILE.read_text(encoding="utf-8"))
    print("=" * 60)
    print("FASTRA ACTS Compliance Report")
    print(f"Generated: {report['timestamp']}")
    print("=" * 60)
    for level_id, data in report["results"].items():
        status = "PASS" if data["condition_met"] else "FAIL"
        print(f"\n{level_id} ({data['name']}): {status}")
        print(f"  Passed: {data['passed']}/{data['total']}  Pass Rate: {data['pass_rate']}%  Required: {data['required_pass_rate']}%")
    print("\n" + "=" * 60)
    summary = report["summary"]
    print(f"Summary: {summary['total_passed']}/{summary['total_tests']} passed ({summary['overall_pass_rate']}%)")
    print("=" * 60)
    # Determine overall compliance
    all_met = all(level["condition_met"] for level in report["results"].values())
    if all_met and summary["overall_pass_rate"] >= 95:
        print("CES FULL COMPLIANT")
    elif all_met:
        print("CES COMPLIANT (per level)")
    else:
        print("NOT FULLY COMPLIANT")

if __name__ == "__main__":
    main()
