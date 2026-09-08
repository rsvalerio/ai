# READ rules

> Thresholds below are industry-common defaults (Clean Code, cognitive-complexity research, Airbnb/typescript-eslint conventions). Adjust per project — the goal is flagging outliers for review, not rigid enforcement.

## Readability (typical severity: Low--Medium)

- **READ-1.** Prefer clarity over cleverness: explicit > implicit, familiar React/TS patterns > obscure type-level gymnastics, readability > brevity.
- **READ-2.** Break dense expressions into named intermediate variables; name the steps of long array-method chains (`const visible = items.filter(...).map(...)`) or use an explicit loop when a chain exceeds ~3--4 operations or mixes control flow with transformation.
- **READ-3.** Use descriptive, consistent names. Components `PascalCase`; hooks `useCamelCase`; event handlers `handleX`/`onX`; booleans `is/has/should/can`. Avoid abbreviations and single-letter names outside trivial scopes.
- **READ-4.** No magic numbers or magic strings — extract to named constants (`const CURSOR_THROTTLE_MS = 33;`), especially for timing, sizes, status codes, storage keys, and protocol event names. Repeated string literals used as keys/discriminants should be a `const`/union.
- **READ-5.** Remove dead code: unused imports, variables, params, components, commented-out blocks, and unreachable branches. *(Partly enforced by `noUnusedLocals`/`noUnusedParameters` and ESLint.)*
- **READ-6.** Document "why", not "what". Comment non-obvious decisions (why a throttle interval, why a cast is safe, why an Effect dependency is intentionally omitted) — not restatements of the code.
- **READ-7.** Use consistent patterns for similar problems across the codebase (one fetch/error pattern, one way to read config, one toast/notification path).
- **READ-8.** No `console.log`/`console.debug`/`console.info` in production (non-test) code — leftover logs leak data and clutter the console. Use a real logger or remove them. `console.error`/`console.warn` in genuine error paths are acceptable but should not include secrets/PII (see SEC-13).
  **Scanning guidance:** exclude test files, dev-only debug utilities gated behind `import.meta.env.DEV`, and config/build scripts before counting.
