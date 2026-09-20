# Phase 4 Linux acceptance — 2026-09-20

Baseline: `ef6f4efcc9149371fad13b623406619b64c9f1ef`. Scope: contribution only; upstream core, test suite and official configuration unchanged.

## Reproduction

From repository root:

```bash
bash contrib/healthcare-verifier/tools/validate_linux.sh
```

Docker daemon: Linux 29.5.2. Container image:
`python:3.12-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`.
Python 3.12.14; Linux aarch64 kernel 6.8.0-117-generic. All resolved Python package versions are recorded in `tools/requirements-linux.lock`, used as pip constraints alongside the unchanged upstream requirements-dev.txt. No additional system packages were needed.

The script uses a disposable `--rm` container, `--cap-drop=ALL`, `--security-opt=no-new-privileges`, no host mounts and no Docker socket. Only explicitly listed source directories/files are streamed through stdin. It does not transfer .git, credentials or .env; the tracked .env.example is included as source. Other containers are untouched. Network is used for public image/package installation, not model inference or cloud resources.

## Final results

| Command inside container | Outcome |
| --- | --- |
| `python tools/check_rsi_release.py` | 791 passed, 2 skipped in 18.54 s |
| `python -m pytest -q contrib/healthcare-verifier/tests` | 44 passed in 2.10 s |
| `python -m compileall -q contrib/healthcare-verifier` | exit 0 |

The two existing skips are frozen OSWorld evaluator opt-in tests in test_evaluator_corrections.py; no skip/deselect flags were introduced. All eight Phase 3 macOS failures passed on Linux unchanged. Local macOS contribution tests also passed 44 cases.

Initial container source extraction failed because tar attempted to restore host UID 501 under dropped capabilities. The script now uses GNU tar `--no-same-owner`; permissions were not elevated. Subsequent full runs passed. This was a transport setup failure, not a benchmark task result.

## Executed integration and accounting

The CLI tests execute real subprocesses for both fixtures/runner_request.json (exit 0) and fixtures/runner_rejection.json (exit 1). Artifacts include public input, case, task, answer, upstream verify2.json and final result.json. Success/rejection replay, tampered replay, existing-directory refusal, private/unknown input rejection, zero budget and actor exception handling are tested.

A normal runner records exactly one setup, one deterministic actor and one independent verifier invocation. Stage counters count attempted boundary invocations, including failures; they are not LLM call counters. Setup generates 36 synthetic records; the chosen case contributes 3 records to verification. A depth success reads 2 observations. A rejected candidate never receives a final success status. A replay mismatch changes final status to replay_mismatch and fails.

Benchmark public setup now actually executes four practice actors and four verifiers, with eight actor reads and twelve verification records. Spies in tests confirm invocation counts. One shared setup is included once in protocol accounting (122 simulated compute units total), whereas each standalone arm includes its full 20-unit setup cost. Paired depth baseline is reused without a second execution. Human time and unit-to-cost conversion remain declared proxies; none are clinician measurements, dollars or real-model benchmark scores.

Both checked-in generated JSON fixtures are byte-reproduced in temporary directories by tests. Synthetic input data remains unchanged; report changes reflect executed setup accounting. No private memories, trajectories, VM assets or generated runtime result directories are committed.

## Boundary and remaining work

This is an executable host deterministic pipeline using actual upstream task identity, Findings and ArtifactSink, not a VM/LLM E2E or clinical system. There is no Phase 4 acceptance blocker. Future VM integration and upstream adoption still need task/candidate serialization, trusted source ownership and real resource measurement agreements; they were not required to implement or push this fork contribution.
