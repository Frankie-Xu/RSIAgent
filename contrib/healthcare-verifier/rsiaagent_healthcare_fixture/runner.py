"""Replayable host deterministic pipeline. No VM, LLM or clinical evaluation."""
from dataclasses import asdict
import json
from pathlib import Path

from core.trace import ArtifactSink

from .benchmark import STRATEGIES, MATCHED_BUDGET_UNITS, _answer
from .synthetic import build_cases, build_tasks
from .runtime_bridge import inspect_candidate


def _write(path, payload):
    path.write_text(json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def run_request(request: dict, output: Path) -> dict:
    if type(request) is not dict or set(request) != {"seed", "case_id", "strategy", "budget"}:
        raise ValueError("only declared public request fields are accepted")
    if (type(request["seed"]) is not int or type(request["budget"]) is not int
            or not 0 <= request["budget"] <= MATCHED_BUDGET_UNITS
            or request["strategy"] not in STRATEGIES
            or type(request["case_id"]) is not str):
        raise ValueError("invalid seed, strategy, case_id or budget")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    sink = ArtifactSink(str(output))
    _write(output / "input.json", request)
    counts = {"setup": 0, "actor": 0, "verifier": 0}
    result = {"kind": "host_deterministic_pipeline", "success": False,
              "official_score": None, "execution_counts": counts}
    stage = "setup"
    try:
        counts[stage] += 1
        cases = build_cases(request["seed"])
        case = next((c for c in cases if c.case_id == request["case_id"]), None)
        if case is None:
            raise ValueError("unknown synthetic case")
        task = build_tasks((case,))[0]
        _write(output / "case.json", asdict(case))
        _write(output / "task.json", asdict(task))
        result["setup_generated_records"] = sum(len(c.events) for c in cases)
        stage = "actor"
        counts[stage] += 1
        # Public fixed procedure only; no private Actor memory or transcript enters checker.
        answer = _answer(case, task, request["strategy"], {"default_threshold": "130"},
                         budget=request["budget"])
        _write(output / "answer.json", asdict(answer))
        result["actor_reads"] = answer.interaction_units
        stage = "verifier"
        counts[stage] += 1
        verdict, _ = inspect_candidate(task, case, answer, sink=sink, seed=request["seed"])
        bridge_result = json.loads((output / "result.json").read_text())
        result.update(task_identity=bridge_result["task_identity"], verification=asdict(verdict),
                      verification_records=len(case.events),
                      status="accepted" if verdict.status == "pass" else "rejected",
                      success=verdict.status == "pass")
    except Exception as exc:
        result.update(status="error", success=False, failed_stage=stage,
                      error_type=type(exc).__name__)
    sink.save_result(result)
    return result


def replay(source: Path, output: Path) -> dict:
    source, output = Path(source), Path(output)
    request = json.loads((source / "input.json").read_text(encoding="utf-8"))
    result = run_request(request, output)
    expected = {p.relative_to(source): p.read_bytes() for p in source.rglob("*.json")}
    actual = {p.relative_to(output): p.read_bytes() for p in output.rglob("*.json")}
    if expected != actual:
        result.update(success=False, status="replay_mismatch")
        ArtifactSink(str(output)).save_result(result)
        raise ValueError("replay artifacts differ")
    return result
