"""
ACTS Runner Secure Execution Engine
Menjalankan pytest per level berdasarkan acts_compliance_matrix.json dan menghasilkan laporan terverifikasi.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ------------------------------------------------------------------------------
# Logging Configuration
# ------------------------------------------------------------------------------
logger = logging.getLogger("fastra_core.acts_runner")
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
)


# ------------------------------------------------------------------------------
# 1. LAYER DTO & CONFIGURATION MATRIX VALIDATOR
# ------------------------------------------------------------------------------
class ACTSLevelDTO:
    """Validator data transfer object untuk memastikan kepatuhan schema matriks."""

    def __init__(self, level_id: str, raw_data: Dict[str, Any]) -> None:
        self.level_id = str(level_id).strip()
        if not self.level_id:
            raise ValueError("level_id_cannot_be_empty")

        self.name = str(raw_data.get("name", "")).strip()
        if not self.name:
            raise ValueError(f"level_name_missing_for_{self.level_id}")

        raw_files = raw_data.get("test_files", [])
        if not isinstance(raw_files, list):
            raise ValueError(f"test_files_must_be_a_list_for_{self.level_id}")

        self.test_files: List[str] = []
        for file_path in raw_files:
            clean_path = str(file_path).strip()
            if clean_path:
                # Mencegah Path Traversal Attack
                if ".." in clean_path or clean_path.startswith("/") or clean_path.startswith("\\"):
                    raise ValueError(f"malicious_path_traversal_attempt_detected: {clean_path}")
                self.test_files.append(clean_path)

        try:
            self.required_pass_rate = float(raw_data.get("required_pass_rate", 100.0))
        except (ValueError, TypeError) as exc:
            raise ValueError(f"invalid_required_pass_rate_format_for_{self.level_id}") from exc

        if not 0.0 <= self.required_pass_rate <= 100.0:
            raise ValueError(f"required_pass_rate_out_of_bounds_for_{self.level_id}")

        try:
            self.critical_count = int(raw_data.get("critical_count", 0))
            self.high_count = int(raw_data.get("high_count", 0))
            self.medium_count = int(raw_data.get("medium_count", 0))
            self.low_count = int(raw_data.get("low_count", 0))
        except (ValueError, TypeError) as exc:
            raise ValueError(f"invalid_count_format_for_{self.level_id}") from exc


# ------------------------------------------------------------------------------
# 2. LAYER DOMAIN MODEL & SECURE REPORT ENTITIES
# ------------------------------------------------------------------------------
class TestExecutionResultDomain:
    """Model domain murni penyimpan status eksekusi suite testing terisolasi."""

    def __init__(self, passed: int, failed: int, errors: int, skipped: int) -> None:
        self.passed = int(passed)
        self.failed = int(failed)
        self.errors = int(errors)
        self.skipped = int(skipped)
        self.total = self.passed + self.failed + self.errors

    def calculate_pass_rate(self) -> float:
        if self.total <= 0:
            return 0.0
        return round((self.passed / self.total) * 100.0, 2)

    def is_condition_met(self, required_rate: float) -> bool:
        # Fail-fast: jika ada failed atau error, kondisi tidak terpenuhi
        if self.failed > 0 or self.errors > 0:
            return False
        return self.calculate_pass_rate() >= required_rate


class LevelReportDomain:
    """Model entitas laporan bisnis per tingkat kepatuhan (Compliance Levels)."""

    def __init__(self, dto: ACTSLevelDTO, result: TestExecutionResultDomain) -> None:
        self.level_id = dto.level_id
        self.name = dto.name
        self.passed = result.passed
        self.failed = result.failed
        self.errors = result.errors
        self.total = result.total
        self.pass_rate = result.calculate_pass_rate()
        self.required_pass_rate = dto.required_pass_rate
        self.condition_met = result.is_condition_met(dto.required_pass_rate)
        self.critical_count = dto.critical_count
        self.high_count = dto.high_count
        self.medium_count = dto.medium_count
        self.low_count = dto.low_count

    def to_dict_record(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "total": self.total,
            "pass_rate": self.pass_rate,
            "required_pass_rate": self.required_pass_rate,
            "condition_met": self.condition_met,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
        }


# ------------------------------------------------------------------------------
# 3. CORE ISOLATED AUTOMATION ENGINE LAYER
# ------------------------------------------------------------------------------
class ACTSExecutorEngine:
    """Mesin utama pengeksekusi sub-proses pengujian aman dengan isolasi berkas laporan json."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir

    def execute_suite(self, test_files: List[str]) -> TestExecutionResultDomain:
        if not test_files:
            return TestExecutionResultDomain(passed=0, failed=0, errors=0, skipped=0)

        # Nama berkas laporan acak UUID untuk menghindari race condition / write collision
        tmp_report = self.base_dir / f"tmp_pytest_{uuid.uuid4().hex}.json"

        # Menggunakan pytest-json-report untuk parsing yang andal
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "--json-report",
            f"--json-report-file={tmp_report}",
            "-q",
            "--tb=no",
            "--disable-warnings",
        ] + test_files

        try:
            # shell=False untuk mencegah command injection
            subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.base_dir,
                check=False,
                timeout=300,  # batas 5 menit anti-hang
            )

            if not tmp_report.exists():
                logger.error("Pytest report file not found after execution")
                return TestExecutionResultDomain(passed=0, failed=0, errors=1, skipped=0)

            raw_report_data = json.loads(tmp_report.read_text(encoding="utf-8"))
            summary = raw_report_data.get("summary", {})

            return TestExecutionResultDomain(
                passed=summary.get("passed", 0),
                failed=summary.get("failed", 0),
                errors=summary.get("error", 0),
                skipped=summary.get("skipped", 0),
            )

        except subprocess.TimeoutExpired:
            logger.error("Pytest execution timed out after 300 seconds")
            return TestExecutionResultDomain(passed=0, failed=0, errors=1, skipped=0)
        except Exception as exc:
            logger.exception("Unexpected error during test suite execution: %s", exc)
            return TestExecutionResultDomain(passed=0, failed=0, errors=1, skipped=0)
        finally:
            # Bersihkan file sementara
            if tmp_report.exists():
                try:
                    os.remove(tmp_report)
                except OSError as exc:
                    logger.warning("Failed to remove temporary report file %s: %s", tmp_report, exc)


# ------------------------------------------------------------------------------
# 4. ORCHESTRATION PIPELINE CONTROL (MAIN)
# ------------------------------------------------------------------------------
def main() -> None:
    current_dir = Path(__file__).parent
    matrix_file = current_dir / "acts_compliance_matrix.json"
    out_file = current_dir / "acts_report.json"

    if not matrix_file.exists():
        logger.error("Matrix file missing at %s", matrix_file)
        sys.exit(1)

    try:
        matrix_raw = json.loads(matrix_file.read_text(encoding="utf-8-sig"))
        raw_levels = matrix_raw.get("levels", {})
        if not isinstance(raw_levels, dict):
            raise ValueError("'levels' must be a dictionary")
    except Exception as exc:
        logger.error("Error reading compliance matrix: %s", exc)
        sys.exit(1)

    executor_engine = ACTSExecutorEngine(base_dir=current_dir)

    final_report: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "runner_version": "1.0.0",
        "results": {},
    }

    total_global_pass = 0
    total_global_tests = 0
    level_count = 0

    for level_key, level_payload in raw_levels.items():
        try:
            if not isinstance(level_payload, dict):
                raise ValueError("level_payload_must_be_dict")
            level_dto = ACTSLevelDTO(level_id=str(level_key), raw_data=level_payload)
        except ValueError as exc:
            logger.error("Configuration Compliance Error: %s", exc)
            continue

        logger.info("=== %s - %s ===", level_dto.level_id, level_dto.name)

        execution_domain = executor_engine.execute_suite(level_dto.test_files)
        report_domain = LevelReportDomain(dto=level_dto, result=execution_domain)

        logger.info(
            "Passed: %d, Failed: %d, Errors: %d, Total: %d, Pass Rate: %.1f%%",
            report_domain.passed,
            report_domain.failed,
            report_domain.errors,
            report_domain.total,
            report_domain.pass_rate,
        )
        logger.info(
            "Required: %.1f%%, Condition Met: %s",
            report_domain.required_pass_rate,
            report_domain.condition_met,
        )

        final_report["results"][level_dto.level_id] = report_domain.to_dict_record()

        total_global_pass += report_domain.passed
        total_global_tests += report_domain.total
        level_count += 1

    # Hitung agregat global tanpa zero coercion
    global_pass_rate = 0.0
    if total_global_tests > 0:
        global_pass_rate = round((total_global_pass / total_global_tests) * 100.0, 2)

    final_report["summary"] = {
        "total_tests": total_global_tests,
        "total_passed": total_global_pass,
        "overall_pass_rate": global_pass_rate,
        "levels": level_count,
    }

    try:
        out_file.write_text(json.dumps(final_report, indent=2), encoding="utf-8")
        logger.info("Report saved to %s", out_file)
    except OSError as exc:
        logger.error("Error compiling output JSON report: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()