# Draft: matched-budget synthetic verifier benchmark for Issue #5

**Status:** local draft only; not submitted or sent.

**Proposed title:** Add a deterministic matched-budget benchmark for exploration and frozen-memory reuse

## Problem

Issue #5 asks for a control that separates recursive curriculum/memory benefit from extra interaction and target practice. The current projectless draft provides a small synthetic control surface without changing the upstream runtime or benchmark claims.

## Proposed contribution

Add a maintainer-approved synthetic fixture that:

- generates FHIR/Synthea-style records from seed `20260919`;
- keeps public, hidden, temporal-holdout, case-disjoint, and drift slices separate;
- verifies conclusions from cited public evidence only, without Actor private reasoning or memory;
- compares breadth, depth, and frozen-memory reuse under explicit interaction/compute/review budgets;
- emits a sealed split summary for public, hidden, temporal-holdout, case-disjoint, and drift cases;
- gives every evaluated strategy the same per-attempt budget, while separately recording actual compute, unused budget, public exploration cost, total cost, review seconds, human-cost proxy, and negative transfer;
- turns future citations, cross-case citations, stale conclusions, and frozen-memory mutation into regression tests.

## Validation in this draft

The independent fixture passes 14 tests under a temporary `uv` pytest environment. Run `uv run --with pytest --python python3 -m pytest -q`, then `python3 tools/generate_fixture.py`; the generated report is in `fixtures/benchmark_report.json`. The frozen memory hash is identical before and after evaluation. The draft does not invoke model APIs, Docker, `/dev/kvm`, OSWorld, ALE, or production data.

## Maintainer questions before an upstream change

1. Should this remain a synthetic companion fixture or live under `benchmarks/` and `tests/`?
2. Which released benchmark lock and budget fields should define the compute-matched control?
3. Should the official report include this as a diagnostic protocol separate from headline benchmark scores?
