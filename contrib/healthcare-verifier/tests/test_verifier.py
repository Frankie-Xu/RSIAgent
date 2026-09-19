from dataclasses import replace
import inspect

import pytest

from rsiaagent_healthcare_fixture import ActorAnswer, EvidenceProvenanceVerifier, build_cases, build_tasks


def _fixture():
    cases = build_cases()
    tasks = build_tasks(cases)
    return cases, tasks, {case.case_id: case for case in cases}, {task.task_id: task for task in tasks}


def test_verifier_reconstructs_from_citation_without_private_trace():
    _, tasks, by_case, by_task = _fixture()
    task = by_task["TASK-SYN-CASE-004"]
    case = by_case[task.case_id]
    latest = max(case.events[:2], key=lambda event: event.observed_at)
    expected = "elevated" if latest.value >= task.threshold else "within_range"
    result = EvidenceProvenanceVerifier().verify(
        task, case, ActorAnswer(expected, (latest.event_id,), 1, compute_units=1, review_seconds=2)
    )
    assert result.status == "pass"
    assert result.recomputed_conclusion == expected
    assert result.evidence_coverage == 1.0


def test_verifier_rejects_future_evidence_for_temporal_holdout():
    _, tasks, by_case, by_task = _fixture()
    task = next(task for task in tasks if task.split == "temporal_holdout")
    case = by_case[task.case_id]
    future = max(case.events[:2], key=lambda event: event.observed_at)
    result = EvidenceProvenanceVerifier().verify(
        task, case, ActorAnswer("elevated", (future.event_id,), 1, 1, 2)
    )
    assert result.status == "wrong"
    assert result.temporal_validity_ok is False
    assert any("future evidence" in finding for finding in result.findings)


def test_verifier_rejects_cross_case_and_unknown_citations():
    cases, tasks, by_case, by_task = _fixture()
    task = by_task["TASK-SYN-CASE-005"]
    foreign = by_case["SYN-CASE-004"].events[0].event_id
    result = EvidenceProvenanceVerifier().verify(
        task, by_case[task.case_id], ActorAnswer("within_range", (foreign, "missing"), 1, 1, 2)
    )
    assert result.status == "wrong"
    assert any("unknown evidence" in finding for finding in result.findings)
    assert any("cross-case" in finding for finding in result.findings)


def test_verifier_rejects_stale_conclusion_even_with_valid_provenance():
    _, tasks, by_case, by_task = _fixture()
    task = by_task["TASK-SYN-CASE-006"]
    case = by_case[task.case_id]
    latest = max(case.events[:2], key=lambda event: event.observed_at)
    wrong = "within_range" if latest.value >= task.threshold else "elevated"
    result = EvidenceProvenanceVerifier().verify(
        task, case, ActorAnswer(wrong, (latest.event_id,), 1, 1, 2)
    )
    assert result.status == "wrong"
    assert any("conclusion mismatch" in finding for finding in result.findings)


def test_verifier_api_has_no_private_trace_or_memory_input():
    parameters = inspect.signature(EvidenceProvenanceVerifier.verify).parameters
    assert "private_trace" not in parameters
    assert "private_memory" not in parameters
    assert "transcript" not in parameters
    assert set(parameters) == {"self", "task", "case", "answer"}
    with pytest.raises(TypeError):
        ActorAnswer("within_range", (), 1, 1, 1, private_reasoning="hidden")


def test_verifier_rejects_untrusted_provenance():
    _, tasks, by_case, by_task = _fixture()
    task = by_task["TASK-SYN-CASE-004"]
    case = by_case[task.case_id]
    latest = max(case.events[:2], key=lambda event: event.observed_at)
    tampered = replace(latest, provenance="file:///production/patient-record")
    tampered_case = replace(
        case,
        events=tuple(tampered if event.event_id == tampered.event_id else event for event in case.events),
    )
    result = EvidenceProvenanceVerifier().verify(
        task,
        tampered_case,
        ActorAnswer("elevated", (tampered.event_id,), 1, 1, 2),
    )
    assert result.status == "wrong"
    assert result.provenance_ok is False
    assert any("provenance" in finding for finding in result.findings)


def test_verifier_rejects_expired_evidence():
    _, tasks, by_case, by_task = _fixture()
    task = by_task["TASK-SYN-CASE-004"]
    case = by_case[task.case_id]
    latest = max(case.events[:2], key=lambda event: event.observed_at)
    expired = replace(latest, valid_to=min(event.observed_at for event in case.events[:2]))
    expired_case = replace(
        case,
        events=tuple(expired if event.event_id == expired.event_id else event for event in case.events),
    )
    result = EvidenceProvenanceVerifier().verify(
        task, expired_case, ActorAnswer("elevated", (expired.event_id,), 1, 1, 2)
    )
    assert result.status == "wrong"
    assert any("expired evidence" in finding for finding in result.findings)
