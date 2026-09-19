"""Regenerate the checked-in synthetic fixture and benchmark report."""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
SEED = 20260919
sys.path.insert(0, str(ROOT))

from rsiaagent_healthcare_fixture import build_cases, build_tasks, run_benchmark  # noqa: E402


def main() -> None:
    cases = build_cases(SEED)
    tasks = build_tasks(cases)
    fixture = {
        "schema_version": 1,
        "seed": SEED,
        "synthetic_only": True,
        "cases": [
            {
                "case_id": case.case_id,
                "synthetic_patient_id": case.synthetic_patient_id,
                "split": case.split,
                "events": [event.as_public_dict() for event in case.events],
            }
            for case in cases
        ],
        "tasks": [asdict(task) for task in tasks],
    }
    report = run_benchmark(cases, tasks, seed=SEED)
    report_json = {
        "seed": report.seed,
        "aggregates": report.aggregates,
        "attempts": [asdict(attempt) for attempt in report.attempts],
        "split_summary": report.split_summary,
        "frozen_memory_hash_before": report.frozen_memory_hash_before,
        "frozen_memory_hash_after": report.frozen_memory_hash_after,
        "attempt_count": len(report.attempts),
    }
    FIXTURES.mkdir(exist_ok=True)
    (FIXTURES / "synthetic_cases.json").write_text(
        json.dumps(fixture, indent=2, sort_keys=True) + "\n"
    )
    (FIXTURES / "benchmark_report.json").write_text(
        json.dumps(report_json, indent=2, sort_keys=True) + "\n"
    )


if __name__ == "__main__":
    main()
