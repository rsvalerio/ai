# Instructions for AI Agents

How to work in this repository: skill conventions, development workflow, validation, and publishing. For install and usage as a skill *consumer*, see [README.md](README.md). For wiring `code-review-rust` as an implementation guardrail in a consumer repo, see [docs/implementation-guardrail.md](docs/implementation-guardrail.md).

## Project Overview

This repo is a collection of [Agent Skills](https://agentskills.io/specification). Skills live under `skills/`; each skill is a directory with `SKILL.md`, optional `references/*.md`, and optional `assets/openai.yaml`.

```text
.
├── README.md                 # Users: install, use, overview
├── AGENTS.md                 # This file: contributor / agent instructions
├── docs/
│   └── implementation-guardrail.md  # Consumer activation for guardrail mode
├── Makefile                  # validate, lint, link/unlink
├── skills/                   # One directory per skill
│   ├── code-review-rust/
│   ├── code-review-web/
│   ├── code-review-triage/
│   ├── code-review-run-wave/
│   ├── code-review-run-waves/
│   ├── commit-script/
│   └── rust-meta/
└── LICENSE
```

Skill purposes are listed in the [README overview](README.md#overview). Relationships that matter when editing skills:

- **code-review-rust** / **code-review-web** — formal review and implementation-guardrail engines. Rule categories are indexed in `references/rules.md` and detailed in `references/rules-*.md`.
- **code-review-triage** — groups `Triage` backlog findings into `code-review-plan-waveN` parents and stamps file scope via `--modified-file` for merge ordering.
- **code-review-run-wave** — claims one open wave, applies fixes in an isolated git worktree, runs QA, merges under a shared lock. Protocol: `skills/code-review-run-wave/references/worktree-protocol.md`.
- **code-review-run-waves** — fans out across open waves; delegates per-wave work to `code-review-run-wave`.
- **commit-script** — groups related files into conventional commit scripts. Two modes: `commit` (default, local commits only — what the wave runners use) and `pr` (topic branch + push + `gh pr create`).
- **rust-meta** — maps external Rust knowledge into `code-review-rust`.

### Finding output

`code-review-rust` and `code-review-web` write one markdown file per finding under `.backlog/tasks/` as `<PREFIX>-<N>-<slug>.md` (YAML frontmatter + body). Parallel skill runs are fine — one file per finding. Every finding must record one `--modified-file` per touched path (repo-root-relative, no line numbers) so triage can compute wave scope and merge order.

## Skill Conventions

### Directory layout

```text
skill-name/
├── SKILL.md                 # Required: YAML frontmatter + instructions
├── assets/
│   └── openai.yaml          # Optional: UI metadata for compatible products
└── references/
    └── *.md                 # Optional: on-demand detail (Title Case H1s)
```

Frontmatter `name` must match the parent directory name (e.g. `code-review-rust`). Prefer keeping `SKILL.md` under ~500 lines; put detail in `references/`.

### SKILL.md section order (review / process skills)

1. Purpose
2. Process
3. Finding File Format (if the skill writes findings)
4. Finding ID Prefixes
5. Severity Scale
6. Scan Checklist
7. Concurrency
8. References

## Development Workflow

```bash
git clone https://github.com/rsvalerio/ai.git
cd ai
mise install         # or: make install-tools (Homebrew)
make check-tools     # confirm they match .tool-versions
make lint-and-validate
```

| Command | Description |
|---------|-------------|
| `make validate` | Validate all skills (`skill-validator`) |
| `make lint` | Format and lint all skills (`rumdl`) |
| `make lint-and-validate` | Both gates |
| `make ci` | Non-mutating CI gate (`validate` + fmt/lint check) |
| `make check-tools` | Fail if local tooling drifted from `.tool-versions` |
| `make install-tools` | Install both tools via Homebrew |
| `make link` | Symlink skills into `~/.claude/skills/` |
| `make unlink` | Remove those symlinks |

`.tool-versions` pins the tool versions, and CI reads that same file — a green `make ci` only means something when `make check-tools` passes too.

Edit under `skills/<skill-name>/`, then run `make ci` before opening a PR. Follow the [Agent Skills specification](https://agentskills.io/specification). Contribution and pull request rules: [CONTRIBUTING.md](CONTRIBUTING.md).

### Validation

```bash
skill-validator validate structure --strict ./skills/code-review-rust
```

Checks YAML frontmatter, required `name`/`description`, lowercase-hyphen naming, directory structure, and that `name` matches the parent directory.

### Markdown linting

Config lives in [`.rumdl.toml`](.rumdl.toml). Prefer Make targets above; for a single path:

```bash
rumdl check skills/code-review-rust/
rumdl fmt skills/code-review-rust/
```

## Adding a New Skill

1. Create `skills/<skill-name>/` with `SKILL.md` (`name`, `description`, `license`).
2. Optionally add `assets/openai.yaml` and `references/*.md`.
3. Add a plugin entry to `.claude-plugin/marketplace.json` and the skill to the [README overview](README.md#overview).
4. Run `make validate` and `make validate-marketplace`.

## Publishing

Prerequisites: `make lint-and-validate` passes.

**Local (Claude Code):** `make link` / `make unlink`.

**Claude Code marketplace:** the repo root is a plugin marketplace (`.claude-plugin/marketplace.json`), one plugin per skill. No `version` fields — installs track the commit SHA, so pushing to `main` *is* the release. Users install with:

```bash
claude plugin marketplace add rsvalerio/ai
claude plugin install code-review-rust@dev-skills
```

Validate the manifest with `make validate-marketplace` before pushing.

**GitHub catalog:** this repo *is* the catalog. Users install with:

```bash
agent-skills install https://github.com/rsvalerio/ai/tree/main/skills/code-review-rust
```

Publish by pushing to `main` (and optionally tagging `vX.Y.Z` for versioned installs). To submit upstream, fork [openai/skills](https://github.com/openai/skills) and follow that repo's guidelines. For discovery, keep the README clear and use topics such as `rust`, `agent-skills`, `claude`, `codex`.
