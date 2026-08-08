# Rust Development Skills

A collection of [Agent Skills](https://agentskills.io/specification) for Rust development. Compatible with Claude Code, OpenAI Codex, Cursor, and other agent platforms.

## Overview

| Skill | Purpose |
|-------|---------|
| **code-review-rust** | Review Rust code for idioms, security, complexity, duplication, test quality, and NATS patterns. Writes one finding per markdown file to `.backlog/tasks/` |
| **code-review-triage** | Group triaged backlog findings into semantic review waves and create `code-review-plan-waveN` parent tasks |
| **code-review-run-wave** | Execute one planned review wave end-to-end in an isolated git worktree, apply fixes, run QA gates, merge it back, and close out the wave |
| **code-review-run-waves** | Run every open wave concurrently, one worktree each, and land them one at a time through a shared merge lock |
| **commit-script** | Analyze git state and generate a script that stages grouped files into conventional commits |
| **rust-meta** | Process external Rust content and integrate new knowledge into code-review-rust |

## Installation

### Option 1: Clone the Repository

```bash
git clone https://github.com/rsvalerio/skills.git
cd skills

# For Claude Code
cp -r skills/* .claude/skills/

# For OpenAI Codex
cp -r skills/* .codex/skills/
```

### Option 2: Install Individual Skills

Using the agent-skills-cli (see [agent-skills-cli docs](https://lib.rs/crates/agent-skills-cli)):

```bash
agent-skills install https://github.com/rsvalerio/skills/tree/main/skills/code-review-rust
```

After installing, restart your AI tool (Claude Code, Codex, etc.) to pick up the new skills.

## Requirements

- **AI Agent Tool**: Claude Code, OpenAI Codex, Cursor, or another Agent Skills-compatible platform
- For developing or validating skills locally: Git and Homebrew. See [AGENTS.md](AGENTS.md) for the full workflow.

## Usage

Once installed, your AI tool will use skills based on context. You can also invoke them explicitly.

### code-review-rust

Run a full review or focus on specific rule categories:

- "Run a code-review-rust on this crate."
- "Review this code for anti-patterns, ownership issues, and unsafe usage."
- "Check this module for security vulnerabilities and OWASP violations."
- "Analyze complexity and readability of this file."
- "Find duplicated logic between these two modules."
- "Review my tests for effectiveness, gaps, and flakiness."
- "Audit NATS consumer patterns against best practices."

Multiple instances can run in parallel against the same codebase -- each finding gets its own file in `.backlog/tasks/`.

### Implementation guardrail mode

Beyond formal reviews, `code-review-rust` can run as an *implementation guardrail* — load the rules *before* editing Rust code so violations never ship in the first place. To activate this mode deterministically (rather than relying on description-matching), wire one of:

- a Cursor rule at `.cursor/rules/rust-implementation-guardrail.mdc` with `globs: ["**/*.rs", "**/Cargo.toml"]`,
- a `CLAUDE.md` directive in your repo,
- or an `AGENTS.md` directive for Codex / other agents.

See [docs/implementation-guardrail.md](docs/implementation-guardrail.md) for per-agent activation snippets, the vendoring pattern for repos where the skill isn't installed, and verification steps.

### Running with CLI agents

```bash
# Full review (Claude Code --print mode)
claude --model opus -p "/code-review-rust @crates"

# Full review (opencode run)
opencode run "/code-review-rust @crates"
```

### Running review waves in parallel

`code-review-triage` groups findings into waves; each wave is then executed by
`code-review-run-wave`. Waves are isolated from one another with a **git worktree per
wave** — its own checkout, index, and pre-merge build — so several can run at once. Merges
are serialised through a lock so only one wave ever mutates the base branch.

```bash
# group triaged findings into waves (single-writer: let it finish first)
claude -p "/code-review-triage"

# run every open wave concurrently and land them one at a time
claude -p "/code-review-run-waves"

# or run a single wave
claude -p "/code-review-run-wave"
```

A wave that fails to merge **parks**: its worktree and branch are deliberately left in
place so the work is resumable, and the other waves carry on. See
[Worktree Protocol](skills/code-review-run-wave/references/worktree-protocol.md) for the
claiming, merging, and recovery procedures.

### rust-meta

- "Process this external Rust doc and integrate new knowledge into the rules."
- "Evaluate this blog post against our evaluation criteria."

## Resources

- [Agent Skills Specification](https://agentskills.io/specification)
- [Agent Skills Integration Guide](https://agentskills.io/integrate-skills)
- [Agent Skills Marketplace](https://skillsmp.com/)
- [openai/skills Repository](https://github.com/openai/skills)
- [skill-validator](https://github.com/agent-ecosystem/skill-validator) -- Validation tool for Agent Skills

## Contributing

To develop or contribute (validation, linting, publishing), see [AGENTS.md](AGENTS.md).

## License

All skills in this repository are licensed under Apache-2.0. See [LICENSE](LICENSE) for details.

## Support

- Issues: <https://github.com/rsvalerio/skills/issues>
- Discussions: <https://github.com/rsvalerio/skills/discussions>

## Acknowledgments

Based on [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/), [The Rust Book](https://doc.rust-lang.org/book/), [Rust By Example](https://doc.rust-lang.org/rust-by-example/), and community best practices.
