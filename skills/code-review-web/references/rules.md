# Web Code Review Rules

All rule IDs for the `code-review-web` skill. Each finding references a rule ID from these rule files. Targets React 19 + TypeScript 5.x + Vite + Vitest single-page applications.

## Finding IDs and Categories

Findings are named after the **rule they violate** — e.g., a violation of `TS-1` is written to `.backlog/tasks/TS-1-<slug>.md` with `id: TS-1` in the frontmatter. Multiple findings against the same rule get distinct slugs (`TS-1-any-in-api-client.md`, `TS-1-any-in-collab.md`).

Rule IDs are grouped into the following categories (used for reporting and triage, not file naming):

| Category | Rule-ID prefixes | Domain | Detailed rules |
|----------|------------------|--------|----------------|
| React idioms & correctness | `REACT` | Hooks, effects, memoization (Compiler era), Actions/`use()`, components, keys, state | [rules-core.md](rules-core.md) |
| TypeScript type safety | `TS` | `any`/`unknown`, assertions, strict flags, discriminated unions, branding, exhaustiveness | [rules-core.md](rules-core.md) |
| Async & error handling | `ASYNC` | Promises, fetch, abort, race conditions, error boundaries, loading/error states | [rules-core.md](rules-core.md) |
| Performance | `PERF` | Re-renders, context stability, expensive compute, virtualization, code splitting | [rules-core.md](rules-core.md) |
| Accessibility | `A11Y` | Semantics, ARIA, keyboard, labels/alt text | [rules-core.md](rules-core.md) |
| Structure & readability | `FN`, `READ`, `ARCH`, `API` | Complexity, readability, architecture, component API design | [rules-structure.md](rules-structure.md) |
| Duplication | `DUP` | Repeated JSX, logic, fetch, and type definitions | [rules-duplication.md](rules-duplication.md) |
| Security | `SEC` | XSS, Web Crypto, secrets, network, build — maps to OWASP Top 10 (see `owasp-2025.md`) | [rules-security.md](rules-security.md) |
| Test quality | `TEST` | Coverage, assertions, query practices, flakiness (Vitest + React Testing Library) | [rules-tests.md](rules-tests.md) |
| Real-time | `RT` | socket.io-client / WebSocket — see `rules-realtime.md`; security maps to SEC | [rules-realtime.md](rules-realtime.md) |
| Classification notes | n/a | Severity adjustment and justified-violation guidance | [rules-classification.md](rules-classification.md) |

> Many `REACT`, `TS`, and `ASYNC` rules are partly enforced by `eslint-plugin-react-hooks` v7, `typescript-eslint`, and `tsc --strict`. Those tools are the machine-enforced baseline — file findings only for what the project's configured tooling does not already catch (severity nuance, design smells, unenabled rules). See [SKILL.md](../SKILL.md#relationship-to-eslint--tsc-machine-enforced-baseline).

## Severity Scale

| Level | Meaning |
|-------|---------|
| Critical | Security issue, correctness risk, or silent data loss reachable in production |
| High | Significant gap or reliability risk |
| Medium | Quality issue worth addressing |
| Low | Minor improvement or dormant concern |

## Design Philosophy

> "Make illegal states unrepresentable, push checks to compile time and lint, and keep effects for synchronization — not for logic the UI already expresses."

- Prefer compile-time (types) and lint-time enforcement over runtime checks
- Model state as discriminated unions, not loose boolean/optional flags
- Treat `useEffect` as a last resort for synchronizing with external systems, not as a place to compute values or run event logic
- Never trust data crossing a boundary (network, WebSocket, URL, `localStorage`, user input) — validate it
- If documentation is required to use a component or hook safely, the API is fragile

Priority order: Safety/security > correctness > maintainability > style (maps to Critical > High > Medium > Low severity).
