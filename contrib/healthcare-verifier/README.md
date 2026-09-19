# RSIAgent healthcare fixture (projectless draft)

This is an independent, reviewable contribution draft for [RSIAgent](https://github.com/AetherLabsAI/RSIAgent). It contains only fabricated FHIR/Synthea-style observations, synthetic IDs, and a deterministic benchmark. No PHI, production patient material, customer identifier, private prompt, or upstream source code is included.

The fixture covers the requested first contribution point:

- `synthetic.py` creates case-disjoint public, hidden, temporal-holdout, and drift slices from seed `20260919`.
- `verifier.py` reconstructs the conclusion from cited public evidence. It does not accept Actor reasoning, transcripts, or private memory, and it reports provenance and temporal-validity failures.
- `benchmark.py` compares breadth, depth, and frozen-memory reuse with quality, evidence coverage, interaction units, review time, actual compute, a shared per-attempt budget of 2 units, unused budget, public exploration cost, total cost, and negative-transfer counts. The report also includes a sealed split summary and the frozen memory hash must remain unchanged during evaluation.
- `tests/` contains unit, integration, reproducibility, leakage, and failure-regression checks.

Run locally:

```bash
uv run --with pytest --python 3.12 -m pytest -q
python3 tools/generate_fixture.py
```

The second command deterministically regenerates both JSON files under `fixtures/`; the fixed seed and checked-in tests make the generated report auditable.

This draft does not invoke the upstream VM, Docker, model APIs, OSWorld, or ALE. The upstream README requires Python 3.12 plus Linux/Docker and `/dev/kvm` for full benchmark runs; those are explicit blockers for this projectless environment. The upstream contribution guide is `docs/CONTRIBUTING.md`, which asks for focused changes, meaningful regression tests, provenance for benchmark-lock changes, and no credentials, private trajectories, memory snapshots, VM images, benchmark assets, or generated results.

The intended upstream follow-up is a maintainer-reviewed adapter or fixture under the repository's existing `benchmarks/` and `tests/` conventions. Before that step, confirm the accepted directory, task contract, benchmark release, and whether the maintainers want this healthcare fixture in-tree or as a separate companion repository.
