"""Unified breadth/depth/frozen-memory benchmark over the synthetic environment."""
from __future__ import annotations

import hashlib
import json
from statistics import mean
from typing import Iterable

from .schema import ActorAnswer, BenchmarkAttempt, BenchmarkReport, Case, Task
from .verifier import EvidenceProvenanceVerifier

STRATEGIES = ("breadth", "depth", "frozen_memory")
MATCHED_BUDGET_UNITS = 2


def _memory_hash(memory: dict[str, str]) -> str:
    payload = json.dumps(memory, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _memory_from_public(tasks: Iterable[Task]) -> dict[str, str]:
    # A procedure, not patient facts: it is safe to freeze and replay across cases.
    return {
        "schema_version": "1",
        "procedure": "select_latest_valid_observation",
        "default_threshold": "130",
        "source_tasks": ",".join(sorted(task.task_id for task in tasks if task.split == "public")),
    }


def _answer(case: Case, task: Task, strategy: str, memory: dict[str, str]) -> ActorAnswer:
    observations = sorted(
        (event for event in case.events if event.code == task.code and event.valid_from <= task.as_of),
        key=lambda event: (event.observed_at, event.event_id),
    )
    if not observations:
        return ActorAnswer("unverified", (), 1, 1, 8)
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
    return {
        "case_count": len(cases),
        "task_count": len(tasks),
        "case_splits": dict(sorted(case_counts.items())),
        "task_splits": dict(sorted(task_counts.items())),
        "case_disjoint": True,
        "evaluation_splits": ["hidden", "temporal_holdout", "drift"],
        "sealed_public_count": task_counts.get("public", 0),
    }


def run_benchmark(cases: tuple[Case, ...], tasks: tuple[Task, ...], *, seed: int) -> BenchmarkReport:
    public_tasks = tuple(task for task in tasks if task.split == "public")
    exploration_compute_units = len(public_tasks)
    memory = _memory_from_public(public_tasks)
    before = _memory_hash(memory)
    by_case = {case.case_id: case for case in cases}
    verifier = EvidenceProvenanceVerifier()
    attempts: list[BenchmarkAttempt] = []
    for strategy in STRATEGIES:
        for task in tasks:
            if task.split == "public":
                continue
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
                    human_cost=round(answer.review_seconds * 0.2 + answer.compute_units * 0.05, 2),
                    negative_transfer=int(strategy == "frozen_memory" and task.split == "drift" and result.status != "pass"),
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
            "total_compute_units": float(exploration_compute_units + sum(row.compute_units for row in rows)),
            "human_cost": round(sum(row.human_cost for row in rows), 2),
            "total_human_cost": round(sum(row.human_cost for row in rows) + exploration_compute_units * 0.05, 2),
            "negative_transfer": float(sum(row.negative_transfer for row in rows)),
        }
    after = _memory_hash(memory)
    return BenchmarkReport(
        seed, tuple(attempts), aggregates, before, after, split_summary(cases, tasks)
    )


def assert_case_disjoint(tasks: Iterable[Task]) -> None:
    seen: dict[str, str] = {}
    for task in tasks:
        previous = seen.setdefault(task.case_id, task.split)
        if previous != task.split:
            raise AssertionError(f"case {task.case_id} appears in {previous} and {task.split}")
