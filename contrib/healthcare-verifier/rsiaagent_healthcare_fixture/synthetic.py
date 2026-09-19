"""Deterministic synthetic FHIR/Synthea-style cases.

The values and identifiers are fabricated. They are not derived from patient data.
"""
from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Iterable

from .schema import Case, Event, Task

DEFAULT_SEED = 20260919


def _iso(day: date) -> str:
    return day.isoformat()


def build_cases(seed: int = DEFAULT_SEED) -> tuple[Case, ...]:
    """Build 12 case-disjoint synthetic records from a fixed seed."""
    rng = random.Random(seed)
    base = date(2026, 1, 1)
    splits = ("public",) * 4 + ("hidden",) * 4 + ("temporal_holdout",) * 2 + ("drift",) * 2
    cases: list[Case] = []
    for index, split in enumerate(splits):
        case_id = f"SYN-CASE-{index:03d}"
        patient_id = f"SYN-PATIENT-{index:03d}"
        first = 150 if index % 2 == 0 else 110
        # Keep a meaningful status change so shallow breadth can fail visibly.
        latest = 110 if index % 2 == 0 else 150
        jitter = rng.choice((-2, -1, 0, 1, 2))
        first += jitter
        latest -= jitter
        if split == "drift":
            # The drift task changes the threshold, while the evidence schema stays fixed.
            latest = 135 + (index % 2)
        first_day = base + timedelta(days=index * 3)
        second_day = first_day + timedelta(days=2)
        events = (
            Event(
                event_id=f"{case_id}-OBS-001",
                case_id=case_id,
                resource_type="Observation",
                code="8480-6",
                value=float(first),
                unit="mmHg",
                observed_at=_iso(first_day),
                valid_from=_iso(first_day),
                valid_to=None,
                provenance=f"synthetic://generator/{seed}/{case_id}/observation-1",
            ),
            Event(
                event_id=f"{case_id}-OBS-002",
                case_id=case_id,
                resource_type="Observation",
                code="8480-6",
                value=float(latest),
                unit="mmHg",
                observed_at=_iso(second_day),
                valid_from=_iso(second_day),
                valid_to=None,
                provenance=f"synthetic://generator/{seed}/{case_id}/observation-2",
            ),
            Event(
                event_id=f"{case_id}-ENC-001",
                case_id=case_id,
                resource_type="Encounter",
                code="SYN-OUTPATIENT",
                value=1.0,
                unit="count",
                observed_at=_iso(second_day),
                valid_from=_iso(second_day),
                valid_to=None,
                provenance=f"synthetic://generator/{seed}/{case_id}/encounter-1",
            ),
        )
        cases.append(Case(case_id, patient_id, events, split))
    return tuple(cases)


def build_tasks(cases: Iterable[Case]) -> tuple[Task, ...]:
    tasks: list[Task] = []
    for case in cases:
        observations = [event for event in case.events if event.code == "8480-6"]
        first_day = observations[0].observed_at
        second_day = observations[1].observed_at
        if case.split == "temporal_holdout":
            as_of = first_day
        else:
            as_of = second_day
        threshold = 140.0 if case.split == "drift" else 130.0
        tasks.append(
            Task(
                task_id=f"TASK-{case.case_id}",
                case_id=case.case_id,
                split=case.split,
                as_of=as_of,
                code="8480-6",
                threshold=threshold,
                query=(
                    f"At {as_of}, classify the latest valid synthetic systolic observation "
                    f"as elevated (>= {threshold:g}) or within_range."
                ),
            )
        )
    return tuple(tasks)
