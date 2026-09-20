"""Regenerate the checked-in synthetic fixture and benchmark report."""
from __future__ import annotations

import json
import argparse
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
SEED = 20260919
sys.path.insert(0, str(ROOT))

from rsiaagent_healthcare_fixture import build_cases, build_tasks, run_benchmark  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=FIXTURES)
    output = parser.parse_args().output
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
        "measurement": "synthetic deterministic proxies; matched caps, not equal actual cost",
        "baseline": "paired depth/no-memory with the same task and actor cap",
        "cost_model": {
            "exploration": "assumed setup charge: one unit per public task; no curriculum executed",
            "verification": "modeled one unit per candidate event, outside actor cap",
            "actor": "counted simulated value reads, maximum two per task",
            "human": "assigned review seconds times 0.2 arbitrary units, not measured",
            "compute": "simulated units times 0.05 arbitrary units, not monetary",
            "baseline_execution": "depth executes once; its cached result is reused for paired comparisons",
            "protocol_actor_reads": sum(a.interaction_units for a in report.attempts),
            "protocol_modeled_compute": sum(m["total_compute_units"] for m in report.aggregates.values()),
            "equal_actual_compute": False,
        },
        "seed": report.seed,
        "aggregates": report.aggregates,
        "attempts": [asdict(attempt) for attempt in report.attempts],
        "split_summary": report.split_summary,
        "frozen_memory_hash_before": report.frozen_memory_hash_before,
        "frozen_memory_hash_after": report.frozen_memory_hash_after,
        "attempt_count": len(report.attempts),
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "synthetic_cases.json").write_text(
        json.dumps(fixture, indent=2, sort_keys=True) + "\n"
    )
    (output / "benchmark_report.json").write_text(
        json.dumps(report_json, indent=2, sort_keys=True) + "\n"
    )


if __name__ == "__main__":
    main()
