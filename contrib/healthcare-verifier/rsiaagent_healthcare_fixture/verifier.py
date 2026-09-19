"""Evidence-only verifier for synthetic cases.

The verifier receives no Actor reasoning, transcript, or private memory. It rebuilds
one conclusion from public evidence citations and the task's temporal contract.
"""
from __future__ import annotations

from datetime import date
from .schema import ActorAnswer, Case, Task, VerificationResult


def _day(value: str) -> date:
    return date.fromisoformat(value)


def _expected(value: float, threshold: float) -> str:
    return "elevated" if value >= threshold else "within_range"


class EvidenceProvenanceVerifier:
    """Independent checker that can be run without an Actor private trace."""

    def verify(self, task: Task, case: Case, answer: ActorAnswer) -> VerificationResult:
        findings: list[str] = []
        if task.case_id != case.case_id:
            return VerificationResult(
                "wrong", None, None, ("task/case identity mismatch",), 0.0, False, False
            )
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
            if _day(event.valid_from) > _day(task.as_of):
                findings.append(f"future evidence cited before valid_from: {event_id}")
                continue
            if event.valid_to is not None and _day(event.valid_to) < _day(task.as_of):
                findings.append(f"expired evidence cited at as_of: {event_id}")
                continue
            cited.append(event)
        valid = [
            event for event in case.events
            if event.code == task.code
            and _day(event.valid_from) <= _day(task.as_of)
            and (event.valid_to is None or _day(event.valid_to) >= _day(task.as_of))
        ]
        if not valid:
            findings.append("no valid evidence exists at task as_of")
            return VerificationResult(
                "unverified", None, None, tuple(findings), 0.0, False, False
            )
        latest = max(valid, key=lambda event: (event.observed_at, event.event_id))
        expected = _expected(latest.value, task.threshold)
        coverage = 1.0 if any(event.event_id == latest.event_id for event in cited) else 0.0
        provenance_ok = bool(cited) and all(event.provenance.startswith("synthetic://") for event in cited)
        temporal_ok = bool(cited) and all(
            _day(event.valid_from) <= _day(task.as_of)
            and (event.valid_to is None or _day(event.valid_to) >= _day(task.as_of))
            for event in cited
        )
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
