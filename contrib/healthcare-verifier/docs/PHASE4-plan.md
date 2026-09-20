# Phase 4 Implementation Plan

**Goal:** Run the unchanged upstream suite on Linux and deliver an executable, replayable deterministic synthetic pipeline.

**Architecture:** A disposable capability-dropped Python 3.12 container receives only an explicit source archive, without host mounts. A public request selects a synthetic case and strategy; setup, bounded actor and independent verifier execute once and persist their public artifacts through upstream types. Replay reads the saved request and checks deterministic outputs in a fresh directory.

**Tech Stack:** Python 3.12, pytest, Docker, existing upstream task identity/Findings/ArtifactSink.

## Constraints

Use the current fork branch; no paid model calls, PHI, privileged containers, secrets mounts, external messages or PRs. Keep core runtime and upstream tests unchanged. Synthetic costs are proxies; do not claim VM/LLM E2E. Execute inline as requested; no new tasks or delegation.

## Task 1: Linux acceptance

Files: `tools/validate_linux.sh` and `docs/PHASE4-validation.md` under this contribution.

- [ ] Archive an explicit list of runtime/test/config/doc paths, excluding .git, .env and caches. Feed it through stdin into `docker run --rm --cap-drop=ALL --security-opt=no-new-privileges` using Python 3.12.
- [ ] Install requirements-dev.txt inside the container; run `python tools/check_rsi_release.py` and contribution pytest without skipping tests, followed by compileall. Record image digest, Python and dependency versions, exact results and any failures.

## Task 2: Executable pipeline

Files: `rsiaagent_healthcare_fixture/runner.py`, `tools/run_synthetic.py`, `tests/test_runner.py`; modify benchmark.py and report generator.

Interface: `run_request(request: dict, output: Path) -> dict`; request fields exactly seed, case_id, strategy, budget. `replay(source: Path, output: Path) -> dict` reruns saved input and compares public artifacts. Existing output directories must fail before overwriting.

- [ ] Add acceptance tests for pass, breadth rejection, zero budget, unknown/private fields, replay equality, existing-output refusal and phase counts. Example: `assert result['execution_counts'] == {'setup': 1, 'actor': 1, 'verifier': 1}` and `assert not result['success']` for a rejected candidate.
- [ ] Execute setup to generate/select task and persist input/case/task; run bounded deterministic actor; pass only declared public records to `inspect_candidate`; persist actor answer and final ledger. Success requires verifier pass; failures never publish success. Use actual phase invocation counts and actual public setup read counts; monetary/time fields remain modeled.
- [ ] Run a public development setup pass in benchmark initialization and charge recorded reads instead of len(public_tasks). Preserve paired baseline reuse, source checks, caps and split admission.
- [ ] Test `python -m pytest -q contrib/healthcare-verifier/tests` with pinned repository dependencies; regenerate both JSON fixtures and require byte-equality tests to pass.

## Task 3: Deliver

- [ ] Update README and issue draft with runnable CLI examples and precise host-only integration boundary.
- [ ] Run final Linux upstream + contribution suites and compile; review diff; commit only contribution files; normal push; compare local and remote SHA.

## Execution record

Tasks 1 and 2 implemented and validated: Linux upstream 791 passed / 2 pre-existing skips; contribution 44 passed; compileall passed. Task 3 documentation and diff review complete; commit/push follows this record. Full environment and limitations are in PHASE4-validation.md.
