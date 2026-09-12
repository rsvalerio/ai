---
name: code-review-rust
description: Reviews Rust code for idioms and ownership, error handling, concurrency and async soundness, performance and unsafe code, OWASP security, test quality, and NATS/JetStream patterns. Use while writing or editing Rust as an implementation guardrail, or run a formal review that files one backlog task per finding.
allowed-tools: Read Grep Glob Bash(wc *) Bash(ls *) Bash(tree *) Bash(git rev-parse:*) Bash(git log:*) Bash(ops backlog:*)
license: Apache-2.0
---

# Rust Code Review

Review Rust code against all rule categories: idioms, ownership, error handling, traits, concurrency, async, performance, unsafe, security (OWASP), complexity, readability, architecture, API design, duplication, test quality, and NATS/JetStream patterns.

## Applicability

- Use this skill for formal Rust code reviews.
- Also use this skill as an implementation guardrail when making non-trivial Rust code changes: read the relevant rules, keep the change within those constraints, and avoid introducing new violations.
- In implementation guardrail mode, do not create backlog tasks unless the user explicitly asked for a formal review. Treat the rules as acceptance criteria for the code change and run the project's relevant Rust QA gates before finishing.

## Purpose

- Create one backlog task per finding via `ops backlog task create --plain` command
- Scan all `.rs` files, `Cargo.toml`, `Cargo.lock`, `tests/`, and configuration files
- Cover every rule category: work from [scan-checklist.md](references/scan-checklist.md) straight to the rule files it names — full rule text for every live candidate, and for every category in its **Sweep** list whether or not a candidate surfaced
- Apply the priority order and severity scale defined in [rules.md](references/rules.md#design-philosophy)

## Loading rules (token discipline)

Rules are stored in three tiers. Read them in this order and stop as soon as you have what
you need — loading every rule file into context is a failed run's worth of tokens spent
before the first grep.

| Tier | File | When to read |
|------|------|--------------|
| 1 | [scan-checklist.md](references/scan-checklist.md) | Start of every scan. Observable signal → rule IDs, plus a **Sweep** list of categories that have no signal and must be read once regardless. |
| 2 | [rules/index.md](references/rules/index.md) | **Not part of a scan.** One line per rule, for looking up a rule you have an ID for but no signal — e.g. resolving an ID carried by a backlog task. A scan skips it: tier 1 already named the IDs, and tier 3 is what decides the finding. |
| 3 | `references/rules/<CATEGORY>.md` | The scan's second and last read. Only for a category with live candidates. Full rationale, examples, exceptions, and scanning guidance. **Required reading before filing a finding against a rule** — never file from a tier-2 one-liner. |

[rules.md](references/rules.md) holds the category table, severity scale, and design philosophy;
it is small and safe to read at any point.

A scan therefore reads tier 1, then tier 3 for the categories that hit — never the whole
index. Tier 1 emits rule IDs directly, so the index adds a 10,700-token hop that tier 3
settles authoritatively anyway.

In implementation-guardrail mode, skip tier 1 as well: read the tier-3 file for the one or
two categories your change touches (e.g. `rules/ASYNC.md`) and nothing else.

## Execution Contract (MUST follow)

You are running unattended — nobody is watching to course-correct. Follow these rules strictly:

1. **Findings are emitted ONLY via `ops backlog task create --plain`.** Do NOT print findings as prose, markdown, or a summary report in lieu of creating tasks. A text-only report is a failed run. If you identify a finding, the next action is a `ops backlog task create --plain` call — not text output.
2. **Never ask for confirmation.** Do not ask "Would you like me to create these tasks?" or pause for approval. You are pre-authorized. Findings → `ops backlog task create --plain` immediately, no intermediate prompt. Questions to the user = failed run.
3. **If you delegate to subagents, you MUST wait for every one to return before finishing.** Never end the turn with subagents still in flight. Collect each subagent's findings and create the backlog tasks yourself — subagents reports as, the parent writes.
4. **The only terminal action is the summary table** (step 5 below), printed *after* all `ops backlog task create --plain` calls have succeeded. If you have not created tasks, you are not done.
5. **On tool failure, retry or report the specific error.** Do not silently degrade to a text report.

## Process

1. **Survey** — List all `.rs` files and `Cargo.toml`; identify large files (>300 lines), map module structure and dependencies, enumerate test files and `#[cfg(test)]` modules
2. **Scan** — Walk [scan-checklist.md](references/scan-checklist.md) signal by signal. For every signal that hits, open `references/rules/<CATEGORY>.md` for the rule IDs it named and confirm against the full rule text. Do not read `rules/index.md` — tier 1 already gave you the IDs. A category the table named whose signals did not hit, and whose code is not present, needs no rule file read. Then work the checklist's **Sweep** list: those categories have no signal at all, so nothing above opens them and that skip cannot apply to them — read each one regardless, or their rules drop out of the review silently. For each violation, prepare a finding with rule ID, severity, file location, description, and acceptance criteria
3. **Deduplicate** — Run `ops backlog search "<RULE-ID>" --plain` to check for existing tasks with the same finding ID. If one exists and is not marked Done, skip. If Done, create only if the issue has regressed. Group findings that target the same `(file, function)` at different granularity into a single finding with the broadest scope
4. **Create tasks** — For each finding, run `ops backlog task create --plain` with the flags below. Use a `"$(cat <<'EOF' ... EOF)"` heredoc for multi-line values (do NOT use `$'...'` ANSI-C quoting — it triggers an `ansi_c_string` safety prompt on every call).
5. **Summarize** — run `ops backlog task list --status 'Triage' --plain`

### Calibration rules (always apply before filing)

Counts from a raw grep are signal, not findings. Before turning a grep count into a finding:

- **Always scope out test code** for production-quality rules (ERR-5 / ERR-8 `unwrap`, READ-8 `eprintln!`, CONC-5 `thread::sleep`, PERF/OWN clone rules, etc.). Exclude anything inside a `#[cfg(test)]` module, a file under `tests/`, a `test-support`/similar feature-gated region, or a `#[test]`-attributed fn. A finding that disappears when test code is excluded is not a finding — do not file it.
- **Prefer a file:line candidate list over a raw count.** Put the list in the task description and let the reviewer verify. Never report aggregate counts like "371 unwraps" without the per-file breakdown behind them — those numbers routinely run 100× inflated by test code and helper patterns.
- **Rules with known false-positive patterns (TEST-1, ERR-5, TEST-11)** have a `**Scanning guidance:**` block in their detailed rule references. Read that guidance before filing — if every candidate falls under one of the accepted idioms (helper-fn assertion, `#[should_panic]`, `Result<...>` test, provably infallible `unwrap`), do not file.
- **When the scanner can't be made precise, label the finding.** If you file anyway, mark the description with `<!-- scan confidence: candidates to inspect -->` and list every candidate by `file:line`. Reviewers treat that marker as "manual triage required" rather than "N issues present".

## Creating a Task

For each finding, run:

```bash
ops backlog task create "<RULE-ID>: <Title>" \
  -d "$(cat <<'EOF'
**File**: `<path>:<line>`

**What**: <what is wrong>

**Why it matters**: <impact>
EOF
)" \
  -s "Triage" \
  -l "code-review-rust,<category>" \
  --priority <critical|high|medium|low> \
  --modified-file "<path>" \
  --ac "<acceptance criterion 1>" \
  --ac "<acceptance criterion 2>" \
  --plain
```

Map severity to `--priority`: critical→critical, high→high, medium→medium, low→low.

**`--modified-file` is required.** Pass one flag per file the finding touches,
repo-root-relative and **without** the `:<line>` suffix (`crates/foo/src/lib.rs`, not
`crates/foo/src/lib.rs:42`). This is the machine-readable twin of the `**File**:` line in
the description: `code-review-triage` reads it to compute each wave's file scope and merge
order, and `ops backlog search --modified-file <path>` finds every finding touching a path. A
finding filed without it is invisible to both.

## Rule Categories and Severity Scale

See [rules.md](references/rules.md#finding-ids-and-categories) for the canonical rule-category table and severity scale. Severity: Critical > High > Medium > Low, mirroring the priority order Safety > correctness > maintainability > style.

## Scan Checklist

The signal → rules table lives in [scan-checklist.md](references/scan-checklist.md). Read it at the
start of a scan; it is the cheapest way to decide which rule categories are even in play.

## Concurrency

This skill is read-only on the codebase and creates tasks only via the `ops backlog` CLI. Multiple instances can run in parallel — each finding gets its own task, so there are no write conflicts.

Finish all reviews before running `code-review-triage`, so the resulting waves capture every finding. Reviews are also safe to run while waves are executing — they only add new `Triage` tasks and never touch wave state — but findings filed mid-wave land in the *next* triage pass, not the current one.

## References

- [Rules index](references/rules.md) — Category table, severity scale, design philosophy
- [Scan checklist](references/scan-checklist.md) — Observable signal → rules to check (tier 1)
- [Rule index](references/rules/index.md) — One line per rule, grouped by category (tier 2)
- Full rules, one file per category (tier 3) — read on demand:
  - [`rules/OWN.md`](references/rules/OWN.md) — Ownership & borrowing (4 KB)
  - [`rules/ERR.md`](references/rules/ERR.md) — Error handling (12 KB)
  - [`rules/TRAIT.md`](references/rules/TRAIT.md) — Traits & generics (8 KB)
  - [`rules/CONC.md`](references/rules/CONC.md) — Concurrency (24 KB)
  - [`rules/ASYNC.md`](references/rules/ASYNC.md) — Async (18 KB)
  - [`rules/PERF.md`](references/rules/PERF.md) — Performance (16 KB)
  - [`rules/UNSAFE.md`](references/rules/UNSAFE.md) — Unsafe (7 KB)
  - [`rules/PATTERN.md`](references/rules/PATTERN.md) — Advanced patterns (7 KB)
  - [`rules/MACRO.md`](references/rules/MACRO.md) — Macro design (4 KB)
  - [`rules/TIME.md`](references/rules/TIME.md) — Date & time (9 KB)
  - [`rules/EDITION.md`](references/rules/EDITION.md) — Rust 2024 edition reference (1 KB)
  - [`rules/VER.md`](references/rules/VER.md) — Version-specific features (2 KB)
  - [`rules/FN.md`](references/rules/FN.md) — Functions & structure (3 KB)
  - [`rules/READ.md`](references/rules/READ.md) — Readability (7 KB)
  - [`rules/ARCH.md`](references/rules/ARCH.md) — Architecture & modules (15 KB)
  - [`rules/API.md`](references/rules/API.md) — API design (25 KB)
  - [`rules/CL.md`](references/rules/CL.md) — Cognitive load (4 KB)
  - [`rules/DUP.md`](references/rules/DUP.md) — Duplication (2 KB)
  - [`rules/SEC.md`](references/rules/SEC.md) — Security (OWASP) (29 KB)
  - [`rules/TEST.md`](references/rules/TEST.md) — Test quality (15 KB)
  - [`rules/NATS.md`](references/rules/NATS.md) — NATS / JetStream (4 KB)
- [Classification notes](references/rules-classification.md) — justified violations and SEC/UNSAFE classification guidance
- [OWASP Top 10:2021](references/owasp-2021.md) — A01--A10 mapping for security findings
- [Anti-patterns](references/anti-patterns.md) — Common cross-cutting anti-patterns
- [NATS security](references/nats-security.md) — NATS-specific SEC rule mapping
- [Flakiness patterns](references/flakiness-patterns.md) — Root causes and mitigations for flaky tests
- [Classification guide](references/classification-guide.md) — Test issue classification indicators
- [OpenAI agent metadata](assets/openai.yaml) — Optional agent configuration for compatible runtimes
