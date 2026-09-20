# Synthetic healthcare evidence contract fixture

This fork contribution uses fabricated FHIR/Synthea-style records (not validated FHIR bundles or Synthea exports). It exercises software contracts, not clinical correctness or real model performance. No patient records, private prompts, credentials, model calls or VM runs are used.

## Reproduce from the repository root

```bash
uv run --python 3.12 --with-requirements requirements-dev.txt python -m pytest -q contrib/healthcare-verifier/tests
uv run --python 3.12 --with-requirements requirements-dev.txt python tools/check_rsi_release.py
uv run --python 3.12 python contrib/healthcare-verifier/tools/generate_fixture.py
uv run --python 3.12 python -m compileall -q contrib/healthcare-verifier/rsiaagent_healthcare_fixture contrib/healthcare-verifier/tests contrib/healthcare-verifier/tools
```

The generator supports `--output /temporary/directory`. Tests compare both generated JSON files byte-for-byte with the checked-in fixtures without rewriting them. Seed 20260919 defines the source registry and data. Different seeds require a matching verifier registry.

## Evidence boundary

The host creates `EvidenceProvenanceVerifier(seed=...)` independently from the Actor. Every event must exactly match the generator registry, including case, source URI, value and dates; altered inventory, duplicate IDs and non-finite values fail closed. Merely providing a `synthetic://` URI is insufficient. The registry is a synthetic fixture trust anchor, not a cryptographic signature for arbitrary clinical data.

An event is available only when BOTH `observed_at <= as_of` and `valid_from <= as_of`, with inclusive `valid_to` when present. Thus a later-observed backfilled fact cannot affect an earlier query. The checker requires citation of the latest available observation and reconstructs the label from that evidence. The threshold is an arbitrary task rule, not medical advice. Exact dataclass types/declared fields are enforced; histories and memory are not accepted.

## Budget and metrics

All metrics are deterministic proxies. Each strategy gets an actor interaction/compute cap of 2 simulated indexed observation reads per task. Admission is enforced before reads; zero budget produces no read. Metadata filtering/sorting is free in this toy cost model. Equal caps DO NOT mean equal actual cost. This fixture does not establish a matched-resource LLM experiment or substantiate upstream performance claims.

Setup now executes four public deterministic practice tasks and verifies each, with 8 counted actor reads and 12 checked candidate records (20 simulated units). `setup_counts` records the actual invocations. This is deterministic practice, not an LLM curriculum. Setup runs once per protocol; each arm's standalone total includes the entire setup cost, while `protocol_modeled_compute` counts the shared setup only once. Verification charges one unit per candidate event (3 per task here), outside the actor cap. Total compute includes setup + actor + verification. Interaction records actor reads. The depth arm is also the paired no-memory baseline and is executed once, then reused for comparisons.

Human cost is solely `review_seconds * 0.2` in arbitrary units; seconds are assigned proxies, not observed clinician time. Compute cost is separately `total_compute_units * 0.05`; no dollar costs are claimed. Exploration human time is zero by assumption. Negative transfer counts frozen-memory tasks whose quality is lower than paired depth/no-memory quality under the same task/cap, regardless of split. Quality delta and baseline quality are retained per attempt. Drift deliberately exposes a stale threshold; it is an injected regression, not an empirical memory-learning result.

## Splits, feedback, runtime boundary

Public development has 4 cases; evaluation has hidden 4, temporal-holdout 2, drift 2. Admission checks case/task identity and split agreement before running. Temporal tasks use the first observation cutoff. These are published synthetic regression cases: separation is logical, not a secret or never-inspected holdout. No tuning uses evaluation outcomes in this runner, but an independent acceptance cohort is still needed for a real experiment.

Feedback attribution: malformed provenance/time evidence is an evidence-contract failure; omitting the latest valid citation is retrieval omission; wrong labels with valid citations are execution/rule errors. A disagreement with the host generator is a verifier regression and must not train memory from evaluation. Frozen memory is constructed from public task IDs plus a declared procedure and remains unchanged; no private memory is serialized in the report.

`runtime_bridge.py` invokes the real upstream `stable_task_start_identity`, creates real `core.verifier.Findings`, and writes through `core.trace.ArtifactSink.save_verify2/save_result`. `runner.py` executes setup → deterministic actor → independent evidence verifier and records actual invocation counts, public input/case/task/answer, findings and final result. It rejects undeclared request fields and existing output directories. Rejected candidates or stage exceptions never produce a final successful status. Replay compares every JSON artifact and fails closed on differences. It does not pass `LoopResult.worklog`, Actor histories or memory into the checker; no official score is claimed. This is a host deterministic pipeline, not Actor/Verifier/VM or LLM E2E.

## Executable runner and Linux validation

From the repository root, choose fresh output paths outside the checkout:

```bash
uv run --python 3.12 --with-requirements requirements-dev.txt python contrib/healthcare-verifier/tools/run_synthetic.py --input contrib/healthcare-verifier/fixtures/runner_request.json --output /tmp/rsi-healthcare-run
uv run --python 3.12 --with-requirements requirements-dev.txt python contrib/healthcare-verifier/tools/run_synthetic.py --replay /tmp/rsi-healthcare-run --output /tmp/rsi-healthcare-replay
uv run --python 3.12 --with-requirements requirements-dev.txt python contrib/healthcare-verifier/tools/run_synthetic.py --input contrib/healthcare-verifier/fixtures/runner_rejection.json --output /tmp/rsi-healthcare-rejected
bash contrib/healthcare-verifier/tools/validate_linux.sh
```

The rejection example intentionally exits 1 and persists `success: false`. Stage errors record their type and attempted invocation counts, not exception text or private context. The container receives an explicit source archive through stdin, mounts no host paths, drops all capabilities, enables no-new-privileges and is removed at exit. The pinned Python image and required Python packages need network access only for installation; tests require no keys or model calls. Linux results and environment versions are recorded in `docs/PHASE4-validation.md`.

Maintainership questions concern future in-tree placement, public candidate serialization, trusted source-manifest ownership, verifier status mapping and resource units. They do not block fork implementation. Rollback is removal/reversion of this isolated contribution; core runtime, role profiles and official benchmark locks are unchanged.
