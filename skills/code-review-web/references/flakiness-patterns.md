# Frontend Test Flakiness Patterns

Root-cause explanations for the TEST async/determinism rules. Use these to understand *why* each rule exists and to classify root causes when triaging flaky frontend tests. For enforceable mitigations see [rules-tests.md](rules-tests.md).

| Pattern | Why it's flaky | Typical severity | Rule |
|---------|----------------|-----------------|------|
| **Real timers for throttle/debounce** | Wall-clock timing varies by machine/CI load; throttled/debounced code resolves at different points | High in CI; Medium locally | TEST-9 |
| **Side effects inside `waitFor`** | The callback re-runs until timeout; firing events or calling APIs inside it produces non-deterministic state and duplicate calls | High | TEST-8 |
| **Un-awaited async update / manual `act()`** | Assertions run before the UI settles; `act()` warnings signal updates not awaited | High | TEST-7 |
| **Unmocked / real network** | Service availability, latency, and ordering vary; tests fail intermittently and erode trust | High | TEST-10 |
| **Shared mutable state / order dependence** | Test outcome depends on execution order or leaked state (unreset mocks, MSW handlers, module singletons) | High (can mask real bugs) | TEST-13 |
| **Uncontrolled randomness / clock** | `Math.random()`/`Date.now()` make output non-deterministic across runs | Medium (High if masking bugs) | TEST-9 |
| **Querying by unstable text/markup** | Asserting on volatile copy, formatting, or auto-updated snapshots breaks on unrelated changes | Medium | TEST-14 |

**Flakiness categories**: *Determinism flakiness* (timers, randomness, un-awaited async) — the test logic is non-deterministic; fix by controlling the source (fake timers, fixed inputs, proper `await`). *Isolation flakiness* (real network, shared state, order dependence) — the test depends on external/leaked state; fix by mocking the boundary (MSW) and resetting state between tests.

> Assign severity per the scale in [rules.md](rules.md#severity-scale). Upgrade when the flaky test covers critical functionality (crypto, auth, collab) or when flakiness masks a real bug; downgrade for non-critical paths with a well-understood, contained cause.
