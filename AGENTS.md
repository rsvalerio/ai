# Instructions for AI Agents

This file tells AI assistants how to work with the skills repository: conventions, development workflow, validation, and publishing.

## Project Overview

skills is a collection of [Agent Skills](https://agentskills.io/specification) for Rust development. Skills live under `skills/`; each skill is a directory with `SKILL.md`, optional `references/*.md`, and optional `agents/openai.yaml`. When editing or adding skills, follow the conventions and workflow below.

## Repository Structure

```text
skills/
├── README.md          # For skill users (install, use, overview)
├── AGENTS.md          # This file: instructions for AI agents
├── Makefile           # validate, lint, publish/unpublish, etc.
├── skills/            # One directory per skill
│   ├── code-review-rust/      # Rust review engine (idioms, security, quality, tests, NATS)
│   ├── code-review-triage/    # Groups triaged findings into review waves
│   ├── code-review-run-wave/  # Executes one review wave in a worktree and closes it
│   ├── code-review-run-waves/ # Runs all open waves concurrently, merges serially
│   ├── commit-script/         # Generates grouped conventional commit scripts
│   ├── rust-meta/             # Knowledge integration from external sources
│   └── ...
└── LICENSE
```

## Skill Conventions

### Directory layout

Each skill directory must contain:

- **SKILL.md** -- Required. YAML frontmatter (`name`, `description`) and Markdown instructions.
- **references/** -- Optional. Detailed reference files loaded on demand.
- **agents/openai.yaml** -- Optional. UI metadata (`display_name`, `short_description`, `default_prompt`) for products that support it.

Example:

```text
skill-name/
├── SKILL.md
├── agents/
│   └── openai.yaml
└── references/
    ├── reference1.md
    └── reference2.md
```

Use **Title Case for H1** in `references/*.md` (e.g. `# Integration Workflow`, `# Audit Checklist`).

### SKILL.md section order

For review/process skills, use this section order for consistency:

1. **Purpose** -- Why use this skill
2. **Process** -- Steps to run the skill
3. **Finding File Format** -- Template for output files (for skills that write findings)
4. **Finding ID Prefixes** -- Rule ID prefix table
5. **Severity Scale** -- Severity level definitions
6. **Scan Checklist** -- Signals to search for and corresponding rules
7. **Concurrency** -- Notes on parallel execution
8. **References** -- Links to `references/*.md`

### Skill relationships

- **code-review-rust** is the main review skill. It contains all rule categories (OWN, ERR, TRAIT, CONC, ASYNC, PERF, UNSAFE, SEC, FN, READ, ARCH, API, CL, DUP, TEST, NATS) in a single `references/rules.md`.
- **code-review-triage** groups backlog findings in `Triage` status into semantic wave parent tasks (`code-review-plan-waveN`), and stamps each wave with its file scope via `--modified-file` so merges can be ordered.
- **code-review-run-wave** claims one open wave, applies each member fix in an isolated git worktree, runs QA gates, merges it back under a shared lock, and marks the wave done. The mechanics live in `skills/code-review-run-wave/references/worktree-protocol.md`.
- **code-review-run-waves** fans out across every open wave, one worktree each, and lands them one at a time. It delegates per-wave execution to code-review-run-wave rather than reimplementing it.
- **commit-script** reviews git state and produces a shell script that batches related files into conventional commits.
- **rust-meta** maps new knowledge to the appropriate section within code-review-rust.

### Finding output

code-review-rust writes one markdown file per finding to `.backlog/tasks/`. Each file is named `<PREFIX>-<N>-<slug>.md` with YAML frontmatter (id, severity, category, labels, status) and a body describing the issue. Multiple skill instances can run in parallel -- each finding gets its own file. Every finding must also record one `--modified-file` per file it touches (repo-root-relative, no line numbers); `code-review-triage` reads that field to compute wave file scope and merge order.

## Development Workflow

### Setup

```bash
git clone https://github.com/rsvalerio/skills.git
cd skills
make install-tools
make lint-and-validate
```

This installs **skill-validator** (validates Agent Skills format) and **rumdl** (markdown linter) via Homebrew.

### Making changes

1. Edit files under `skills/<skill-name>/`.
2. Validate all skills: `make validate`.
3. Lint all skills: `make lint`.
4. Run both gates: `make lint-and-validate`.
5. Test the skill in your AI tool (Claude Code, Codex, etc.).

### Key commands

| Command | Description |
|---------|-------------|
| `make validate` | Validate all skills |
| `make lint` | Format and lint all skills |
| `make lint-and-validate` | Run lint and validation together |
| `make publish` | Link skills into `~/.claude/skills/` |
| `make unpublish` | Remove linked skills from `~/.claude/skills/` |

## Validation (skill-validator)

The validator checks that skills conform to the Agent Skills specification:

```bash
skill-validator validate structure --strict ./skills/code-review-rust
```

It checks:

- Valid YAML frontmatter
- Required fields: `name`, `description`
- Naming: lowercase, hyphens
- Directory structure
- **name matches parent directory name** (e.g. a skill in `./my-skill/SKILL.md` must have `name: my-skill`)

## Markdown Linting (rumdl)

This project uses **rumdl**, a high-performance Markdown linter and formatter written in Rust (57+ lint rules, auto-fix support).

### Benefits

- Built for speed; zero runtime dependencies; single binary
- Auto-fix: `rumdl fmt` or `rumdl check --fix`
- TOML configuration; CI/CD friendly (non-zero exit on errors)

### Usage

```bash
rumdl check README.md
rumdl check .
rumdl check --fix .
rumdl fmt .
rumdl check skills/code-review-rust/
```

### Configuration

Create `.rumdl.toml` in the project root for custom configuration:

```toml
line-length = 100
exclude = ["target", ".git"]
disable = ["MD013", "MD033"]

[MD007]
indent = 2

[MD013]
line-length = 100
code-blocks = false
tables = false

[MD048]
code-fence-style = "backtick"
```

Run `rumdl init` to create a default config. List rules: `rumdl rule`; details: `rumdl rule MD013`.

### Rule categories

rumdl covers headings (MD001--MD003), lists (MD004, MD005, MD007), whitespace (MD009, MD010, MD012), code (MD040, MD046, MD048), links (MD034, MD039, MD042), images (MD045, MD052), style (MD031, MD032, MD035).

## Contributing Guidelines

1. **Follow the Agent Skills specification** -- <https://agentskills.io/specification>
2. **Run checks before submitting** -- `make lint-and-validate`
3. **Update CHANGELOG.md** -- Document notable changes under `[Unreleased]` using existing categories.
4. **Keep SKILL.md concise** -- Prefer under 500 lines; put detailed content in `references/` markdown files.
5. **Match directory and skill name** -- The `name` in YAML frontmatter must match the directory name (e.g. `code-review-rust`).

### Workflow

1. Fork the repository and create a branch.
2. Make changes in `skills/<skill-name>/`.
3. Run `make validate` and `make lint`.
4. Run `make lint-and-validate` before opening a pull request.
5. Open a pull request with a clear description.

## Adding a New Skill

1. Create a directory under `skills/<skill-name>/`.
2. Add `SKILL.md` with valid YAML frontmatter (`name`, `description`, `license`).
3. Optionally add `agents/openai.yaml` and `references/*.md`.
4. Run `make validate`.
5. Update the root `README.md` overview table and any relevant docs.

## Publishing Workflow

### Prerequisites

- `make lint-and-validate` passes.

### Publishing locally (Claude Code)

To link all skills into `~/.claude/skills/`:

```bash
make publish
```

To remove linked skills:

```bash
make unpublish
```

### Publishing to GitHub

This repository is the published catalog. Users install via:

```bash
agent-skills install https://github.com/rsvalerio/skills/tree/main/skills/code-review-rust
```

To publish changes:

```bash
make lint-and-validate
git add skills/
git commit -m "feat: description"
git tag v1.1.0   # optional
git push origin v1.1.0
git push origin main
```

For a new repo: `git remote add origin https://github.com/rsvalerio/skills.git`, then push.

### Tagging releases

```bash
git tag v1.0.0
git push origin v1.0.0
```

Users can install from a version: `agent-skills install .../tree/v1.0.0/skills/code-review-rust`.

### Submitting to openai/skills

To be included in the official catalog:

1. Fork <https://github.com/openai/skills>
2. Add each skill (or subset) to `skills/.curated/` or `skills/.experimental/`
3. Follow that repository's contribution guidelines
4. Submit a pull request

Note: Review process and criteria are not publicly documented.

### Discovery

- **SkillsMP** (skillsmp.com) indexes public GitHub repositories; ensure a clear README and topics.
- Add GitHub topics: `rust`, `agent-skills`, `claude`, `codex`.
- Use descriptive skill names and descriptions in `SKILL.md`.
