# Test Quality Rules — TEST

Grounded in vitest.dev, testing-library.com (esp. Kent C. Dodds, "Common Mistakes with React Testing Library"), and MSW docs. For root-cause explanations of flaky tests see [flakiness-patterns.md](flakiness-patterns.md).

## Test Structure & Behavior

- **TEST-1.** Every test must have a meaningful assertion; no assertion-free tests that only render or call a function.
  **Scanning guidance:** a naive search for `expect(` misses real assertions. Treat each of these as an assertion: a call to an `assert*`/`expect*` helper, a `.rejects`/`.resolves` matcher, a `findBy*` query (it throws if not found — but prefer an explicit assertion too), and `expect(...).toThrow()`. A test that renders and queries without any `expect`/matcher is a real TEST-1 candidate — verify at the source line and prefer a `file:line` list over a raw count.
- **TEST-2.** Test behavior, not implementation details. Don't assert on component internal state, instance methods, hook internals, CSS class names as logic, or `data-testid` as the primary contract — query and assert the way a user perceives the UI. — kentcdodds.com/blog/testing-implementation-details
- **TEST-3.** Use the React Testing Library query priority: `getByRole` (with name) > `getByLabelText` > `getByPlaceholderText` > `getByText` > `getByDisplayValue`, and `getByTestId` only as a last resort. Reaching for `getByTestId`/`container.querySelector` where a role/label query fits is a finding. — testing-library.com/docs/queries/about/#priority
- **TEST-4.** Use `@testing-library/user-event` over `fireEvent` for user interactions — `userEvent` simulates real event sequences (focus, keydown, input) that `fireEvent` skips. — testing-library.com/docs/user-event/intro
- **TEST-5.** Cover every security-critical and logic-critical unit with at least one test: crypto round-trips (`decrypt(encrypt(x)) === x`), parsers/validators (fragment/URL/response parsing), auth/permission logic, and reducers. In a codebase with no tests, missing coverage of these units is the primary TEST finding.
- **TEST-6.** Test error and edge paths, not just the happy path: 4xx/5xx responses, empty/zero/max inputs, malformed data, aborted requests, and the loading/error UI states (ASYNC-7).

## Test Async & Determinism

- **TEST-7.** For async UI use `findBy*` / `await waitFor(...)` to await appearance; do not wrap interactions in manual `act()` — RTL's `userEvent`/`findBy` handle `act` for you, and a manual `act()` warning usually signals an un-awaited update. — testing-library.com/docs/dom-testing-library/api-async
- **TEST-8.** `waitFor` callbacks must contain a single assertion and **no side effects** (don't fire events or call APIs inside `waitFor`); side effects run repeatedly until timeout and cause flakiness. — kentcdodds.com/blog/common-mistakes-with-react-testing-library
- **TEST-9.** Make tests deterministic: fake timers (`vi.useFakeTimers()`) for throttle/debounce/`setTimeout` logic, fixed seeds/inputs, and no dependence on wall-clock or `Date.now()`/`Math.random()` without control. Restore timers/mocks after each test. — vitest.dev/api/vi (fake timers)
- **TEST-10.** Mock network with MSW (Mock Service Worker) at the network boundary rather than monkey-patching `fetch`/modules ad hoc; MSW tests the real request path and survives refactors. Never let unit/component tests hit a real network. — mswjs.io, testing-library.com guiding-principles

## Test Hygiene

- **TEST-11.** Assert specific values, not just truthiness — verify the actual rendered text/value/call arguments, not merely that an element exists or a function "was called".
- **TEST-12.** No redundant tests (identical logic with trivial differences). Test code tolerates more duplication than production for clarity (DUP-10), but truly copy-pasted assertions verifying the same thing should be parameterized or removed.
- **TEST-13.** Ensure isolation and cleanup between tests: rely on RTL auto-cleanup, reset module/handler/mocks state (`vi.restoreAllMocks()`, MSW `server.resetHandlers()`), and avoid shared mutable state or order-dependent tests. — testing-library.com/docs/react-testing-library/api#cleanup
- **TEST-14.** Avoid snapshot overuse — large/auto-updated snapshots assert nothing meaningful and get blindly re-recorded. Prefer targeted assertions; reserve snapshots for small, stable, intentional output. — kentcdodds.com/blog/effective-snapshot-testing
- **TEST-15.** No skipped/`.skip`/`.todo`/`.only` tests left in the suite without explanation; a bare skip is silent coverage loss, and a stray `.only` disables the rest of the file. Document why a test is skipped and how to run it.

## Test Tooling

- **TEST-16.** Track coverage of critical paths (Vitest `--coverage` via v8/istanbul) but treat coverage as a gap-finder, not a quality proof — combine with meaningful assertions (TEST-1, TEST-11). — vitest.dev/guide/coverage
