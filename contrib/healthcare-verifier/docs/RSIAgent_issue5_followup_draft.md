# Local Issue #5 discussion draft — not sent

This fork adds a synthetic matched-cap diagnostic, not evidence resolving the real matched-resource performance question. Actor reads have an enforced common cap; actual costs may differ. Setup/exploration charges and verifier compute are separately reported, and human time/cost is explicitly simulated. Negative transfer is the quality loss against a paired no-memory depth baseline, not a drift label.

Source checks reject future observations (including backfilled facts), altered sources, cross-case evidence, duplicates and non-finite values. Development and evaluation cases are disjoint but all are public synthetic regression fixtures, not a confidential holdout. A thin contract bridge uses real upstream task identity, Findings and ArtifactSink objects without reading private histories or invoking a VM/model.

## Validation

30 contribution tests pass, including byte-exact regeneration of both JSON fixtures and real upstream-object contract tests. Run from repository root:

The complete upstream suite on this macOS host reports 783 passed, 2 skipped and 8 failures in unchanged Linux-oriented provisioning/isolation tests; see PHASE3.md. It is not reported as a passing full release check.

```bash
uv run --python 3.12 --with-requirements requirements-dev.txt python -m pytest -q contrib/healthcare-verifier/tests
uv run --python 3.12 --with-requirements requirements-dev.txt python tools/check_rsi_release.py
uv run --python 3.12 python -m compileall -q contrib/healthcare-verifier
```

Before a real experiment, agree on source trust ownership, public candidate fields, official lock, full exploration/verification/inference budgets and an independent acceptance cohort. No clinical or real-model conclusion is claimed by the deterministic fixtures.
