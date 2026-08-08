# Classification Guide

Detailed indicators and severity guide for classifying test issues. For enforceable rules, see TEST rules in [rules.md](rules.md).

## Classification Indicators

Concrete symptoms to look for when classifying test issues:

- **Useless**: test body lacks `assert!`/`assert_eq!`/`assert_ne!`; test only instantiates objects without verifying behavior; test catches errors but doesn't check the error variant or message; test always passes regardless of implementation changes
- **Redundant**: multiple tests with similar or identical names; duplicated inline `#[cfg(test)]` modules; tests that exercise the exact same code path with trivially different inputs (same branch, same outcome)
- **FrameworkOnly**: imports exclusively from third-party crates with no `crate::` references; tests that verify HTTP client behavior, serde round-trips on external types, or database driver functionality without project-specific logic
- **TestGap**: source files in `src/` without any test coverage (no inline `#[cfg(test)]`, no matching integration test); public API functions with zero tests; error handling paths (`Err` variants, `None` returns) never exercised; complex match arms without per-branch tests
- **Flaky**: tests using randomness without fixed seeds; `thread::sleep` or `tokio::time::sleep` with real durations; tests depending on external services or network; shared mutable state (`static mut`, global singletons) without isolation; tests relying on task/thread scheduling order

## Quick Classification Checklist

When evaluating a test, ask:

1. Does it exercise **project logic** (`crate::`) or only external libraries?
2. Are assertions **meaningful** — testing outcomes, not just success status?
3. Does another test verify **identical behavior** and paths?
4. Are **edge cases**, error paths, and boundaries tested?
5. Does it exhibit **flakiness patterns** (randomness, timing, shared state, concurrency)?

## Classification Severity Guide

| Classification | High | Medium | Low |
|---|---|---|---|
| **Useless** | Creates false confidence in coverage metrics | Adds noise to test suite (no assertions, always passes) | Temporarily disabled with tracking issue |
| **Redundant** | Masks missing coverage (appears covered but tests same path as another) | Maintenance burden without unique value | Minor overlap with another test (slightly different setup) |
| **FrameworkOnly** | Only tests in a critical module (no project logic coverage at all) | Mixed: some project logic, mostly framework calls | Incidental framework testing alongside real logic |
| **TestGap** | Public API or safety-critical code with zero coverage | Error paths or complex branches untested | Edge cases on non-critical paths |
| **Flaky** | Masks real bugs; fails randomly in CI (erodes trust) | Known source, non-critical path | Rare, well-documented, tracked for fix |
