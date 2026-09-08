"""
ACTS Compliance Reporter Engine
Membaca dan memproses berkas acts_report.json untuk menghasilkan laporan kepatuhan terstruktur.
Enforced with Decimal Precision, Strict Fail-Fast IO Validation, and Data Sanitization.
"""

from __future__ import annotations

import json
import logging
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, Optional

# ------------------------------------------------------------------------------
# Logging Configuration
# ------------------------------------------------------------------------------
logger = logging.getLogger("fastra_core.generate_compliance_report")
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
)

REPORT_FILE: Path = Path(__file__).parent.resolve() / "acts_report.json"

# ------------------------------------------------------------------------------
# 1. LAYER DOMAIN MODEL (SNAKE_CASE & NO UI)
# ------------------------------------------------------------------------------


class LevelComplianceResultDomain:
    """Model representasi bisnis murni untuk mengevaluasi data kepatuhan per level."""

    def __init__(self, level_id: str, raw_data: Dict[str, Any]) -> None:
        self.level_id = str(level_id).strip()
        if not self.level_id:
            raise ValueError("level_id_cannot_be_empty")

        self.name = str(raw_data.get("name", "")).strip()

        # Validasi angka dengan ketat (tidak menerima nilai negatif atau non-integer)
        try:
            self.passed = int(raw_data.get("passed", 0))
            self.total = int(raw_data.get("total", 0))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"invalid_integer_fields_for_{self.level_id}") from exc

        if self.passed < 0 or self.total < 0:
            raise ValueError(f"negative_counts_not_allowed_for_{self.level_id}")

        # Parsing Decimal dengan validasi
        try:
            self.pass_rate = Decimal(str(raw_data.get("pass_rate", "0.00")))
            self.required_pass_rate = Decimal(str(raw_data.get("required_pass_rate", "0.00")))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ValueError(f"invalid_decimal_rate_for_{self.level_id}") from exc

        if not self.pass_rate.is_finite() or not self.required_pass_rate.is_finite():
            raise ValueError(f"non_finite_decimal_rate_for_{self.level_id}")

        self.condition_met = bool(raw_data.get("condition_met", False))

    def get_status_string(self) -> str:
        return "PASS" if self.condition_met else "FAIL"


class GlobalComplianceSummaryDomain:
    """Model representasi bisnis murni untuk mengevaluasi status kepatuhan global sistem (CES)."""

    def __init__(self, summary_data: Dict[str, Any], all_levels_met: bool) -> None:
        try:
            self.total_tests = int(summary_data.get("total_tests", 0))
            self.total_passed = int(summary_data.get("total_passed", 0))
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid_summary_integer_fields") from exc

        if self.total_tests < 0 or self.total_passed < 0:
            raise ValueError("summary_counts_must_be_non_negative")

        try:
            self.overall_pass_rate = Decimal(str(summary_data.get("overall_pass_rate", "0.00")))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ValueError("invalid_overall_pass_rate") from exc

        if not self.overall_pass_rate.is_finite():
            raise ValueError("overall_pass_rate_must_be_finite")

        self.all_levels_met = all_levels_met

    def determine_compliance_status(self) -> str:
        # Batas ambang kelulusan penuh (95.00%) dievaluasi menggunakan presisi objek Decimal
        compliance_threshold = Decimal("95.00")

        if self.all_levels_met and self.overall_pass_rate >= compliance_threshold:
            return "CES FULL COMPLIANT"
        if self.all_levels_met:
            return "CES COMPLIANT (per level)"
        return "NOT FULLY COMPLIANT"


# ------------------------------------------------------------------------------
# 2. INTERACTION CONTROLLER / ORCHESTRATOR
# ------------------------------------------------------------------------------
def main() -> None:
    if not REPORT_FILE.is_file():
        logger.error("acts_report.json not found at %s. Run acts_runner.py first.", REPORT_FILE)
        sys.exit(1)

    try:
        raw_content = REPORT_FILE.read_text(encoding="utf-8")
        if not raw_content.strip():
            raise ValueError("report_file_is_empty")
        report: Dict[str, Any] = json.loads(raw_content)
    except Exception as exc:
        logger.exception("Error reading or parsing reports payload: %s", exc)
        sys.exit(1)

    # Validasi Fail-Fast struktur dasar skema JSON
    required_keys = {"results", "summary", "timestamp"}
    if not required_keys.issubset(report.keys()):
        logger.error("Invalid report schema: missing required keys %s", required_keys)
        sys.exit(1)

    # Sanitasi: pastikan 'results' adalah dict
    results_payload = report.get("results")
    if not isinstance(results_payload, dict):
        logger.error("Invalid report schema: 'results' must be a dictionary")
        sys.exit(1)

    # --- Output laporan dengan logging terstruktur ---
    logger.info("=" * 60)
    logger.info("FASTRA ACTS Compliance Report")
    logger.info("Generated: %s", report.get("timestamp", ""))
    logger.info("=" * 60)

    all_levels_met = True
    for level_id, level_data in results_payload.items():
        if not isinstance(level_data, dict):
            logger.warning("Skipping non-dict level data for %s", level_id)
            continue

        try:
            domain_level = LevelComplianceResultDomain(level_id, level_data)
        except ValueError as exc:
            logger.error("Invalid level data for %s: %s", level_id, exc)
            all_levels_met = False
            continue

        if not domain_level.condition_met:
            all_levels_met = False

        logger.info(
            "\n%s (%s): %s\n  Passed: %d/%d  Pass Rate: %s%%  Required: %s%%",
            domain_level.level_id,
            domain_level.name,
            domain_level.get_status_string(),
            domain_level.passed,
            domain_level.total,
            domain_level.pass_rate,
            domain_level.required_pass_rate,
        )

    logger.info("\n" + "=" * 60)

    try:
        summary_payload = report.get("summary", {})
        if not isinstance(summary_payload, dict):
            raise ValueError("summary_must_be_dict")
        global_summary = GlobalComplianceSummaryDomain(summary_payload, all_levels_met)
    except ValueError as exc:
        logger.exception("Error processing summary: %s", exc)
        sys.exit(1)

    logger.info(
        "Summary: %d/%d passed (%s%%)",
        global_summary.total_passed,
        global_summary.total_tests,
        global_summary.overall_pass_rate,
    )
    logger.info("=" * 60)
    logger.info(global_summary.determine_compliance_status())


if __name__ == "__main__":
    main()