"""Host-only contract bridge to real upstream types; no agent/VM execution."""
from dataclasses import asdict
import hashlib
import json

from core.task_baseline import stable_task_start_identity
from core.trace import ArtifactSink
from core.verifier import Findings

from .verifier import EvidenceProvenanceVerifier


def inspect_candidate(task, case, answer, *, sink: ArtifactSink, seed=20260919):
    # No LoopResult, transcript, worklog or memory parameter is accepted.
    result = EvidenceProvenanceVerifier(seed=seed).verify(task, case, answer)
    fingerprint = hashlib.sha256(json.dumps(asdict(case), sort_keys=True,
                                           allow_nan=False).encode()).hexdigest()
    identity = stable_task_start_identity(
        task_id=task.task_id, instruction=task.query,
        setup_projection="synthetic-healthcare-v3",
        setup_manifest={"seed": seed, "as_of": task.as_of,
                        "threshold": task.threshold, "code": task.code},
        target_input_fingerprint=fingerprint)
    findings = Findings("; ".join(result.findings) or "Cited evidence reconstructs the conclusion")
    status = {"pass": "met", "wrong": "violated", "unverified": "could-not-confirm"}[result.status]
    findings.items = (("evidence reconstruction", status, str(findings)),)
    sink.save_verify2(1, result.status, findings)
    sink.save_result({"kind": "synthetic_contract_check", "task_identity": identity,
                      "verification": asdict(result), "official_score": None})
    return result, findings
