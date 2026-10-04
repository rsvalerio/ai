# Instructions for AI Agents

How to work in this repository: skill conventions, development workflow, validation, and publishing. For install and usage as a skill *consumer*, see [README.md](README.md). For wiring `code-review-rust` as an implementation guardrail in a consumer repo, see [docs/implementation-guardrail.md](docs/implementation-guardrail.md).

## Project Overview

This repo is a monorepo of AI tooling, published as a Claude Code plugin marketplace. The root holds only the marketplace manifest; each plugin lives under `plugins/<name>/` with its own manifest, `skills/` and optional `evals/`. Each skill is a directory with `SKILL.md`, optional `references/*.md`, and optional `assets/openai.yaml`. A top-level `skills/` (or `agents/`) is allowed for standalone items that belong to no plugin; create it only when needed.

```text
.
├── README.md                 # Users: install, use, overview
├── AGENTS.md                 # This file: contributor / agent instructions
├── docs/
│   └── implementation-guardrail.md  # Consumer activation for guardrail mode
├── Makefile                  # validate, lint, link/unlink, eval — discovers skills by glob
├── scripts/
│   ├── validate-skills.py    # strict skill-validator run + documented allowlist
│   └── validate-rules.py     # rule-index parity for the review skills
├── .claude-plugin/
│   └── marketplace.json      # The only root manifest; lists every plugin
├── plugins/
│   ├── dev/                  # Rust and frontend development
│   │   ├── .claude-plugin/plugin.json
│   │   ├── evals/            # `claude plugin eval` cases (see Behavioural evals)
│   │   └── skills/
│   │       ├── code-review-rust/
│   │       ├── code-review-web/
│   │       ├── code-review-lovable/
│   │       ├── code-review-triage/
│   │       ├── code-review-run-wave/
│   │       ├── code-review-run-waves/
│   │       ├── commit-script/
│   │       ├── rust-make-build-fast/
│   │       ├── rust-make-clippy-pedantic/
│   │       └── rust-meta/
│   └── product/              # Product and market research
│       ├── .claude-plugin/plugin.json
│       ├── evals/
│       └── skills/
│           └── product-research/
└── LICENSE
```

Paths inside a skill that name another skill (`skills/code-review-run-wave/references/worktree-protocol.md`) are relative to the **plugin root**, which is what an installed plugin contains. They stay correct wherever the plugin lives in this repo.

Skill purposes are listed in the [README overview](README.md#overview). Relationships that matter when editing the `dev` skills:

- **code-review-rust** / **code-review-web** — formal review, implementation-guardrail and ad-hoc review engines. Only a formal review files backlog tasks; the other two answer in chat, and the Execution Contract is scoped to formal review so a pasted snippet never lands in a mode that forbids a chat answer. Rules live in three tiers: `references/scan-checklist.md` (signal → rule IDs), `references/rules/index.md` (one line per rule), and `references/rules/<CATEGORY>.md` (full text). A **scan** reads tier 1 then tier 3 — tier 2 is not a scan step, because tier 1 already emits rule IDs and tier 3 is what decides a finding. Tier 2 is for resolving an ID you hold without a signal (a backlog task, a `rust-meta` lookup); guardrail mode reads tier 3 alone. Keeping tier 2 out of the scan path is worth ~10,700 tokens a review, and the same again per wave runner. `references/rules.md` holds the category table and severity scale. Adding or changing a rule means updating its category file **and** `rules/index.md`; if the rule's observable signal changes, update `scan-checklist.md` too — and a brand-new category needs either a signal row there or a `## Sweep` entry, or it is unreachable. `rules/index.md` is maintained by hand — its one-liners carry deliberate wording and are not regenerated from the category files.
- **code-review-lovable** — stack overlay on `code-review-web` for Lovable-style apps (Vite + React + shadcn/ui + Tailwind on Supabase or Lovable Cloud, TanStack Query, Zustand, react-hook-form + zod, and Shopify Storefront commerce when the app uses Lovable's Shopify integration). Same three-tier rule layout, same three modes (formal, guardrail, ad-hoc) and filing contract, its own prefixes (`RLS`, `SUPA`, `AUTH`, `EDGE`, `QRY`, `FORM`, `UI`, `SHOP`, `LOV`) that must never overlap `code-review-web`'s. A rule belongs here only when the stack is what makes the code wrong; generic React/TS rules go to `code-review-web`, and a formal review of such an app runs both. SQL rules are judged on the final state of the replayed migrations.
- **code-review-triage** — groups `Triage` backlog findings into `code-review-plan-waveN` parents and stamps file scope via `--modified-file` for merge ordering. A wave is a task labelled `code-review-wave` whose members carry `parent_task_id`; the runners enumerate them with `ops backlog wave list` / `wave members`.
- **code-review-run-wave** — claims one open wave (`ops backlog wave claim`), applies fixes in an isolated git worktree, runs QA, merges under `ops lock code-review-merge` (one command covering rebase → integration verify → fast-forward, with conflicts fixed outside the lock), commits bookkeeping with `ops backlog commit`, parks with `ops backlog wave park`. Protocol: `skills/code-review-run-wave/references/worktree-protocol.md`.
- **code-review-run-waves** — fans out across open waves; delegates per-wave work to `code-review-run-wave`.
- **commit-script** — groups related files into conventional commit scripts. Two modes: `commit` (default, local commits only — what the wave runners use) and `pr` (topic branch + push + `gh pr create`).
- **rust-make-clippy-pedantic** — mechanical counterpart to `code-review-rust`: runs `ops clippy-findings` (Clippy under `--locked`, one normalized JSON row per diagnostic) with the lint policy of ops's Rust foundation (rendered by `ops init --rust` into scratch) passed as flags (never as source edits) over a verified-clean tree, files one `Triage` task per warning labelled `pedantic` — dropping test-only style findings, generated files and out-of-tree warnings, and collapsing any lint that fires more than 20 times in one crate into a single aggregate task — reports an effort estimate, and prints the `Cargo.toml` / `clippy.toml` lint policy that would make the strictness permanent, writing it only under `--apply`. The policy is never restated in the skill: it is ops's foundation, and `ops init --rust --check` decides what an existing file lacks. Feeds `code-review-triage` like the review skills do.
- **rust-make-build-fast** — `rust-make-clippy-pedantic`'s shape applied to build cost: over a verified-clean tree it reads the profiles, cargo config, gates, nextest config and dependency graph, and takes sccache stats around a warm `cargo build --timings`. It files one `Triage` task per finding, labelled `build-fast`, carrying a measured cost with its date and machine load, classified `safe` or `trade-off`. Cold builds run only under `--measure-cold`, into a target directory on real disk (never tmpfs), with variants passed as `--config` overrides rather than file edits. `--apply` writes only safe findings that have a template (`Cargo.toml` test profile, `.ops.toml` gates, `.config/nextest.toml`). Trade-offs such as dependency `opt-level` are never applied. Machine facts (tmpfs `/tmp`, a user-level `jobs` cap) are report-only. The checks catalog is drawn from hand-tuning dbsec, ops and event0; a check should enter it only after it has cost a real workspace time.
- **rust-meta** — maps external Rust knowledge into `code-review-rust`.

Relationships that matter when editing the `product` skills:

- **product-research** — carries no project conventions. Output paths, coverage dimensions and markers, scope, tiers, jurisdiction policy and vocabulary all come from the consuming repo's profile (`.product-research.md`, or a `## Product research` section in its `CLAUDE.md` / `AGENTS.md`); with none, the skill stops and offers to scaffold one from `assets/profile.md`. Never add a consuming project's thesis, paths or product list to the skill, not even as an example. Each rubric is defined in exactly one file: the evidence levels and source record in `references/evidence-contract.md`, license classes in `license-taxonomy.md`, business-model patterns and self-hostability grades in `business-model.md`, jurisdiction classes in `jurisdiction.md`, and the profile schema in `project-profile.md`. `SKILL.md` and `assets/` link to them rather than restate them. Record templates live in `assets/`, not `templates/`, because strict `skill-validator` warns on unknown top-level directories. The skill does not use `ops`.

### ops dependency

Every skill that touches the backlog, and several that do not, run through
[`ops`](https://github.com/rsvalerio/ops), and the floor is **ops 0.74.0**. Each such skill
checks `ops --version` first and stops if it is older; the README's Requirements section
states the same floor. Raise it in all three places — the skill preflights, the README, and
here — when a skill starts using a newer ops feature. Running this repo's own gates
(`ops verify`, `ops qa`) needs ops 0.75.0 or newer for the `lint-actions` built-in. That is
a contributor requirement, pinned on ci.yml's `setup-ops` steps, not a skill floor. What
each skill relies on:

| ops feature | Used by |
|-------------|---------|
| `ops backlog task create --unless-exists` (idempotent filing) | code-review-rust, code-review-web, code-review-lovable, rust-make-clippy-pedantic, rust-make-build-fast |
| `ops backlog wave create` / `wave overlap` | code-review-triage, code-review-run-waves |
| `ops backlog wave claim` / `wave park`, `ops backlog commit`, `ops lock` | code-review-run-wave, code-review-run-waves |
| `ops clippy-findings --schema-version 2` (camelCase report) | rust-make-clippy-pedantic |
| `ops explain`, `ops about machine` (incl. `cargo.incremental` / `incrementalProfiles`), `ops about dependencies --duplicates [--target]` (host-filtered by default) | rust-make-build-fast |
| `ops init --rust` (rendered into scratch, never the repo) and `ops init --rust --check` (drift) — the Rust foundation | rust-make-clippy-pedantic, rust-make-build-fast |
| `ops about crates` / `ops about loc` | code-review-rust, rust-make-clippy-pedantic, rust-make-build-fast |
| `ops typecheck` / `ops lint` (vite/node stack) | code-review-web, code-review-lovable |

### Finding output

`code-review-rust`, `code-review-web` and `code-review-lovable` file one task per finding through `ops backlog task create --unless-exists <identity key>` — one markdown file under `.backlog/tasks/` as `task-<N> - <slug>.md` (YAML frontmatter + body); the task id prefixes the title. Task files are written only through the CLI: field types and marker layout are load-bearing for the triage and wave skills. Parallel skill runs are fine — one file per finding. Every finding must record one `--modified-file` per touched path (repo-root-relative, no line numbers) so triage can compute wave scope and merge order.

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
ops verify           # fast offline gate
ops qa               # full gate: verify + marketplace + install path
```

| Command | Description |
|---------|-------------|
| `make validate` | Validate all skills, strict (`scripts/validate-skills.py`) |
| `make lint` | Format and lint all skills (`rumdl`) |
| `make lint-and-validate` | Both gates |
| `ops verify` | Fast offline gate (skills, rules index, action pins, markdown, tool versions); wave runners and CI run it. Steps in `.ops.toml` |
| `ops qa` | Full gate: `verify` plus `validate-marketplace` and `check-install`; CI runs it |
| `make ci` | The `ops qa` checks without ops: no `check-tools`, no `lint-actions` |
| `make check-install` | `make link` / `make unlink` round-trip every skill through a scratch directory |
| `ops lint-actions` | ops built-in, part of `ops verify`: every action SHA-pinned with a version comment, no `secrets: inherit` |
| `make validate-rules` | Fail if `rules/index.md` and `references/rules/*.md` disagree |
| `make eval` | Run the behavioural eval suite (`claude plugin eval`, not in `make ci`) |
| `make check-tools` | Fail if local tooling drifted from `.tool-versions` |
| `make install-tools` | Install both tools via Homebrew |
| `make link` | Symlink skills into `~/.claude/skills/` |
| `make unlink` | Remove those symlinks |

`.tool-versions` pins the tool versions, and CI reads that same file — a green `make ci` only means something when `make check-tools` passes too.

Edit under `plugins/<plugin>/skills/<skill-name>/`, then run `ops qa` before opening a PR. Follow the [Agent Skills specification](https://agentskills.io/specification). Contribution and pull request rules: [CONTRIBUTING.md](CONTRIBUTING.md).

### Validation

```bash
skill-validator validate structure --strict ./plugins/dev/skills/code-review-rust
```

Checks YAML frontmatter, required `name`/`description`, lowercase-hyphen naming, directory structure, and that `name` matches the parent directory.

`make validate` runs this over every skill (`plugins/*/skills/*/` and `skills/*/`) through [`scripts/validate-skills.py`](scripts/validate-skills.py), which propagates per-skill failures — a plain shell loop kept only the last skill's exit code, so the gate silently passed while four skills were failing — and carries one allowlist entry:

**`deep nesting detected: references/rules/` (all three review skills) is allowed, and cannot be fixed.** Flattening the corpus to `references/rules-<CAT>.md` makes those 21 files counted top-level references and trips a hard error from the same validator (`total reference files: 74055 tokens`), which fails even without `--strict`. The nesting is what keeps ~50k tokens of rule text out of the counted budget; the warning and the error cannot both be satisfied without deleting rules. An allowlist entry that stops firing fails the build, so it cannot rot into a licence to regress.

`references/rules/index.md` lives inside `rules/` for the same reason — as a counted top-level reference it exceeded the validator's 10,000-token-per-file limit. Note what that does and does not achieve: it satisfies the checker, it does not reduce what an agent loads. Splitting the index was the alternative and would have cost the "one place to find any rule" property.

### Rule-index drift

`make validate-rules` compares every `**<CAT>-<N>**` id in
`references/rules/*.md` against `references/rules/index.md`, for
`code-review-rust`, `code-review-web` and `code-review-lovable`. A rule that lands in a category file
without an index line is invisible to a scan — the skill silently stops
enforcing it — and a ghost index line points at a rule that no longer exists.
Part of `make ci`.

### Behavioural evals

Each plugin can carry an `evals/` directory; `make eval` runs `claude plugin eval
plugins/<name>` for every plugin that has one. The cases answer "does the skill still
fire", not "is the markdown well-formed".

| Case | Asserts |
|------|---------|
| `review-rust` | A pasted-snippet Rust review loads `code-review-rust`, reads a `references/rules/` category file and cites a rule ID in the chat answer |
| `review-web` | A pasted React/TS review loads `code-review-web`, not the Rust skill, and cites a web rule ID |
| `review-lovable` | A pasted Supabase migration + supabase-js review loads `code-review-lovable`, reads an `RLS`/`SUPA`/`QRY` rule file and cites a lovable rule ID |
| `guardrail-rust` | The verification prompt from [docs/implementation-guardrail.md](docs/implementation-guardrail.md) loads the skill and names a rule id |
| `research-no-profile` (product) | A "research product X" request loads `product-research` and, with no profile in the sandbox, stops and asks for `.product-research.md`: no web search or fetch, no write or edit attempt |

Every grader is free (`tool_used` / `regex`), so a run costs agent turns but no
judge calls. By default each case also runs a no-plugin arm and reports the
delta — a case that scores the same in both arms is not being carried by the
skill.

`Write`, `Edit`, `WebSearch` and `WebFetch` are gated: without `--allow-tools` they
are withheld from both arms, so a "must not write" or "must not research" grader
passes vacuously. `make eval` grants them; pass the same flag when running one case
by hand, or the product case's baseline scores 0.80 instead of 0.20.

```bash
make eval                                              # whole suite
claude plugin eval plugins/dev --trust-plugin --case review-web  # one case
claude plugin eval plugins/product --trust-plugin \
  --allow-tools Write Edit WebSearch WebFetch     # product suite, graders armed
```

Deliberately **not** in `make ci`: it is non-deterministic and needs
credentials. Run it before a release and after a Claude Code or model bump.
Results land in `plugins/<name>/evals/results/` (gitignored).

Scope limit worth keeping in mind: these cover description-driven auto-load,
which `docs/implementation-guardrail.md` calls best-effort by design. The
consumer-side `CLAUDE.md` / `AGENTS.md` directive is the actual contract and is
not exercised here.

### Markdown linting

Config lives in [`.rumdl.toml`](.rumdl.toml). Prefer Make targets above; for a single path:

```bash
rumdl check plugins/dev/skills/code-review-rust/
rumdl fmt plugins/dev/skills/code-review-rust/
```

## Adding a New Skill

1. Create `plugins/<plugin>/skills/<skill-name>/` with `SKILL.md` (`name`, `description`, `license`). The plugin picks up every directory under its `skills/` automatically. Skill names must be unique across plugins, because `make link` installs them into one flat `~/.claude/skills/`; `make validate` enforces it.
2. Optionally add `assets/openai.yaml` and `references/*.md`.
3. Add the skill to the [README overview](README.md#overview).
4. Run `make validate` and `make validate-marketplace`.

## Adding a New Plugin

1. Create `plugins/<name>/.claude-plugin/plugin.json` (`name`, `description`, `author`, `homepage`, `license`; no `version`, see Publishing) and `plugins/<name>/skills/`.
2. Add an entry to `.claude-plugin/marketplace.json` with `"source": "./plugins/<name>"`.
3. Optionally add `plugins/<name>/evals/`; `make eval` finds it.
4. Add the plugin to the README overview and its install line.
5. Run `make ci`. Nothing in the Makefile, the validator scripts or CI needs editing: they discover plugins and skills with `plugins/*/` and `plugins/*/skills/*/`.

## Publishing

Prerequisites: `make lint-and-validate` passes.

**Local (Claude Code):** `make link` / `make unlink`.

**Claude Code marketplace:** the repo root is a plugin marketplace (`.claude-plugin/marketplace.json`) listing every plugin under `plugins/`. Inside a plugin the skills reference each other's files, so they are not installable separately. No `version` field in any `plugin.json` — installs track the commit SHA, so pushing to `main` *is* the release. `claude plugin validate` warns about the missing version; that warning is expected and does not fail `make ci`. Each plugin's manifest is also what `claude plugin eval plugins/<name>` resolves to run its no-plugin baseline arm. Users install with:

```bash
claude plugin marketplace add rsvalerio/ai
claude plugin install dev@rsvalerio
claude plugin install product@rsvalerio
```

Validate the manifest with `make validate-marketplace` before pushing (also part of `make lint-and-validate` and `make ci`).

**GitHub catalog:** this repo *is* the catalog. Users install with:

```bash
agent-skills install https://github.com/rsvalerio/ai/tree/main/plugins/dev/skills/code-review-rust
```

Publish by pushing to `main` (and optionally tagging `vX.Y.Z` for versioned installs). To submit upstream, fork [openai/skills](https://github.com/openai/skills) and follow that repo's guidelines. For discovery, keep the README clear and use topics such as `rust`, `agent-skills`, `claude`, `codex`.
