---
name: code-review-rust
description: Reviews Rust code for idioms and ownership, error handling, concurrency and async soundness, performance and unsafe code, OWASP security, test quality, and NATS/JetStream patterns. Use while writing or editing Rust as an implementation guardrail, or run a formal review that files one backlog task per finding.
allowed-tools: Read Grep Glob Bash(wc *) Bash(ls *) Bash(tree *) Bash(git rev-parse:*) Bash(git log:*) Bash(backlog task:*) Bash(backlog search:*)
license: Apache-2.0
---

# Rust Code Review

Review Rust code against all rule categories: idioms, ownership, error handling, traits, concurrency, async, performance, unsafe, security (OWASP), complexity, readability, architecture, API design, duplication, test quality, and NATS/JetStream patterns.

## Applicability

- Use this skill for formal Rust code reviews.
- Also use this skill as an implementation guardrail when making non-trivial Rust code changes: read the relevant rules, keep the change within those constraints, and avoid introducing new violations.
- In implementation guardrail mode, do not create backlog tasks unless the user explicitly asked for a formal review. Treat the rules as acceptance criteria for the code change and run the project's relevant Rust QA gates before finishing.

## Purpose

- Create one backlog task per finding via `backlog task create --plain` command
- Scan all `.rs` files, `Cargo.toml`, `Cargo.lock`, `tests/`, and configuration files
- Check every rule category in [rules.md](references/rules.md)
- Apply the priority order and severity scale defined in [rules.md](references/rules.md#design-philosophy)

## Execution Contract (MUST follow)

You are running unattended — nobody is watching to course-correct. Follow these rules strictly:

1. **Findings are emitted ONLY via `backlog task create --plain`.** Do NOT print findings as prose, markdown, or a summary report in lieu of creating tasks. A text-only report is a failed run. If you identify a finding, the next action is a `backlog task create --plain` call — not text output.
2. **Never ask for confirmation.** Do not ask "Would you like me to create these tasks?" or pause for approval. You are pre-authorized. Findings → `backlog task create --plain` immediately, no intermediate prompt. Questions to the user = failed run.
3. **If you delegate to subagents, you MUST wait for every one to return before finishing.** Never end the turn with subagents still in flight. Collect each subagent's findings and create the backlog tasks yourself — subagents reports as, the parent writes.
4. **The only terminal action is the summary table** (step 5 below), printed *after* all `backlog task create --plain` calls have succeeded. If you have not created tasks, you are not done.
5. **On tool failure, retry or report the specific error.** Do not silently degrade to a text report.

## Process

1. **Survey** — List all `.rs` files and `Cargo.toml`; identify large files (>300 lines), map module structure and dependencies, enumerate test files and `#[cfg(test)]` modules
2. **Scan** — Check all rule categories from [rules.md](references/rules.md) against the codebase. For each violation, prepare a finding with rule ID, severity, file location, description, and acceptance criteria
3. **Deduplicate** — Run `backlog search "<RULE-ID>" --plain` to check for existing tasks with the same finding ID. If one exists and is not marked Done, skip. If Done, create only if the issue has regressed. Group findings that target the same `(file, function)` at different granularity into a single finding with the broadest scope
4. **Create tasks** — For each finding, run `backlog task create --plain` with the flags below. Use a `"$(cat <<'EOF' ... EOF)"` heredoc for multi-line values (do NOT use `$'...'` ANSI-C quoting — it triggers an `ansi_c_string` safety prompt on every call). User authorized this change on 2026-05-02.
5. **Summarize** — run `backlog task list --status 'Triage' --plain`

### Calibration rules (always apply before filing)

Counts from a raw grep are signal, not findings. Before turning a grep count into a finding:

- **Always scope out test code** for production-quality rules (ERR-5 / ERR-8 `unwrap`, READ-8 `eprintln!`, CONC-5 `thread::sleep`, PERF/OWN clone rules, etc.). Exclude anything inside a `#[cfg(test)]` module, a file under `tests/`, a `test-support`/similar feature-gated region, or a `#[test]`-attributed fn. A finding that disappears when test code is excluded is not a finding — do not file it.
- **Prefer a file:line candidate list over a raw count.** Put the list in the task description and let the reviewer verify. Never report aggregate counts like "371 unwraps" without the per-file breakdown behind them — those numbers routinely run 100× inflated by test code and helper patterns.
- **Rules with known false-positive patterns (TEST-1, ERR-5, TEST-11)** have a `**Scanning guidance:**` block in their detailed rule references. Read that guidance before filing — if every candidate falls under one of the accepted idioms (helper-fn assertion, `#[should_panic]`, `Result<...>` test, provably infallible `unwrap`), do not file.
- **When the scanner can't be made precise, label the finding.** If you file anyway, mark the description with `<!-- scan confidence: candidates to inspect -->` and list every candidate by `file:line`. Reviewers treat that marker as "manual triage required" rather than "N issues present".

## Creating a Task

For each finding, run:

```bash
backlog task create "<RULE-ID>: <Title>" \
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
order, and `backlog search --modified-file <path>` finds every finding touching a path. A
finding filed without it is invisible to both.

## Rule Categories and Severity Scale

See [rules.md](references/rules.md#finding-ids-and-categories) for the canonical rule-category table and severity scale. Severity: Critical > High > Medium > Low, mirroring the priority order Safety > correctness > maintainability > style.

## Scan Checklist

Survey for these signals, then check against the corresponding rules:

| Signal | Rules to check |
|--------|----------------|
| `unwrap` / `expect` in non-test code *(exclude `#[cfg(test)]` / `tests/` / `test-support` feature gates before counting — see ERR-5 scanning guidance)* | ERR-5, ERR-8 |
| `.clone()` in hot path or to appease borrow checker | OWN-8, PERF-3 |
| `RefCell<T>` | OWN-10, SEC-24 |
| `Arc<Mutex<T>>` around collections | CONC-1--3, CONC-7--9 |
| `Result<T, String>` or `Box<dyn Error>` in library API | ERR-1, ERR-2, ERR-10 |
| Missing `.with_context()` on `?` propagation | ERR-4 |
| `std::fs` error propagated with no path in the message | ERR-13 |
| `serde_*::from_str` on human-edited config with no field path in the error | ERR-14, SEC-11 |
| Repeated `to_str().unwrap()` / `to_string_lossy()` on the same path values | API-12 |
| `HashMap` used as a cache with no size cap, TTL, or eviction | PERF-16, SEC-33 |
| `Arc<RwLock<T>>` read on every request, replaced wholesale and rarely | CONC-1, CONC-8 |
| CLI binary with no test that runs it as a command (flags, exit codes, stderr) | TEST-31, READ-8 |
| `unsafe` blocks | UNSAFE-1--5, UNSAFE-8, SEC-1--4, SEC-34--36 |
| `lazy_static!` / `once_cell::sync::Lazy` in new code | CONC-10 |
| `async-trait` macro on types that could use native async fn | ASYNC-10 |
| `println!` / `eprintln!` in library or service code | READ-8 |
| Workspace crates with diverging dep versions or per-crate lint config | ARCH-11 |
| Hand-rolled date math (`is_leap_year`, month-length tables, `secs / 86_400`) | TIME-1 |
| `Local::now()` or `NaiveDateTime` persisted, logged, or serialized | TIME-2, TIME-5 |
| `Utc::now()` / `SystemTime::now()` subtracted or `duration_since`d to time an operation | TIME-4 |
| `Utc::now()` / `SystemTime::now()` called inside business logic instead of injected | TIME-6, TEST-16 |
| `std::thread::sleep` in async | CONC-5 |
| Missing `tokio::time::timeout` on I/O | ASYNC-6 |
| Hardcoded secrets, weak crypto | SEC-5--10 |
| String concatenation in SQL/commands | SEC-12, SEC-13 |
| Functions >50 lines, nesting >4, params >5 | FN-1--3 |
| Identical code blocks 5+ lines | DUP-1--4 |
| Tests without assertions *(see TEST-1 scanning guidance — recognize `assert_*` helpers, `#[should_panic]`, and `Result<...>` tests before filing)* | TEST-1, TEST-11 |
| `#[ignore]` without explanation | TEST-24, TEST-26 |
| NATS `connect()` without options | NATS-1--8 |
| JetStream without resource limits | NATS-9--14 |

## Concurrency

This skill is read-only on the codebase and creates tasks only via the `backlog` CLI. Multiple instances can run in parallel — each finding gets its own task, so there are no write conflicts.

Finish all reviews before running `code-review-triage`, so the resulting waves capture every finding. Reviews are also safe to run while waves are executing — they only add new `Triage` tasks and never touch wave state — but findings filed mid-wave land in the *next* triage pass, not the current one.

## References

- [Rules index](references/rules.md) — Category table, severity scale, design philosophy, and links to all detailed rule references
- [Core rules](references/rules-core.md) — OWN, ERR, TRAIT, CONC, ASYNC, PERF, UNSAFE, PATTERN, TIME, EDITION, VER
- [Structure rules](references/rules-structure.md) — FN, READ, ARCH, API, CL
- [Duplication rules](references/rules-duplication.md) — DUP
- [Security rules](references/rules-security.md) — SEC
- [Test rules](references/rules-tests.md) — TEST
- [NATS rules](references/rules-nats.md) — NATS / JetStream
- [Classification notes](references/rules-classification.md) — justified violations and SEC/UNSAFE classification guidance
- [OWASP Top 10:2021](references/owasp-2021.md) — A01--A10 mapping for security findings
- [Anti-patterns](references/anti-patterns.md) — Common cross-cutting anti-patterns
- [NATS security](references/nats-security.md) — NATS-specific SEC rule mapping
- [Flakiness patterns](references/flakiness-patterns.md) — Root causes and mitigations for flaky tests
- [Classification guide](references/classification-guide.md) — Test issue classification indicators
- [OpenAI agent metadata](assets/openai.yaml) — Optional agent configuration for compatible runtimes
