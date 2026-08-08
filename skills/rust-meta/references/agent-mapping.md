# Skill Mapping

Map extracted knowledge to the appropriate location within code-review-rust:

| Target section | Knowledge types |
|----------------|------------------|
| **Idioms** (OWN, ERR, TRAIT, CONC, ASYNC, PERF, UNSAFE, PATTERN, EDITION, VER) | Anti-patterns, ownership/borrowing, errors, traits, concurrency, performance, unsafe usage, advanced patterns (typestate, phantom types), edition migration, version-specific features |
| **Code quality** (FN, READ, ARCH, API, CL) | Complexity, readability, architecture, cognitive load, API design |
| **Duplication** (DUP) | Duplication detection, refactoring, DRY |
| **Security** (SEC) | Security vulnerabilities, OWASP, crypto, memory safety, access control |
| **Test quality** (TEST) | Testing strategies, patterns, coverage, flakiness, organization |
| **NATS** (NATS) | NATS/JetStream patterns, async-nats configuration, consumers, backpressure, observability |

Rule categories are indexed in `code-review-rust/references/rules.md`, with detailed content in `code-review-rust/references/rules-*.md` files. If the user's project uses different skill names or files, map to the closest section.

## Rule numbering

When adding new rules, use the next available number in the target prefix range. Check the corresponding detailed file (`rules-core.md`, `rules-structure.md`, `rules-duplication.md`, `rules-security.md`, `rules-tests.md`, or `rules-nats.md`) for the current highest number in each prefix.

## Conditional routing

Some content requires context-aware placement within the rules file:

- **Unsafe code**: "safe abstraction over unsafe" (wrapping patterns, API design) → UNSAFE-1--8 section; "security exploit or memory safety violation" → SEC-1--4 section
- **Performance tips**: general optimization → PERF section; complexity/readability trade-offs of optimization → CL section
- **Error handling**: idiomatic patterns → ERR section; secret leakage or fail-open risks → SEC-21, SEC-31 section
