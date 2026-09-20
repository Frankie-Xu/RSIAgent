# Local Issue #5 discussion draft — not sent

This fork adds a synthetic matched-cap diagnostic, not evidence resolving the real matched-resource performance question. Actor reads have an enforced common cap; actual costs may differ. Public setup practice actually executes and records 4 actor calls and 4 verifier calls, while compute and human time/cost conversions remain simulated. Shared setup is counted once for protocol cost and included in each standalone arm cost. Negative transfer is the quality loss against a paired no-memory depth baseline, not a drift label.

Source checks reject future observations (including backfilled facts), altered sources, cross-case evidence, duplicates and non-finite values. Development and evaluation cases are disjoint but all are public synthetic regression fixtures, not a confidential holdout. A thin contract bridge uses real upstream task identity, Findings and ArtifactSink objects without reading private histories or invoking a VM/model.

## Validation

Contribution tests include byte-exact regeneration of both JSON fixtures, real upstream-object contracts and executable success/rejection/replay paths. Current Linux counts and environment evidence are in PHASE4-validation.md. Run from repository root:

Phase 3 macOS results remain recorded in PHASE3.md; Phase 4 runs the full unchanged suite in a disposable Linux container, without suppressing the previously failing tests.

```bash
uv run --python 3.12 --with-requirements requirements-dev.txt python -m pytest -q contrib/healthcare-verifier/tests
uv run --python 3.12 --with-requirements requirements-dev.txt python tools/check_rsi_release.py
uv run --python 3.12 python -m compileall -q contrib/healthcare-verifier
```

Before a real experiment, agree on source trust ownership, public candidate fields, official lock, full exploration/verification/inference budgets and an independent acceptance cohort. No clinical or real-model conclusion is claimed by the deterministic fixtures.
