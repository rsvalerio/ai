# Implementation Guardrail Activation

The `code-review-rust` skill ships with two complementary modes:

1. **Formal review mode** (default) — scan a codebase, file findings as backlog tasks, and exit. Triggered by review-shaped prompts ("review this crate", "audit our NATS usage").
2. **Implementation guardrail mode** — read the rules *before* writing or editing Rust code, then keep the change within those constraints. Treats rules as acceptance criteria rather than post-hoc findings.

Implementation guardrail mode prevents violations from shipping. Formal review mode catches them after the fact. Use both — the guardrail keeps reviews focused on subtle issues instead of repeating yesterday's `unwrap` discussion.

This document covers how to wire up implementation guardrail mode in each agent platform.

## Quick start: setting up in your Rust project

If you just want to wire `code-review-rust` into a Rust project of your own, this is the minimum setup. Beyond installing the skill itself, you only need to add a short activation directive to your project's agent config so the skill loads on Rust edits instead of relying on description-matching.

1. **Install the skill.** See the repository [README](../README.md#installation). Confirm with `ls ~/.claude/skills/code-review-rust/SKILL.md` (or your platform's equivalent install location).
2. **Add an activation directive to your project**, choosing at least one — wire several if your team uses multiple agents:
  - **Cursor users** → create `.cursor/rules/rust-implementation-guardrail.mdc` using the snippet in the *Cursor* section below.
  - **Claude Code users** → append the snippet from the *Claude Code* section below to your project's `CLAUDE.md` (create the file if it doesn't exist).
  - **Codex and other `AGENTS.md`-aware agents** → append the snippet from the *Codex / generic AGENTS.md* section below to your project's `AGENTS.md`.
3. **(Recommended) Vendor a binding-rules subset.** Copy the block from the *When the skill might not be installed* section into your `AGENTS.md`. This makes the highest-severity rules apply unconditionally — even on CI runners, fresh clones, or machines where the skill isn't installed.
4. **Verify.** Open a `.rs` file and ask the agent: *"What guardrails apply to Rust changes in this repo?"*. It should cite `code-review-rust` and at least one specific rule ID (e.g., ERR-5, UNSAFE-1). See the *Verification* section for the full check.
5. **Use it.** The next time you ask the agent to write or edit Rust, it will read the rules first and treat them as acceptance criteria — no new commands to learn. Run your usual `cargo fmt` / `cargo clippy` / `cargo test` gates as you would normally; the skill complements them, it doesn't replace them.

The rest of this document is the per-platform reference: full snippets, rationale for each choice, and edge cases.

## Why explicit activation matters

Agent Skills are auto-loaded via description-matching heuristics. The `code-review-rust` description was widened on 2026-05-05 to include "implementation guardrail" and authoring-time keywords, but matching is still best-effort:

- A prompt like *"add a JetStream consumer"* should match, but won't always.
- Fresh sessions with no prior context may miss the trigger.
- Different agent platforms weight description tokens differently.

Explicit activation — via `CLAUDE.md`, `AGENTS.md`, or a Cursor rule — bypasses the matcher and makes the skill load deterministically when Rust files are touched. Treat the description as a hint and the explicit activation as the contract.

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

The `globs` field ensures the rule attaches whenever a Rust file is touched, without `alwaysApply: true` polluting non-Rust contexts. This is the most reliable activation method for IDE work because Cursor evaluates globs deterministically rather than via skill description matching.

## Claude Code

Add to your repo's `CLAUDE.md` (create if missing):

```markdown
## Rust implementation guardrails

For any non-trivial Rust change, read the `code-review-rust` skill *before*
editing and follow its rules as acceptance criteria. Do not file backlog tasks
during implementation — that mode is for formal reviews only.

Run `cargo fmt`, `cargo clippy --all-targets --workspace -- -D warnings`, and
`cargo test --workspace` before declaring the change done.
```

Place this near the top of `CLAUDE.md` so it is always in context. `CLAUDE.md` is loaded into every Claude Code conversation, so unlike skill auto-matching, this directive fires deterministically.

## Codex / generic AGENTS.md

Same pattern, in `AGENTS.md`:

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

If the consumer repo runs in environments where the skill isn't guaranteed (CI agents, fresh clones, alternate AI tooling), don't rely on the skill alone. Vendor a short binding-rules summary directly into the consumer repo's `AGENTS.md`:

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

The vendored list is the binding contract; the skill is the deeper guidance. Update the vendored summary if the canonical rules in `code-review-rust` change.

## Verification

After wiring up activation, confirm it's working:

1. Open a Rust file in the consumer repo.
2. Ask the agent: *"What guardrails apply to Rust changes in this repo?"*
3. The agent should mention `code-review-rust` (or your vendored summary) and at least one specific rule ID.
4. If it doesn't, the rule, `CLAUDE.md`, or `AGENTS.md` isn't being picked up — check file location, frontmatter syntax, and that the skill is actually installed (`ls ~/.claude/skills/code-review-rust/`).

## What this is not

- Implementation guardrail mode does **not** replace formal review. Periodic full reviews still catch architectural drift and rule interactions that single-edit guardrails miss.
- It does **not** mean filing tasks during implementation. The skill explicitly tells the agent: *"do not create backlog tasks unless the user explicitly asked for a formal review"* (see `code-review-rust/SKILL.md`, Applicability section).
- It does **not** lint code. The QA gates (`cargo fmt`, `cargo clippy`, `cargo test`) still run separately. The skill complements them by covering rules tools can't easily express (architectural, severity-nuanced, NATS-pattern, security-classification).

## See also

- [`code-review-rust` skill](../skills/code-review-rust/SKILL.md) — the skill itself, with the full Applicability section.
- [`references/rules.md`](../skills/code-review-rust/references/rules.md) — canonical rule index.
- [Agent Skills specification](https://agentskills.io/specification) — for general skill activation semantics.
