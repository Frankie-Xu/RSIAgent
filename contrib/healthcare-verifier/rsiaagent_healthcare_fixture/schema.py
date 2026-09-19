"""Small, immutable schemas for synthetic RSIAgent healthcare experiments."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class Event:
    event_id: str
    case_id: str
    resource_type: str
    code: str
    value: float
    unit: str
    observed_at: str
    valid_from: str
    valid_to: str | None
    provenance: str
    cost_units: int = 1

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "case_id": self.case_id,
            "resource_type": self.resource_type,
            "code": self.code,
            "value": self.value,
            "unit": self.unit,
            "observed_at": self.observed_at,
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "provenance": self.provenance,
            "cost_units": self.cost_units,
        }


@dataclass(frozen=True)
class Case:
    case_id: str
    synthetic_patient_id: str
    events: tuple[Event, ...]
    split: str

    def event_map(self) -> dict[str, Event]:
        return {event.event_id: event for event in self.events}


@dataclass(frozen=True)
class Task:
    task_id: str
    case_id: str
    split: str
    as_of: str
    code: str
    threshold: float
    query: str


@dataclass(frozen=True)
class ActorAnswer:
    """Public answer surface; private reasoning is deliberately not represented."""

    conclusion: str
    evidence_ids: tuple[str, ...]
    interaction_units: int
    compute_units: int
    review_seconds: int


@dataclass(frozen=True)
class VerificationResult:
    status: str
    conclusion: str | None
    recomputed_conclusion: str | None
    findings: tuple[str, ...]
    evidence_coverage: float
    provenance_ok: bool
    temporal_validity_ok: bool


@dataclass(frozen=True)
class BenchmarkAttempt:
    strategy: str
    task_id: str
    split: str
    status: str
    quality: float
    evidence_coverage: float
    interaction_units: int
    review_seconds: int
    compute_units: int
    matched_budget_units: int
    unused_budget_units: int
    human_cost: float
    negative_transfer: int


@dataclass(frozen=True)
class BenchmarkReport:
    seed: int
    attempts: tuple[BenchmarkAttempt, ...]
    aggregates: Mapping[str, Mapping[str, float]]
    frozen_memory_hash_before: str
    frozen_memory_hash_after: str
    split_summary: Mapping[str, object]
