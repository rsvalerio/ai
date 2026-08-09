# Implementation Guardrail Activation

`code-review-rust` has two modes:

1. **Formal review** (default) — scan, file backlog findings, exit. Review-shaped prompts ("review this crate", "audit our NATS usage").
2. **Implementation guardrail** — read the rules *before* writing or editing Rust, treat them as acceptance criteria, and do not file backlog tasks unless the user asked for a formal review.

Use both: the guardrail stops known violations from shipping; formal review catches drift and subtle cross-rule issues. Install and invoke the skill via the repository [README](../README.md). This document is only about *activating* guardrail mode deterministically.

## Why explicit activation

Skill auto-load via description matching is best-effort. Fresh sessions, vague prompts, and platform-specific token weighting can miss the skill. Explicit activation (`CLAUDE.md`, `AGENTS.md`, or a Cursor rule) is the contract; the skill description is a hint.

## Quick start

1. **Install** the skill ([README installation](../README.md#installation)). Confirm with `ls ~/.claude/skills/code-review-rust/SKILL.md` (or your platform's path).
2. **Add an activation directive** (wire several if the team uses multiple agents):
   - **Cursor** → `.cursor/rules/rust-implementation-guardrail.mdc` (snippet below).
   - **Claude Code** → append the Claude Code snippet to the project's `CLAUDE.md`.
   - **Codex / `AGENTS.md` agents** → append the Codex snippet to the project's `AGENTS.md`.
3. **(Recommended) Vendor binding rules** — copy the subset from [When the skill might not be installed](#when-the-skill-might-not-be-installed) into consumer `AGENTS.md` so CI / fresh clones still get the highest-severity rules.
4. **Verify** — ask: *"What guardrails apply to Rust changes in this repo?"* Expect `code-review-rust` and at least one rule ID (e.g. ERR-5, UNSAFE-1).

No new commands: normal Rust edits should load the skill; keep using `cargo fmt` / `cargo clippy` / `cargo test` as usual.

## Cursor

Create `.cursor/rules/rust-implementation-guardrail.mdc` in the consumer repo:

```markdown
---
description: Apply code-review-rust rules as implementation guardrails on Rust edits
globs:
  - "**/*.rs"
  - "**/Cargo.toml"
  - "**/Cargo.lock"
alwaysApply: false
---

Before making non-trivial changes to Rust code, read the `code-review-rust` Agent
Skill (typically installed at `~/.claude/skills/code-review-rust/SKILL.md`) and
treat its `references/rules.md` rules as acceptance criteria for your change.

Do **not** introduce new violations of any rule in:

- `references/rules-core.md` (OWN, ERR, TRAIT, CONC, ASYNC, PERF, UNSAFE, …)
- `references/rules-security.md` (SEC)
- `references/rules-tests.md` (TEST)
- `references/rules-nats.md` (NATS / JetStream)

Do **not** file backlog tasks during implementation — the rules apply as
guardrails only. Reserve `backlog task create` for explicit formal-review
prompts.

After substantive edits, run the project's Rust QA gates:

- `cargo fmt`
- `cargo clippy --all-targets --workspace -- -D warnings`
- `cargo test --workspace`
```

`globs` attaches the rule on Rust touches without `alwaysApply: true` polluting other contexts. Cursor evaluates globs deterministically, unlike skill description matching.

## Claude Code

Add to the repo's `CLAUDE.md` (create if missing), near the top so it stays in context:

```markdown
## Rust implementation guardrails

For any non-trivial Rust change, read the `code-review-rust` skill *before*
editing and follow its rules as acceptance criteria. Do not file backlog tasks
during implementation — that mode is for formal reviews only.

Run `cargo fmt`, `cargo clippy --all-targets --workspace -- -D warnings`, and
`cargo test --workspace` before declaring the change done.
```

## Codex / generic AGENTS.md

```markdown
## Rust implementation guardrails

When editing Rust code, follow the rules in the `code-review-rust` Agent Skill
(<https://github.com/rsvalerio/skills/tree/main/skills/code-review-rust>). The
full rule index is at `references/rules.md`.

Treat each rule as an acceptance criterion, not a post-hoc check. Run
`cargo fmt`, `cargo clippy --all-targets --workspace -- -D warnings`, and
`cargo test --workspace` before finishing.
```

## When the skill might not be installed

If the skill is not guaranteed (CI agents, fresh clones, alternate tooling), vendor a short binding subset into the consumer `AGENTS.md`:

```markdown
## Rust binding rules (subset of code-review-rust)

These are the highest-severity rules from the `code-review-rust` skill. Even
without the skill installed, these apply unconditionally:

- **ERR-1** — Propagate with `?`; handle or propagate, never both. Don't both
  log and propagate the same error.
- **ERR-5** — No `unwrap`/`expect` in non-test code without an `// SAFETY:`
  justification. (`#[cfg(test)]`, `tests/`, and `test-support` gates are
  exempt.)
- **ERR-10** — Never use `Result<T, String>`; use a domain error enum.
- **UNSAFE-1** — All `unsafe` blocks have a `// SAFETY:` comment justifying
  every invariant relied upon.
- **CONC-2** — Hold locks briefly; never across `.await`.
- **CONC-5** — No `std::thread::sleep` or other blocking calls inside
  `async fn` — use `tokio::time::sleep`, `tokio::fs::*`, or
  `tokio::task::spawn_blocking`.
- **SEC-5** — Secret-bearing types disable `Debug`/`Clone` and zeroize on drop.
- **NATS-1** — All NATS connections use `ConnectOptions::new()` (timeouts,
  reconnect, TLS) — not bare `connect()`.
- **TEST-1** — Every test has at least one meaningful assertion. Empty bodies
  and assertion-free tests are not tests.

Full rule catalog (when installed): see the `code-review-rust` skill's
`references/rules.md`.
```

The vendored list is the binding contract; the skill is deeper guidance. Update the subset when canonical rules in `code-review-rust` change.

## Verification

1. Open a Rust file in the consumer repo.
2. Ask: *"What guardrails apply to Rust changes in this repo?"*
3. Expect `code-review-rust` (or the vendored summary) plus at least one rule ID.
4. If not: check rule/`CLAUDE.md`/`AGENTS.md` location and frontmatter, and that the skill is installed (`ls ~/.claude/skills/code-review-rust/`).

## What this is not

- Not a replacement for periodic formal review.
- Not a reason to file backlog tasks during implementation (see Applicability in `code-review-rust/SKILL.md`).
- Not a linter — still run `cargo fmt` / `clippy` / `test`. The skill covers what tools express poorly (architecture, severity nuance, NATS patterns, security classification).

## See also

- [`code-review-rust` skill](../skills/code-review-rust/SKILL.md)
- [`references/rules.md`](../skills/code-review-rust/references/rules.md) — rule index
- [Agent Skills specification](https://agentskills.io/specification)
