# Rust Code Review Rules

All rule IDs for the `code-review-rust` skill. Each finding references a rule ID from these rule files.

## Finding IDs and Categories

Findings are named after the **rule they violate** — e.g., a violation of `ERR-5` is written to `.backlog/tasks/ERR-5-<slug>.md` with `id: ERR-5` in the frontmatter. Multiple findings against the same rule get distinct slugs (`ERR-5-unwrap-in-http-handler.md`, `ERR-5-unwrap-in-parser.md`).

Rule IDs are grouped into the following categories (used for reporting and triage, not file naming):

| Category | Rule-ID prefixes | Domain | Detailed rules |
|----------|------------------|--------|----------------|
| Idioms & correctness | `OWN`, `ERR`, `TRAIT`, `CONC`, `ASYNC`, `PERF`, `UNSAFE`, `PATTERN`, `TIME`, `VER`, `EDITION` | Ownership, errors, traits, concurrency, async, performance, unsafe, patterns, date/time correctness, version-specific features | [rules-core.md](rules-core.md) |
| Structure & readability | `FN`, `READ`, `ARCH`, `API`, `CL` | Complexity, readability, architecture, API design, cognitive load | [rules-structure.md](rules-structure.md) |
| Duplication | `DUP` | Code duplication (production and test-helper) | [rules-duplication.md](rules-duplication.md) |
| Security | `SEC` | Security — maps to OWASP Top 10 (see `owasp-2021.md`) | [rules-security.md](rules-security.md) |
| Test quality | `TEST` | Test coverage, assertions, flakiness, organization | [rules-tests.md](rules-tests.md) |
| NATS / JetStream | `NATS` | `async-nats` patterns — see `nats-security.md` for security mapping | [rules-nats.md](rules-nats.md) |
| Classification notes | n/a | Severity adjustment and SEC/UNSAFE mapping guidance | [rules-classification.md](rules-classification.md) |

> `EDITION-*` rules are reference material, not finding-generating — the compiler and `cargo fix --edition` enforce them.

## Severity Scale

| Level | Meaning |
|-------|---------|
| Critical | Correctness risk, security issue, or silent data loss |
| High | Significant gap or reliability risk |
| Medium | Quality issue worth addressing |
| Low | Minor improvement or dormant concern |

## Design Philosophy

> "The best Rust APIs feel boring to use — one obvious correct way, every wrong attempt rejected at compile time."

- Prefer compile-time enforcement over runtime checks
- Use types to represent states, not flags
- Encode preconditions in the type system
- If documentation is required to prevent misuse, the API is fragile

Priority order: Safety > correctness > maintainability > style (maps to Critical > High > Medium > Low severity).
