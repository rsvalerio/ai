# rsvalerio/ai

[![CI](https://github.com/rsvalerio/ai/actions/workflows/ci.yml/badge.svg)](https://github.com/rsvalerio/ai/actions/workflows/ci.yml)

A monorepo of AI tooling: [Agent Skills](https://agentskills.io/specification) grouped into Claude Code plugins, one per domain. Compatible with Claude Code, OpenAI Codex, Cursor, and other agent platforms.

## Overview

| Plugin | Path | Contents |
|--------|------|----------|
| **dev** | [`plugins/dev`](plugins/dev) | Rust and frontend development: code review, review-wave orchestration, Clippy and build-cost surveys, commit scripting. The nine skills below |
| **product** | [`plugins/product`](plugins/product) | Product and market research: product, vendor, license and business-model research. The skill below |

### dev skills

| Skill | Purpose |
|-------|---------|
| **code-review-rust** | Review Rust for idioms, security, complexity, duplication, test quality, and NATS patterns. One finding per file in `.backlog/tasks/`. Also answers ad-hoc reviews of pasted code in chat, with rule IDs, and works as an [implementation guardrail](docs/implementation-guardrail.md). |
| **code-review-web** | Review React/TypeScript (Vite) frontends for hooks, types, async, a11y, security, and tests. Same finding, ad-hoc review and guardrail pattern as the Rust skill. |
| **code-review-lovable** | Overlay on `code-review-web` for Lovable-style apps (shadcn/ui + Tailwind on Supabase or Lovable Cloud, TanStack Query, Zustand, zod, Shopify Storefront): RLS policies, supabase-js and GraphQL errors, Edge Function auth and value minting, cache keys, price truth, forms, design tokens, scaffold hygiene. |
| **code-review-triage** | Group triaged backlog findings into semantic review waves (`code-review-plan-waveN` parents). |
| **code-review-run-wave** | Run one planned wave in an isolated git worktree: apply fixes, QA, merge, close. |
| **code-review-run-waves** | Run every open wave concurrently (one worktree each); land merges one at a time via a shared lock. |
| **commit-script** | Analyze git state and generate a script that stages grouped files into conventional commits — optionally on a topic branch that ends in a `gh` pull request. |
| **rust-make-build-fast** | Survey a clean Rust checkout's build cost: profiles, gates, nextest, target directories, duplicate and unused dependencies, sccache hit rate. File one `build-fast` backlog task per finding with its measured cost, the date and machine load, classified `safe` or `trade-off`. Cold builds only with `--measure-cold`; with `--apply`, write the safe fixes (never the trade-offs). |
| **rust-make-clippy-pedantic** | Lint a clean Rust checkout at pedantic strength via flags and a scratch `clippy.toml` only, file one `pedantic`-labelled backlog task per warning — generated files and out-of-tree warnings dropped, the policy's four in-tests lints exempt in test code, high-volume lints aggregated per crate — estimate the cleanup, and show (or with `--apply`, write) the matching `Cargo.toml` / `clippy.toml` lint policy. |
| **rust-meta** | Process external Rust content and integrate new knowledge into `code-review-rust`. |

### product skills

| Skill | Purpose |
|-------|---------|
| **product-research** | Research a product from its name, URL or GitHub repo and record its feature coverage, vendor ownership and jurisdiction, and license and business model per component (open vs paid, self-hostable, license history, forks and rebuilds). Every claim carries its source, ref and date checked. Conventions come from the consuming repo's `.product-research.md` profile; with none, the skill stops and offers to scaffold one. Proposes in chat and writes only what was approved. |

## Installation

### Option 1: Claude Code Plugin Marketplace

The repository root is a plugin marketplace listing every plugin under `plugins/`. Install the ones you want; each is independent. Inside a plugin the skills ship together, because they reference each other's files (in `dev`, the review waves lean on the worktree protocol and rust-meta on the review rule set).

```bash
claude plugin marketplace add rsvalerio/ai
claude plugin install dev@rsvalerio
claude plugin install product@rsvalerio
```

Inside a session, `/plugin marketplace add rsvalerio/ai` and `/plugin install dev@rsvalerio` work the same way. Skills are invoked through the plugin namespace, e.g. `/dev:code-review-rust`, and track the latest commit on `main`; update with `claude plugin update dev@rsvalerio`.

### Option 2: Clone the Repository

```bash
git clone https://github.com/rsvalerio/ai.git
cd ai

# Claude Code
cp -r plugins/*/skills/* .claude/skills/

# OpenAI Codex
cp -r plugins/*/skills/* .codex/skills/
```

For a live symlink into `~/.claude/skills/` while developing this repo, use `make link` (see [AGENTS.md](AGENTS.md)).

### Option 3: Install Individual Skills

Using [agent-skills-cli](https://lib.rs/crates/agent-skills-cli):

```bash
agent-skills install https://github.com/rsvalerio/ai/tree/main/plugins/dev/skills/code-review-rust
```

Restart your AI tool after installing so it picks up the new skills.

## Requirements

- **AI agent**: Claude Code, OpenAI Codex, Cursor, or another Agent Skills-compatible platform
- **ops 0.74.0 or newer**: [`ops`](https://github.com/rsvalerio/ops) on PATH. Every skill that files findings uses `ops backlog` (a `.backlog/tasks/` directory in the target repo is all the setup it needs), with `--unless-exists` so a finding is filed once. The wave runners claim, lock, park and commit bookkeeping through `ops backlog wave` and `ops lock`. `rust-make-clippy-pedantic` lints through `ops clippy-findings`. `rust-make-build-fast` reads gate plans, machine state and duplicate dependencies through `ops explain` and `ops about`. Both Rust `--apply` modes take their templates from the Rust foundation that `ops init --rust` renders. Each skill checks `ops --version` first and stops if it is older
- **Developing this repo**: Git, plus `rumdl` and `skill-validator` at the versions pinned in [`.tool-versions`](.tool-versions) — `mise install` gets both, or `make install-tools` via Homebrew — and `claude-code` on PATH for `make validate-marketplace` (the asdf route is in [CONTRIBUTING.md](CONTRIBUTING.md)). Full workflow in [AGENTS.md](AGENTS.md)

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

### code-review-lovable

- "Run code-review-lovable and code-review-web on this Lovable app."
- "Check my Supabase migrations for RLS gaps."
- "Review this Edge Function before I ship it."

### Implementation guardrail mode

`code-review-rust` (and `code-review-web`) can load rules *before* edits so violations do not ship. Description-matching alone is best-effort; for deterministic activation, add a Cursor rule, `CLAUDE.md` directive, or `AGENTS.md` directive.

Full snippets, vendoring when the skill is missing, and verification: [docs/implementation-guardrail.md](docs/implementation-guardrail.md).

### CLI agents

```bash
claude --model opus -p "/code-review-rust @crates"
opencode run "/code-review-rust @crates"
```

### Review waves

`code-review-triage` groups findings into waves (`ops backlog wave create`) and records their overlap and merge order (`ops backlog wave overlap`); `code-review-run-wave` / `code-review-run-waves` execute them. Each wave gets its own git worktree (`ops backlog wave claim`); merges serialize through `ops lock code-review-merge`, which a killed runner cannot leave behind. A failed merge **parks** the worktree/branch (`ops backlog wave park`) so work stays resumable.

```bash
claude -p "/code-review-triage"       # finish triage first (single-writer)
claude -p "/code-review-run-waves"    # all open waves
claude -p "/code-review-run-wave"     # one wave
```

Details: [Worktree Protocol](plugins/dev/skills/code-review-run-wave/references/worktree-protocol.md).

### rust-make-clippy-pedantic

- "Run rust-make-clippy-pedantic on this workspace."
- "How much work is it to get this crate clippy-pedantic clean?"
- "Configure this workspace for pedantic clippy — show me the config first."

Requires a clean `git status`; the run aborts rather than stashing or pulling. The lint set
is the policy of the Rust foundation that ships with ops (`ops init --rust`, rendered into a
scratch crate), passed as `-W` flags after `--` rather than by editing the crate. Both passes run
through `ops clippy-findings`, which returns one normalized JSON row per diagnostic. What
keeps the run off your files is the rest of it: `--locked` so Cargo cannot write
`Cargo.lock`, a scratch `CARGO_TARGET_DIR` so `target/` is untouched, and no `--fix`. Findings are written
to `.backlog/`, which is the point.

The run finishes by printing the `Cargo.toml` lint tables and `clippy.toml` that would make
the strictness permanent: `[workspace.lints.*]` plus a `[lints] workspace = true` opt-in per
member for a workspace, or direct `[lints.rust]` / `[lints.clippy]` tables for a single
crate. Both come from the same foundation, and in a repository that already has them only
what `ops init --rust --check` reports as drift is shown. Pass `--apply` to have it write them — the only mode that edits checked-in lint
configuration, though every run writes its findings to `.backlog/`. Neither commits.

### rust-make-build-fast

- "Run rust-make-build-fast on this workspace."
- "Why is `ops verify` slow here? Survey it and file what you find."
- "Measure whether dependency opt-level is worth it — run rust-make-build-fast with `--measure-cold`."

Requires a clean `git status`. The default run is cheap: it reads `Cargo.toml` profiles,
cargo config and `.config/nextest.toml`, resolves gate plans with `ops explain` (which never
runs a step), lists fixable duplicate dependencies with `ops about dependencies --duplicates`,
and runs a warm `cargo build --timings` (twice: catch-up, then no-op) into your existing
`target/`, with machine state and sccache stats from `ops about machine` before and after. It never runs a cold build. Every timing is
recorded with the date, core count, load, `jobs` cap and compiler wrapper, because a build
number without them cannot be compared with the next one.

`--measure-cold` adds the cold builds that trade-off findings need. They go into a scratch
directory under `~/.cache`, never `/tmp` (a tmpfs `/tmp` fails a cold build with exit 101
and no compile error). The compiler cache is off, and alternatives are passed as
`--config` overrides, so no file is edited.

Findings are `safe` (nothing gets worse) or `trade-off` (for example, dependency
`opt-level` speeds the build but may slow the tests). `--apply` writes only the safe ones
that have a template, into the `Cargo.toml` test profile, `.ops.toml` and
`.config/nextest.toml`, and then verifies them. It never commits.

### rust-meta

- "Process this external Rust doc and integrate new knowledge into the rules."
- "Evaluate this blog post against our evaluation criteria."

### product-research

- "Research Tailscale and add it to our reference folder."
- "Update what we have on HashiCorp Vault — check whether the license changed."
- "Who owns this product and under whose law? <https://example.com>"

The skill needs a profile in the consuming repo: `.product-research.md` at the root, or a
`## Product research` section in `CLAUDE.md` / `AGENTS.md`. It declares where records go,
the coverage dimensions and markers, the scope map, depth tiers, jurisdiction policy and
search paths. Without one the skill stops before any research and offers to scaffold it,
asking for each section rather than guessing. It needs no `ops`.

Licenses are read from the LICENSE file at a pinned tag or commit, per component, never
from a badge; an unknown license is never recorded as permissive. Every claim carries its
source URL, ref and date checked, and every unknown names the check that would settle it.
Findings are proposed in chat, and only the approved edits are written.

## Resources

- [Agent Skills Specification](https://agentskills.io/specification)
- [Agent Skills Integration Guide](https://agentskills.io/integrate-skills)
- [Agent Skills Marketplace](https://skillsmp.com/)
- [openai/skills Repository](https://github.com/openai/skills)
- [skill-validator](https://github.com/agent-ecosystem/skill-validator)

## Contributing

Setup, gates, commit format, and pull request rules: [CONTRIBUTING.md](CONTRIBUTING.md).
Skill authoring conventions and publishing: [AGENTS.md](AGENTS.md).

`main` is protected: pull requests merge by squash only, need signed commits, and
must pass the `ops verify` and `ops qa` checks. Both run the same gates locally.

## License

Apache-2.0. See [LICENSE](LICENSE).

## Support

- Issues: <https://github.com/rsvalerio/ai/issues>

## Acknowledgments

Rust rules draw on the [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/),
[The Rust Book](https://doc.rust-lang.org/book/) and
[Rust By Example](https://doc.rust-lang.org/rust-by-example/). Frontend rules draw on the
[React documentation](https://react.dev/), the
[TypeScript handbook](https://www.typescriptlang.org/docs/handbook/intro.html) and the
[OWASP Top 10](https://owasp.org/www-project-top-ten/), alongside community best practices.
