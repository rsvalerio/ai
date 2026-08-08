# Test Quality Rules

## Test Structure

- **TEST-1.** Every test must have meaningful assertions; no empty bodies or assertion-free tests.
  **Scanning guidance:** a naive regex that looks only for `assert!` / `assert_eq!` / `assert_ne!` inside the test body produces massive false-positive counts. Treat each of the following as an assertion for TEST-1 purposes:
  - Calls to a helper function whose name starts with `assert_` (e.g. `assert_passthrough(&result)`) — the helper contains the real assertion.
  - `#[should_panic]` or `#[should_panic(expected = "...")]` on the `#[test]` fn — panic is the assertion.
  - `.unwrap()` / `.expect()` / `?` in a `#[test] fn foo() -> Result<...>` — panic or `Err` propagation is the assertion.
  - `.is_ok()` / `.is_err()` / `.is_some()` / `.is_none()` used in an expression that drives `assert!` (TEST-11 still applies: prefer asserting the value).
  - Property-based tests where the property itself panics on falsification (`proptest!`, `quickcheck!`).
  A test with none of the above is a real TEST-1 candidate — typically a `#[test]` that performs setup + calls the function under test without inspecting the result. Before filing, verify the candidate at its source line; prefer surfacing an exact *file:line list* of candidates over a raw count (raw counts in this workspace ran 70× inflated).
- **TEST-2.** One concern per test; name encodes both the state/scenario being tested AND the expected outcome — e.g., `test_empty_input_returns_none`, not just `test_parse` or `test_empty`
- **TEST-3.** Integration tests in `tests/`; unit tests in `#[cfg(test)]` modules
- **TEST-4.** Shared setup via helper functions when setup is identical across 3+ tests; some duplication in test setup is acceptable for clarity (see DUP-10). Avoid deep fixture hierarchies

## Test Coverage & Gaps

- **TEST-5.** All public API functions must have at least one test
- **TEST-6.** Test error paths and edge cases, not just happy paths
- **TEST-7.** Complex functions (cyclomatic complexity >10, see FN-6) need at least one test per distinct branch or match arm — this applies even when FN-6 grants a structural complexity exception (e.g., state machines, exhaustive matches). FN-6 exceptions mean the complexity is acceptable and need not be refactored, but each branch/path still needs test coverage to prevent regressions. A complexity exception is not a testing exception
- **TEST-8.** Test boundary conditions: empty collections, zero values, max values, None variants

**TestGap heuristics** — when scanning for untested code, check for:

- Source files without any tests (no inline `#[cfg(test)]` module, no matching `tests/` integration test)
- Public API functions with no test anywhere in the suite
- Complex functions (cyclomatic complexity >10 per FN-6) without per-branch coverage
- Error paths (`Err` variants, `None` returns) not exercised in tests
- Boundary conditions (empty, zero, max, `None`) without specific tests

## Test Assertions & Quality

- **TEST-9.** Consider property-based tests (`proptest`, `quickcheck`) for: serialization round-trips (`decode(encode(x)) == x`), parser correctness (arbitrary input never panics), numeric invariants (commutative/associative properties), data structure invariants (sorted after insert, size consistency) — not required for all code; highest value where input space is large and edge cases are hard to enumerate manually
- **TEST-10.** `#[should_panic]` for expected panics; include `expected` message substring
- **TEST-11.** Assert specific values, not just `is_ok()` / `is_some()`; verify the actual result
- **TEST-12.** No redundant tests: identical logic, same paths, copy-paste with trivial differences. **This rule is the single authority for test duplication tolerance** (DUP-10 defers here): test setup boilerplate and similar-but-distinct scenarios have higher duplication tolerance than production code — only flag tests that are truly redundant in what they verify
- **TEST-29.** Prefer std `assert_matches!` / `debug_assert_matches!` (stable since Rust 1.96) over hand-rolled `matches!(x, P)` + `assert!` or `if let … else panic!` when asserting a value matches a pattern — it panics with the `Debug` representation of the actual value, giving a better failure message (extends TEST-11's "assert specific values" to enum-variant/pattern shape). Not in the prelude (it would collide with third-party crates of the same name), so import explicitly: `use std::assert_matches::assert_matches;`. Drop-in replacement for the popular `assert_matches` crate — flag that dependency for removal at MSRV ≥ 1.96. Check project MSRV before adopting

## Test Async & Concurrency

- **TEST-13.** `#[tokio::test]` + `tokio::time::pause()` for async/time tests (tokio-specific; other runtimes need different approaches — see [flakiness patterns](flakiness-patterns.md))
- **TEST-14.** Use `#[tokio::test(flavor = "multi_thread")]` as a race condition discovery tool — single-threaded flavor serializes tasks and hides data races; multi-threaded flavor exposes ordering-dependent bugs that only manifest under real concurrency
- **TEST-15.** Deterministic sync points over `sleep`-based waits

## Test Flakiness Prevention

See [flakiness patterns](flakiness-patterns.md) for detailed explanations and mitigations per pattern. Rules below are the enforceable checklist:

- **TEST-16.** Fixed seed for random-based tests; production code may use `thread_rng` per SEC-10, but tests must inject a seeded RNG for determinism
- **TEST-17.** No real network in unit tests; use `wiremock` or test doubles
- **TEST-18.** Isolated state per test; avoid `static mut` or shared fixtures that mutate
- **TEST-19.** Use `tempfile::tempdir()` for filesystem tests; no hardcoded paths
- **TEST-20.** Bind to port `0` instead of hardcoded ports — hardcoded ports cause collisions when CI runs tests in parallel (`cargo test` runs test binaries concurrently by default)
- **TEST-21.** Do not rely on thread or task scheduling order; use explicit synchronization (barriers, channels, `Notify`)

## Test Anti-Patterns

- **TEST-22.** Avoid excessive `clone()` or `unwrap()` in tests when they mask the intent; prefer `let val = result.expect("setup: reason")` for clarity
- **TEST-23.** Ensure shared global state has proper cleanup between test runs (use `Drop` guards, `tempdir`, or per-test isolation)

## Test Organization

- **TEST-24.** `#[ignore]` for slow tests; document why and how to run them. Acceptable: `#[ignore = "requires external DB, run with: cargo test -- --ignored"]`. Unacceptable: bare `#[ignore]` with no explanation (see TEST-26)
- **TEST-25.** No framework-only tests that only exercise external libraries without testing crate logic. Severity by ratio: mostly framework calls with no project logic = High; mixed (some project logic, mostly framework) = Medium; primarily project logic with framework setup = Low/ignore
- **TEST-26.** Remove or fix `#[ignore]`d tests with no explanation — ignored tests with a tracking issue or clear justification are Low severity; ignored tests without explanation are High severity (silent coverage loss, may hide regressions)

## Test Tooling

- **TEST-27.** Coverage measurement: `cargo tarpaulin` for quick local checks (easy setup, single command), `grcov` for CI pipelines (LLVM-based, more accurate, integrates with coverage services). Both identify untested paths; neither proves test quality — combine with TEST-28
- **TEST-28.** Mutation testing: `cargo-mutants` for validating test effectiveness — mutates source code (replaces operators, removes calls, changes returns) and re-runs tests; tests that still pass with mutations are weak. Interpret: focus on survived mutants in critical code paths; not all survived mutants are actionable (some mutations are semantically equivalent)
