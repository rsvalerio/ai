# Flakiness Patterns

Root-cause explanations for TEST-16--21. Use these to understand *why* each rule exists and to classify root causes when triaging flaky tests. For enforceable mitigations, see the corresponding rules in [rules.md](rules.md).

| Pattern | Why it's flaky | Typical severity | Rule |
|---------|----------------|-----------------|------|
| **Random without seed** | Non-deterministic; different runs give different results | Medium (High if masking real bugs) | TEST-16 |
| **Time / sleep** | Timing varies by load; `thread::sleep` in tests is inherently unreliable. Runtime-specific: tokio has `time::pause()`, other runtimes (async-std, smol) need mock clocks or channel-based sync | High in CI (timing is load-dependent); Medium locally | TEST-13, TEST-15 |
| **Shared mutable state** | Order of test execution or parallelism changes outcome | High (can mask real race conditions) | TEST-18 |
| **File system / env** | Depends on cwd, env vars, or files that change between runs | Medium (Low if test-only paths) | TEST-19 |
| **Network / external services** | Service availability or latency varies; hardcoded ports cause collisions | High (non-deterministic failures erode CI trust) | TEST-17, TEST-20 |
| **Concurrency / order** | Thread scheduling or async task order is non-deterministic | High (may hide real data races) | TEST-21 |

**Flakiness categories**: *Determinism flakiness* (random, time, concurrency) — the test logic itself is non-deterministic; fix by controlling the source of non-determinism. *Isolation flakiness* (shared state, filesystem, network) — the test depends on external state; fix by isolating the test environment.

> Assign severity per the severity scale in [rules.md](rules.md#severity-scale). Upgrade severity when the flaky test covers critical functionality or when flakiness masks real bugs. Downgrade when the test is on a non-critical path and the flakiness source is well-understood.
