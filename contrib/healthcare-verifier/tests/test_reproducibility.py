import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from rsiaagent_healthcare_fixture import build_cases, build_tasks
from rsiaagent_healthcare_fixture import run_benchmark


def snapshot(seed):
    cases = build_cases(seed)
    payload = {
        "cases": [
            {
                "case_id": case.case_id,
                "split": case.split,
                "events": [event.as_public_dict() for event in case.events],
            }
            for case in cases
        ],
        "tasks": [task.__dict__ for task in build_tasks(cases)],
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def test_fixed_seed_is_byte_stable_and_seed_changes_fixture():
    assert snapshot(20260919) == snapshot(20260919)
    assert snapshot(20260919) != snapshot(20260920)


def test_fixture_contains_only_synthetic_provenance():
    for case in build_cases():
        assert case.synthetic_patient_id.startswith("SYN-")
        assert all(event.provenance.startswith("synthetic://") for event in case.events)


def test_checked_in_report_matches_recomputed_attempt_records():
    root = Path(__file__).resolve().parents[1]
    report = json.loads((root / "fixtures" / "benchmark_report.json").read_text())
    cases = build_cases(report["seed"])
    tasks = build_tasks(cases)
    expected = run_benchmark(cases, tasks, seed=report["seed"])
    assert report["attempt_count"] == len(expected.attempts)
    assert report["attempts"] == [asdict(attempt) for attempt in expected.attempts]
    assert report["aggregates"] == expected.aggregates
    assert report["split_summary"] == expected.split_summary
