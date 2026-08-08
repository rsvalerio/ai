# Duplication Rules — DUP

## Code Duplication (typical severity: Medium--High)

### Detection

> Thresholds are sensible defaults; adjust per project. Some duplication is cheaper than the wrong abstraction (DUP-9).

- **DUP-1.** Flag identical or near-identical code blocks of 5+ lines (copy-pasted logic, repeated JSX subtrees). Threshold is configurable — lower for critical code, higher for generated/boilerplate.
- **DUP-2.** Flag 3+ functions/components with the same structure differing only in literals, field names, or types — candidates for a generic helper, a shared component with props, or a custom hook.
- **DUP-3.** Flag copy-pasted network code: repeated `fetch` + URL building + `response.ok` check + JSON parse + error handling across call sites. Extract a single typed API client/module (the codebase's API layer, e.g. `library/api.ts`, is the reuse anchor).
- **DUP-4.** Flag duplicated type definitions: the same shape declared independently in multiple files (request/response bodies, props). Define once and import; derive related types with utility types (`Pick`, `Omit`, `Partial`) rather than re-declaring.
- **DUP-5.** Flag repeated stateful logic across components (the same `useState`/`useEffect` choreography) — extract a custom hook (REACT-8).

### Refactoring

- **DUP-6.** Extract shared JSX into a reusable component; pass variation as props/children.
- **DUP-7.** Extract shared stateful logic into a custom `use*` hook.
- **DUP-8.** Extract shared async/network logic into a typed API module; centralize base URL, headers, error mapping, and 401 handling.

### Judgment

- **DUP-9.** Context matters: a little duplication is better than a premature or wrong abstraction. Don't DRY two things that merely look alike today but evolve independently.
- **DUP-10.** Test code has higher duplication tolerance than production code (see TEST-12); prefer clarity over DRY in tests.
