"""Unified breadth/depth/frozen-memory benchmark over the synthetic environment."""
from __future__ import annotations

import hashlib
import json
from statistics import mean
from typing import Iterable

from .schema import ActorAnswer, BenchmarkAttempt, BenchmarkReport, Case, Task
from .verifier import EvidenceProvenanceVerifier, available

STRATEGIES = ("breadth", "depth", "frozen_memory")
MATCHED_BUDGET_UNITS = 2


def _memory_hash(memory: dict[str, str]) -> str:
    payload = json.dumps(memory, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _memory_from_public(cases, tasks, verifier):
    """Actually execute public practice and record its read/check counts."""
    public = tuple(task for task in tasks if task.split == "public")
    by_case = {case.case_id: case for case in cases}
    counts = {"setup_calls": 1, "actor_calls": 0, "verifier_calls": 0,
              "actor_reads": 0, "verification_records": 0}
    for task in public:
        counts["actor_calls"] += 1
        answer = _answer(by_case[task.case_id], task, "depth", {})
        counts["actor_reads"] += answer.interaction_units
        counts["verifier_calls"] += 1
        result = verifier.verify(task, by_case[task.case_id], answer)
        counts["verification_records"] += len(by_case[task.case_id].events)
        if result.status != "pass":
            raise ValueError("public setup practice rejected")
    thresholds = {task.threshold for task in public}
    if len(thresholds) != 1:
        raise ValueError("public setup needs one observed task threshold")
    return {
        "schema_version": "1",
        "procedure": "select_latest_valid_observation",
        "default_threshold": format(next(iter(thresholds)), "g"),
        "source_tasks": ",".join(sorted(task.task_id for task in public)),
    }, counts


def _answer(case: Case, task: Task, strategy: str, memory: dict[str, str],
            *, budget: int = MATCHED_BUDGET_UNITS) -> ActorAnswer:
    if type(budget) is not int or budget < 0:
        raise ValueError("budget must be a nonnegative integer")
    if strategy not in STRATEGIES:
        raise ValueError(f"unknown strategy: {strategy}")
    observations = sorted(
        (event for event in case.events if event.code == task.code and available(event, task.as_of)),
        key=lambda event: (event.observed_at, event.event_id),
    )
    # Simulated indexed metadata is free; each returned value costs one read.
    # Admission happens BEFORE reading values, including for depth exploration.
    ordered = observations[-1:] if strategy == "frozen_memory" else observations
    reads = []
    limit = budget if strategy == "depth" else min(budget, 1)
    for event in ordered:
        if len(reads) >= limit:
            break
        reads.append(event)
    observations = reads
    if not observations:
        return ActorAnswer("unverified", (), 0, 0, 8)
    if strategy == "breadth":
        chosen = observations[0]
        threshold = task.threshold
        interaction = 1
        units = 1
        review = 4
    elif strategy == "depth":
        chosen = observations[-1]
        threshold = task.threshold
        interaction = len(observations)
        units = len(observations)
        review = 3
    elif strategy == "frozen_memory":
        chosen = observations[-1]
        # The frozen procedure is useful, but its old threshold creates a deliberate
        # negative-transfer case on drift tasks. The memory remains immutable.
        threshold = float(memory["default_threshold"])
        interaction = 1
        units = 1
        review = 2
    else:
        raise ValueError(f"unknown strategy: {strategy}")
    conclusion = "elevated" if chosen.value >= threshold else "within_range"
    return ActorAnswer(conclusion, (chosen.event_id,), interaction, units, review)


def split_summary(cases: Iterable[Case], tasks: Iterable[Task]) -> dict[str, object]:
    cases = tuple(cases)
    tasks = tuple(tasks)
    case_counts: dict[str, int] = {}
    task_counts: dict[str, int] = {}
    for case in cases:
        case_counts[case.split] = case_counts.get(case.split, 0) + 1
    for task in tasks:
        task_counts[task.split] = task_counts.get(task.split, 0) + 1
    assert_case_disjoint(tasks)
    if len({c.case_id for c in cases}) != len(cases) or len({t.task_id for t in tasks}) != len(tasks):
        raise ValueError("duplicate case/task identity")
    by_case = {c.case_id: c for c in cases}
    for task in tasks:
        if task.case_id not in by_case or by_case[task.case_id].split != task.split:
            raise ValueError("case/task split mismatch")
        if task.split not in {"public", "hidden", "temporal_holdout", "drift"}:
            raise ValueError("unknown split")
    return {
        "case_count": len(cases),
        "task_count": len(tasks),
        "case_splits": dict(sorted(case_counts.items())),
        "task_splits": dict(sorted(task_counts.items())),
        "case_disjoint": True,
        "evaluation_splits": ["hidden", "temporal_holdout", "drift"],
        "public_development_count": task_counts.get("public", 0),
        "seal_scope": "logical development/evaluation separation; published synthetic cases are not secret",
    }


def run_benchmark(cases: tuple[Case, ...], tasks: tuple[Task, ...], *, seed: int) -> BenchmarkReport:
    summary = split_summary(cases, tasks)
    verifier = EvidenceProvenanceVerifier(seed=seed)
    memory, setup_counts = _memory_from_public(cases, tasks, verifier)
    exploration_compute_units = setup_counts["actor_reads"] + setup_counts["verification_records"]
    before = _memory_hash(memory)
    by_case = {case.case_id: case for case in cases}
    baseline = {}
    baseline_runs = {}
    for task in tasks:
        if task.split != "public":
            answer = _answer(by_case[task.case_id], task, "depth", {})
            result = verifier.verify(task, by_case[task.case_id], answer)
            baseline_runs[task.task_id] = (answer, result)
            baseline[task.task_id] = float(result.status == "pass")
    attempts: list[BenchmarkAttempt] = []
    for strategy in STRATEGIES:
        for task in tasks:
            if task.split == "public":
                continue
            if strategy == "depth":
                answer, result = baseline_runs[task.task_id]
            else:
                answer = _answer(by_case[task.case_id], task, strategy, memory)
                result = verifier.verify(task, by_case[task.case_id], answer)
            attempts.append(
                BenchmarkAttempt(
                    strategy=strategy,
                    task_id=task.task_id,
                    split=task.split,
                    status=result.status,
                    quality=1.0 if result.status == "pass" else 0.0,
                    evidence_coverage=result.evidence_coverage,
                    interaction_units=answer.interaction_units,
                    review_seconds=answer.review_seconds,
                    compute_units=answer.compute_units,
                    matched_budget_units=MATCHED_BUDGET_UNITS,
                    unused_budget_units=MATCHED_BUDGET_UNITS - answer.compute_units,
                    human_cost=round(answer.review_seconds * 0.2, 2),
                    negative_transfer=int(strategy == "frozen_memory" and baseline[task.task_id] > float(result.status == "pass")),
                    baseline_quality=baseline[task.task_id],
                    quality_delta=float(result.status == "pass") - baseline[task.task_id],
                    verification_compute_units=len(by_case[task.case_id].events),
                )
            )
    aggregates: dict[str, dict[str, float]] = {}
    for strategy in STRATEGIES:
        rows = [attempt for attempt in attempts if attempt.strategy == strategy]
        aggregates[strategy] = {
            "quality": mean(row.quality for row in rows),
            "evidence_coverage": mean(row.evidence_coverage for row in rows),
            "interaction_units": float(sum(row.interaction_units for row in rows)),
            "review_seconds": float(sum(row.review_seconds for row in rows)),
            "compute_units": float(sum(row.compute_units for row in rows)),
            "matched_budget_units": float(sum(row.matched_budget_units for row in rows)),
            "unused_budget_units": float(sum(row.unused_budget_units for row in rows)),
            "exploration_compute_units": float(exploration_compute_units),
            "verification_compute_units": float(sum(row.verification_compute_units for row in rows)),
            "total_compute_units": float(exploration_compute_units + sum(row.compute_units + row.verification_compute_units for row in rows)),
            "human_cost": round(sum(row.human_cost for row in rows), 2),
            "total_human_cost": round(sum(row.human_cost for row in rows), 2),
            "simulated_compute_cost": round((exploration_compute_units + sum(row.compute_units + row.verification_compute_units for row in rows)) * 0.05, 2),
            "mean_quality_delta": mean(row.quality_delta for row in rows),
            "negative_transfer": float(sum(row.negative_transfer for row in rows)),
        }
    after = _memory_hash(memory)
    return BenchmarkReport(
        seed, tuple(attempts), aggregates, before, after, summary, setup_counts
    )


def assert_case_disjoint(tasks: Iterable[Task]) -> None:
    seen: dict[str, str] = {}
    for task in tasks:
        previous = seen.setdefault(task.case_id, task.split)
        if previous != task.split:
            raise AssertionError(f"case {task.case_id} appears in {previous} and {task.split}")
