# RSIAgent Healthcare Fixture Implementation Plan

> **For agentic workers:** This plan is for an independent projectless fixture. It must not modify or copy code from the upstream checkout until a maintainer-approved checkout and contribution boundary exist.

**Goal:** Provide a small, deterministic synthetic FHIR/Synthea-style environment, an evidence-only provenance verifier, and a breadth/depth/frozen-memory benchmark that can be reviewed before any upstream contribution.

**Architecture:** Synthetic cases are generated from a fixed seed and represented as immutable public event records. The verifier receives only the task contract, public case records, and an actor answer containing citations; it never receives private reasoning or memory. The benchmark builds disjoint public, hidden, temporal-holdout, and drift slices, then evaluates broad exploration, deep exploration, and frozen-memory reuse with quality, evidence coverage, cost, and negative-transfer metrics.

**Tech Stack:** Python 3.12-compatible standard library; pytest for unit/integration/regression tests; JSON fixtures.

## Global Constraints

- Use only synthetic, non-identifying case IDs and fabricated clinical facts.
- Keep verifier inputs independent of Actor private traces and private memory.
- Fix the random seed and make generated tasks byte-for-byte reproducible.
- Preserve temporal validity and case-disjoint splits; no future events may be used for an `as_of` query.
- Report quality, evidence traceability, review time, compute/human cost, and negative transfer.
- Do not copy upstream implementation code or submit/push/open issues in this projectless phase.

### Task 1: Synthetic environment and schema

**Files:**
- Create: `outputs/rsiaagent_healthcare_fixture/rsiaagent_healthcare_fixture/schema.py`
- Create: `outputs/rsiaagent_healthcare_fixture/rsiaagent_healthcare_fixture/synthetic.py`
- Create: `outputs/rsiaagent_healthcare_fixture/README.md`

**Deliverable:** Immutable records for cases, events, evidence citations, tasks, and benchmark attempts. The generator emits deterministic fabricated observations with `case_id`, `source_id`, `valid_from`, `valid_to`, provenance, and cost metadata.

### Task 2: Independent provenance verifier

**Files:**
- Create: `outputs/rsiaagent_healthcare_fixture/rsiaagent_healthcare_fixture/verifier.py`
- Test: `outputs/rsiaagent_healthcare_fixture/tests/test_verifier.py`

**Deliverable:** A verifier that reconstructs the expected conclusion from cited public events, rejects unknown or cross-case citations, rejects temporally invalid evidence, and distinguishes `pass`, `wrong`, and `unverified`. The API accepts no private trace parameter.

### Task 3: Unified benchmark

**Files:**
- Create: `outputs/rsiaagent_healthcare_fixture/rsiaagent_healthcare_fixture/benchmark.py`
- Test: `outputs/rsiaagent_healthcare_fixture/tests/test_benchmark.py`

**Deliverable:** A deterministic benchmark with public, hidden, temporal-holdout, case-disjoint, and drift slices. It compares breadth, depth, and frozen-memory reuse while retaining an immutable memory snapshot and reporting quality, evidence coverage, review time, compute cost, and negative transfer.

### Task 4: Regression and reproducibility checks

**Files:**
- Create: `outputs/rsiaagent_healthcare_fixture/tests/test_reproducibility.py`
- Create: `outputs/rsiaagent_healthcare_fixture/pytest.ini`
- Create: `outputs/rsiaagent_healthcare_fixture/tools/generate_fixture.py`

**Deliverable:** Unit, integration, and failure-regression tests covering seed stability, case/temporal leakage, stale citations, frozen-memory mutation, cost accounting, and checked-in JSON regeneration.

### Validation

Run from `outputs/rsiaagent_healthcare_fixture`:

```bash
python3 -m pytest -q
```

Expected: all tests pass without credentials, network, Docker, VM images, or benchmark assets.
