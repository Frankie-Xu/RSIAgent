# Phase 3 implementation plan

1. Bind public evidence to a host-owned deterministic source registry; validate identity, finite values, unique IDs and both observation and validity times. Reject undeclared input fields.
2. Enforce a shared execution cap before simulated evidence reads; record actor, exploration and verification costs separately. Measure negative transfer against a paired no-memory baseline.
3. Inspect and bridge real upstream task identity, Findings and ArtifactSink interfaces without accepting Actor histories; test with real upstream objects and no VM/model calls.
4. Regenerate fixed-seed fixtures, test byte equality and split admission, run the contribution suite and upstream portable release suite, compile, then commit and push the existing fork branch.

All numbers are synthetic diagnostic proxies. Matched caps do not imply equal actual consumption. This is a host-side contract integration, not a complete agent or clinical benchmark.

## Validation outcome (2026-09-20, macOS, Python 3.12)

- Contribution suite: 30 passed, including real upstream objects and two-file byte regeneration.
- Python 3.12 compileall: passed. Diff whitespace check: passed.
- Required `python tools/check_rsi_release.py`: 783 passed, 2 skipped, 8 failed.
- No changes to core/, explore/, env/, tests/, tools/ or requirements (verified against HEAD).
- Three provisioning tests encounter macOS tar metadata; with COPYFILE_DISABLE=1 they advance but Linux archive-size probing returns -1. One venv test expects a Linux lib64 symlink. Four verifier isolation tests execute Linux /proc/self/fd/1 ownership plumbing, unavailable on this macOS host. A focused rerun reproduced 8 failures and passed 64 tests; no tests were suppressed or upstream code changed.

The full upstream suite therefore is NOT green on this host. A supported Linux rerun remains necessary; model/VM E2E is outside this contribution. The local fork implementation and related tests are complete and do not await maintainer permission. Public acceptance, source-manifest ownership and full real-resource experiments remain future decisions.
