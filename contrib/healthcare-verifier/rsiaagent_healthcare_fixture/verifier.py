"""Evidence-only verifier for synthetic cases.

The verifier receives no Actor reasoning, transcript, or private memory. It rebuilds
one conclusion from public evidence citations and the task's temporal contract.
"""
from __future__ import annotations

from datetime import date
from dataclasses import fields
from math import isfinite
from .schema import ActorAnswer, Case, Event, Task, VerificationResult
from .synthetic import DEFAULT_SEED, build_cases


def strict_record(value, cls):
    if type(value) is not cls or set(vars(value)) != {f.name for f in fields(cls)}:
        raise ValueError(f"undeclared fields or invalid {cls.__name__} input")


def available(event, as_of):
    cutoff = _day(as_of)
    return (_day(event.observed_at) <= cutoff and _day(event.valid_from) <= cutoff
            and (event.valid_to is None or cutoff <= _day(event.valid_to)))


def _day(value: str) -> date:
    return date.fromisoformat(value)


def _expected(value: float, threshold: float) -> str:
    return "elevated" if value >= threshold else "within_range"


class EvidenceProvenanceVerifier:
    """Independent checker that can be run without an Actor private trace."""

    def __init__(self, *, seed=DEFAULT_SEED):
        # Host-owned source of truth, never supplied by the Actor candidate.
        self.sources = {e.event_id: e for c in build_cases(seed) for e in c.events}

    def verify(self, task: Task, case: Case, answer: ActorAnswer) -> VerificationResult:
        for value, cls in ((task, Task), (case, Case), (answer, ActorAnswer)):
            strict_record(value, cls)
        for event in case.events:
            strict_record(event, Event)
        if not isfinite(task.threshold):
            raise ValueError("non-finite task threshold")
        findings: list[str] = []
        if task.case_id != case.case_id:
            return VerificationResult(
                "wrong", None, None, ("task/case identity mismatch",), 0.0, False, False
            )
        ids = [e.event_id for e in case.events]
        if len(ids) != len(set(ids)):
            findings.append("duplicate evidence ID")
        trusted = True
        expected_ids = {e.event_id for e in self.sources.values() if e.case_id == case.case_id}
        if set(ids) != expected_ids:
            findings.append("provenance inventory mismatch")
            trusted = False
        for event in case.events:
            if not isfinite(event.value):
                findings.append(f"non-finite evidence value: {event.event_id}")
                trusted = False
            if event.case_id != case.case_id or self.sources.get(event.event_id) != event:
                findings.append(f"untrusted provenance or altered source: {event.event_id}")
                trusted = False
        public = case.event_map()
        cited = []
        for event_id in answer.evidence_ids:
            if event_id.startswith("SYN-CASE-") and not event_id.startswith(case.case_id + "-"):
                findings.append(f"cross-case evidence citation: {event_id}")
                continue
            event = public.get(event_id)
            if event is None:
                findings.append(f"unknown evidence citation: {event_id}")
                continue
            if event.case_id != task.case_id:
                findings.append(f"cross-case evidence citation: {event_id}")
                continue
            if event.code != task.code:
                findings.append(f"evidence code mismatch: {event_id}")
                continue
            if max(_day(event.valid_from), _day(event.observed_at)) > _day(task.as_of):
                findings.append(f"future evidence observed or valid after as_of: {event_id}")
                continue
            if event.valid_to is not None and _day(event.valid_to) < _day(task.as_of):
                findings.append(f"expired evidence cited at as_of: {event_id}")
                continue
            cited.append(event)
        valid = [
            event for event in case.events
            if event.code == task.code
            and available(event, task.as_of)
            and isfinite(event.value)
        ]
        if not valid:
            findings.append("no valid evidence exists at task as_of")
            return VerificationResult(
                "wrong" if not trusted or len(findings) > 1 else "unverified",
                None, None, tuple(findings), 0.0, False, False
            )
        latest = max(valid, key=lambda event: (event.observed_at, event.event_id))
        expected = _expected(latest.value, task.threshold)
        coverage = 1.0 if any(event.event_id == latest.event_id for event in cited) else 0.0
        provenance_ok = trusted and len(ids) == len(set(ids)) and bool(cited)
        temporal_ok = bool(answer.evidence_ids) and all(
            event_id in public and available(public[event_id], task.as_of)
            for event_id in answer.evidence_ids)
        if not cited:
            findings.append("answer supplied no valid evidence citation")
        if not provenance_ok:
            findings.append("evidence provenance is missing or outside synthetic source")
        if not temporal_ok:
            findings.append("evidence is not temporally valid")
        if coverage == 0.0:
            findings.append(f"latest valid observation was not cited: {latest.event_id}")
        if answer.conclusion != expected:
            findings.append(f"conclusion mismatch: expected {expected}, got {answer.conclusion}")
        status = "pass" if not findings else "wrong"
        return VerificationResult(
            status,
            answer.conclusion,
            expected,
            tuple(findings),
            coverage,
            provenance_ok,
            temporal_ok,
        )


def verify_without_private_trace(task: Task, case: Case, answer: ActorAnswer) -> VerificationResult:
    """Convenience function whose signature makes the isolation boundary explicit."""
    return EvidenceProvenanceVerifier().verify(task, case, answer)
