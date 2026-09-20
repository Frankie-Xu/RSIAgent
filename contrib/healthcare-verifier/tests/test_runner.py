import json
import subprocess
import sys
from pathlib import Path

import pytest

from rsiaagent_healthcare_fixture.runner import run_request, replay


def request(strategy="depth", budget=2):
    return {"seed": 20260919, "case_id": "SYN-CASE-004", "strategy": strategy, "budget": budget}


def test_pipeline_success_and_phase_counts(tmp_path):
    result = run_request(request(), tmp_path / "run")
    assert result["success"] is True
    assert result["execution_counts"] == {"setup": 1, "actor": 1, "verifier": 1}
    assert result["actor_reads"] == 2
    assert result["verification_records"] == 3
    assert len(result["task_identity"]["sha256"]) == 64
    assert json.loads((tmp_path / "run/iter_01/verify2.json").read_text())["transcript"] == []


@pytest.mark.parametrize("strategy,budget", [("breadth", 2), ("depth", 0)])
def test_rejection_never_publishes_success(tmp_path, strategy, budget):
    result = run_request(request(strategy, budget), tmp_path / "run")
    assert result["success"] is False
    assert result["status"] == "rejected"
    assert result["actor_reads"] <= budget
    assert result["execution_counts"] == {"setup": 1, "actor": 1, "verifier": 1}


@pytest.mark.parametrize("field", ["reasoning", "memory", "transcript", "unknown"])
def test_private_or_unknown_input_is_rejected(tmp_path, field):
    with pytest.raises(ValueError):
        run_request({**request(), field: "PRIVATE"}, tmp_path / "run")
    assert not (tmp_path / "run").exists()


@pytest.mark.parametrize("strategy", ["depth", "breadth"])
def test_replay_success_and_failure(tmp_path, strategy):
    first = run_request(request(strategy), tmp_path / "first")
    second = replay(tmp_path / "first", tmp_path / "second")
    assert first == second
    for path in (tmp_path / "first").rglob("*.json"):
        assert path.read_bytes() == (tmp_path / "second" / path.relative_to(tmp_path / "first")).read_bytes()


def test_existing_output_is_never_overwritten(tmp_path):
    run_request(request(), tmp_path / "run")
    before = (tmp_path / "run/result.json").read_bytes()
    with pytest.raises(FileExistsError):
        run_request(request(), tmp_path / "run")
    assert (tmp_path / "run/result.json").read_bytes() == before


def test_replay_tamper_fails_closed(tmp_path):
    run_request(request(), tmp_path / "first")
    (tmp_path / "first/answer.json").write_text('{}')
    with pytest.raises(ValueError, match="replay"):
        replay(tmp_path / "first", tmp_path / "second")
    assert not json.loads((tmp_path / "second/result.json").read_text())["success"]


def test_actor_exception_records_failure_and_never_runs_verifier(tmp_path, monkeypatch):
    import rsiaagent_healthcare_fixture.runner as runner
    def fail(*args, **kwargs):
        raise RuntimeError("synthetic actor failure")
    monkeypatch.setattr(runner, "_answer", fail)
    result = run_request(request(), tmp_path / "run")
    assert result["status"] == "error" and not result["success"]
    assert result["execution_counts"] == {"setup": 1, "actor": 1, "verifier": 0}


def test_benchmark_setup_counts_real_invocations(monkeypatch):
    import rsiaagent_healthcare_fixture.benchmark as benchmark
    from rsiaagent_healthcare_fixture import build_cases, build_tasks
    actual = {"public_actor": 0, "public_verifier": 0}
    actor = benchmark._answer
    verify = benchmark.EvidenceProvenanceVerifier.verify
    def track_actor(case, task, *args, **kwargs):
        actual["public_actor"] += int(task.split == "public")
        return actor(case, task, *args, **kwargs)
    def track_verifier(self, task, *args, **kwargs):
        actual["public_verifier"] += int(task.split == "public")
        return verify(self, task, *args, **kwargs)
    monkeypatch.setattr(benchmark, "_answer", track_actor)
    monkeypatch.setattr(benchmark.EvidenceProvenanceVerifier, "verify", track_verifier)
    cases = build_cases()
    report = benchmark.run_benchmark(cases, build_tasks(cases), seed=20260919)
    assert report.setup_counts == {"setup_calls": 1, "actor_calls": 4, "verifier_calls": 4,
                                   "actor_reads": 8, "verification_records": 12}
    assert actual == {"public_actor": 4, "public_verifier": 4}


def test_cli_persists_success_and_failure(tmp_path):
    root = Path(__file__).resolve().parents[1]
    for name, code in (("runner_request.json", 0), ("runner_rejection.json", 1)):
        output = tmp_path / name
        process = subprocess.run([sys.executable, str(root / "tools/run_synthetic.py"),
                                  "--input", str(root / "fixtures" / name),
                                  "--output", str(output)], capture_output=True, text=True)
        assert process.returncode == code, process.stderr
        assert json.loads((output / "result.json").read_text())["success"] == (code == 0)
