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

Exploration is a fixed simulated setup charge of one unit per public task (4 per arm); it is not measured curriculum execution. Verification charges one unit per candidate event (3 per task here), outside the actor cap and equal across arms on the same case. Total compute includes setup + actor + verification. Interaction records actor reads; verification and setup are separate compute categories. The depth arm is also the paired no-memory baseline and is executed once, then reused for comparisons.

Human cost is solely `review_seconds * 0.2` in arbitrary units; seconds are assigned proxies, not observed clinician time. Compute cost is separately `total_compute_units * 0.05`; no dollar costs are claimed. Exploration human time is zero by assumption. Negative transfer counts frozen-memory tasks whose quality is lower than paired depth/no-memory quality under the same task/cap, regardless of split. Quality delta and baseline quality are retained per attempt. Drift deliberately exposes a stale threshold; it is an injected regression, not an empirical memory-learning result.

## Splits, feedback, runtime boundary

Public development has 4 cases; evaluation has hidden 4, temporal-holdout 2, drift 2. Admission checks case/task identity and split agreement before running. Temporal tasks use the first observation cutoff. These are published synthetic regression cases: separation is logical, not a secret or never-inspected holdout. No tuning uses evaluation outcomes in this runner, but an independent acceptance cohort is still needed for a real experiment.

Feedback attribution: malformed provenance/time evidence is an evidence-contract failure; omitting the latest valid citation is retrieval omission; wrong labels with valid citations are execution/rule errors. A disagreement with the host generator is a verifier regression and must not train memory from evaluation. Frozen memory is constructed from public task IDs plus a declared procedure and remains unchanged; no private memory is serialized in the report.

`runtime_bridge.py` invokes the real upstream `stable_task_start_identity`, creates real `core.verifier.Findings`, and writes through `core.trace.ArtifactSink.save_verify2/save_result`. Contract tests inspect actual artifacts in a temporary directory. It does not pass `LoopResult.worklog`, Actor histories or memory into the checker; it does not call the agentic verifier or claim an official score. Upstream `LoopResult` represents lifecycle status and private worklog, so it is intentionally not converted wholesale. No generic upstream healthcare task plug-in interface was found: integration is limited to host task identity, findings and artifact persistence, not full Actor/Verifier/VM E2E.

Maintainership questions concern future in-tree placement, public candidate serialization, trusted source-manifest ownership, verifier status mapping and resource units. They do not block fork implementation. Rollback is removal/reversion of this isolated contribution; core runtime, role profiles and official benchmark locks are unchanged.
