# Development Skills

[![CI](https://github.com/rsvalerio/ai/actions/workflows/ci.yml/badge.svg)](https://github.com/rsvalerio/ai/actions/workflows/ci.yml)

A collection of [Agent Skills](https://agentskills.io/specification) for Rust and frontend development. Compatible with Claude Code, OpenAI Codex, Cursor, and other agent platforms.

## Overview

| Skill | Purpose |
|-------|---------|
| **code-review-rust** | Review Rust for idioms, security, complexity, duplication, test quality, and NATS patterns. One finding per file in `.backlog/tasks/`. Also usable as an [implementation guardrail](docs/implementation-guardrail.md). |
| **code-review-web** | Review React/TypeScript (Vite) frontends for hooks, types, async, a11y, security, and tests. Same finding and guardrail pattern as the Rust skill. |
| **code-review-triage** | Group triaged backlog findings into semantic review waves (`code-review-plan-waveN` parents). |
| **code-review-run-wave** | Run one planned wave in an isolated git worktree: apply fixes, QA, merge, close. |
| **code-review-run-waves** | Run every open wave concurrently (one worktree each); land merges one at a time via a shared lock. |
| **commit-script** | Analyze git state and generate a script that stages grouped files into conventional commits. |
| **rust-meta** | Process external Rust content and integrate new knowledge into `code-review-rust`. |

## Installation

### Option 1: Clone the Repository

```bash
git clone https://github.com/rsvalerio/ai.git
cd ai

# Claude Code
cp -r skills/* .claude/skills/

# OpenAI Codex
cp -r skills/* .codex/skills/
```

For a live symlink into `~/.claude/skills/` while developing this repo, use `make link` (see [AGENTS.md](AGENTS.md)).

### Option 2: Install Individual Skills

Using [agent-skills-cli](https://lib.rs/crates/agent-skills-cli):

```bash
agent-skills install https://github.com/rsvalerio/ai/tree/main/skills/code-review-rust
```

Restart your AI tool after installing so it picks up the new skills.

## Requirements

- **AI agent**: Claude Code, OpenAI Codex, Cursor, or another Agent Skills-compatible platform
- **Developing this repo**: Git, Homebrew; full workflow in [AGENTS.md](AGENTS.md)

## Usage

Skills load from context or explicit invocation.

### code-review-rust

- "Run a code-review-rust on this crate."
- "Review this code for anti-patterns, ownership issues, and unsafe usage."
- "Check this module for security vulnerabilities and OWASP violations."
- "Analyze complexity and readability of this file."
- "Find duplicated logic between these two modules."
- "Review my tests for effectiveness, gaps, and flakiness."
- "Audit NATS consumer patterns against best practices."

Parallel instances are fine — each finding is its own file under `.backlog/tasks/`.

### code-review-web

- "Run a code-review-web on this frontend."
- "Review these React components for hooks and accessibility issues."
- "Check this Vite app for XSS and Web Crypto misuse."

### Implementation guardrail mode

`code-review-rust` (and `code-review-web`) can load rules *before* edits so violations do not ship. Description-matching alone is best-effort; for deterministic activation, add a Cursor rule, `CLAUDE.md` directive, or `AGENTS.md` directive.

Full snippets, vendoring when the skill is missing, and verification: [docs/implementation-guardrail.md](docs/implementation-guardrail.md).

### CLI agents

```bash
claude --model opus -p "/code-review-rust @crates"
opencode run "/code-review-rust @crates"
```

### Review waves

`code-review-triage` groups findings into waves; `code-review-run-wave` / `code-review-run-waves` execute them. Each wave gets its own git worktree; merges serialize through a lock. A failed merge **parks** the worktree/branch so work stays resumable.

```bash
claude -p "/code-review-triage"       # finish triage first (single-writer)
claude -p "/code-review-run-waves"    # all open waves
claude -p "/code-review-run-wave"     # one wave
```

Details: [Worktree Protocol](skills/code-review-run-wave/references/worktree-protocol.md).

### rust-meta

- "Process this external Rust doc and integrate new knowledge into the rules."
- "Evaluate this blog post against our evaluation criteria."

## Resources

- [Agent Skills Specification](https://agentskills.io/specification)
- [Agent Skills Integration Guide](https://agentskills.io/integrate-skills)
- [Agent Skills Marketplace](https://skillsmp.com/)
- [openai/skills Repository](https://github.com/openai/skills)
- [skill-validator](https://github.com/agent-ecosystem/skill-validator)

## Contributing

Validation, linting, conventions, and publishing: [AGENTS.md](AGENTS.md).

## License

Apache-2.0. See [LICENSE](LICENSE).

## Support

- Issues: <https://github.com/rsvalerio/ai/issues>
- Discussions: <https://github.com/rsvalerio/ai/discussions>

## Acknowledgments

Based on [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/), [The Rust Book](https://doc.rust-lang.org/book/), [Rust By Example](https://doc.rust-lang.org/rust-by-example/), and community best practices.
