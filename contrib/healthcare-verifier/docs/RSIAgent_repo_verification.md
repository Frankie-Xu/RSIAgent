# RSIAgent repository verification (read-only)

Snapshot verified 2026-09-19 from the public repository `https://github.com/AetherLabsAI/RSIAgent` at `main` commit `a9e56263f6deaa493496ad6b155fe24bf131bc12`.

- License: root `LICENSE` is Apache License 2.0; README links the same license. Third-party benchmark dependencies retain their own terms and are documented in `docs/THIRD_PARTY.md`.
- Contribution entry: no root `CONTRIBUTING.md`; contribution instructions are in `docs/CONTRIBUTING.md`. It requests focused issues/PRs, Python 3.12, `requirements-dev.txt`, `python tools/check_rsi_release.py`, meaningful regression tests, provenance for role/lock changes, and no credentials/private trajectories/memory snapshots/VM images/benchmark assets/generated result directories.
- Structure: `core/` contains Actor/Verifier runtime; `explore/` contains curriculum, learning, memory, and recovery; `env/` contains transport/isolation; `benchmarks/` contains OSWorld and ALE adapters; `tests/` contains regression tests; `config/` contains role and benchmark locks; `tools/` contains smoke/release checks.
- Test entry: `pytest.ini` sets `tests` as `testpaths`; `requirements-dev.txt` includes pytest 9.1.1; portable release validation is `python tools/check_rsi_release.py`, which invokes `pytest -q tests`.
- Benchmark entry: `run_osworld.py` and `run_ale.py`; README advertises a no-credential smoke path through `tools/smoke_osworld.py`, but full runs require benchmark installations and VM infrastructure.
- Current issue: Issue #5 remains open: “Unmatched evaluation does not support the public ‘outperforms GPT-6’ claim”. Its body asks for same-model/harness matched-resource controls including exploration costs and qualifications alongside the public claim.

This checkout was cloned into `work/upstream` for read-only inspection only. No upstream files were modified, no GitHub message was sent, and no branch, issue, or PR was created.
