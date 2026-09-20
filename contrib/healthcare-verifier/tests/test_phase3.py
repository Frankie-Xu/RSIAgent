from dataclasses import replace
import json
import subprocess
import sys
from pathlib import Path

import pytest

from rsiaagent_healthcare_fixture import build_cases, build_tasks, ActorAnswer, EvidenceProvenanceVerifier
from rsiaagent_healthcare_fixture.benchmark import _answer, run_benchmark, split_summary


@pytest.mark.parametrize("mutation", ["future", "backfill", "source", "foreign", "duplicate", "nan", "inf", "omission"])
def test_reject_corrupted_source(mutation):
    case = build_cases()[4]
    task = build_tasks((case,))[0]
    event = case.events[1]
    change = {
        "future": {"observed_at": "2099-01-01"},
        "backfill": {"observed_at": "2099-01-01", "valid_from": "2020-01-01"},
        "source": {"provenance": "synthetic://generator/20260919/forged/observation-2"},
        "foreign": {"case_id": "SYN-CASE-005"},
        "nan": {"value": float("nan")}, "inf": {"value": float("inf")},
    }.get(mutation, {})
    events = (case.events[0], replace(event, **change), case.events[2])
    if mutation == "duplicate":
        events += (event,)
    if mutation == "omission":
        events = (event,)
    answer = ActorAnswer("within_range", (event.event_id,), 1, 1, 2)
    result = EvidenceProvenanceVerifier().verify(task, replace(case, events=events), answer)
    assert result.status == "wrong"
    assert not result.provenance_ok


def test_future_observation_is_excluded_even_with_backdated_validity():
    case = build_cases()[4]
    task = build_tasks((case,))[0]
    event = replace(case.events[1], observed_at="2099-01-01", valid_from="2020-01-01")
    case = replace(case, events=(case.events[0], event))
    answer = _answer(case, task, "depth", {})
    assert answer.evidence_ids == (case.events[0].event_id,)


@pytest.mark.parametrize("budget", [0, 1, 2])
def test_depth_execution_stops_at_cap(budget):
    case = build_cases()[4]
    task = build_tasks((case,))[0]
    case = replace(case, events=case.events[:2] * 10)
    answer = _answer(case, task, "depth", {}, budget=budget)
    assert answer.compute_units == budget
    assert answer.interaction_units == budget


def test_split_admission_rejects_overlap_and_mismatch():
    cases = build_cases()
    tasks = build_tasks(cases)
    with pytest.raises(AssertionError):
        split_summary(cases, tasks + (replace(tasks[0], split="hidden"),))
    with pytest.raises(ValueError):
        split_summary(cases, (replace(tasks[0], split="hidden"),) + tasks[1:])


def test_negative_transfer_is_paired_baseline_difference():
    cases = build_cases()
    report = run_benchmark(cases, build_tasks(cases), seed=20260919)
    for row in report.attempts:
        assert row.quality_delta == row.quality - row.baseline_quality
        assert row.negative_transfer == int(row.strategy == "frozen_memory" and row.quality_delta < 0)


def test_real_upstream_contract_and_private_input_rejection(tmp_path):
    from core.trace import ArtifactSink
    from core.verifier import Findings
    from rsiaagent_healthcare_fixture.runtime_bridge import inspect_candidate
    case = build_cases()[4]
    task = build_tasks((case,))[0]
    answer = _answer(case, task, "depth", {})
    result, findings = inspect_candidate(task, case, answer, sink=ArtifactSink(str(tmp_path)))
    assert result.status == "pass" and isinstance(findings, Findings)
    record = json.loads((tmp_path / "iter_01/verify2.json").read_text())
    assert record["transcript"] == [] and record["items"][0]["status"] == "met"
    saved = json.loads((tmp_path / "result.json").read_text())
    assert len(saved["task_identity"]["sha256"]) == 64
    assert saved["official_score"] is None
    with pytest.raises(TypeError):
        inspect_candidate(task, case, answer, sink=None, memory="private")
    object.__setattr__(answer, "reasoning", "PRIVATE_SENTINEL")
    with pytest.raises(ValueError, match="undeclared"):
        inspect_candidate(task, case, answer, sink=None)
    assert "PRIVATE_SENTINEL" not in (tmp_path / "result.json").read_text()


def test_checked_in_json_is_byte_reproducible(tmp_path):
    root = Path(__file__).resolve().parents[1]
    subprocess.run([sys.executable, str(root / "tools/generate_fixture.py"),
                    "--output", str(tmp_path)], check=True)
    for name in ("synthetic_cases.json", "benchmark_report.json"):
        assert (tmp_path / name).read_bytes() == (root / "fixtures" / name).read_bytes()
