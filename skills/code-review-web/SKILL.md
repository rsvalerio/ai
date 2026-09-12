---
name: code-review-web
description: Reviews React and TypeScript code in Vite SPAs for hooks and type safety, async error handling, rendering performance, accessibility, XSS and Web Crypto security, and test quality including socket.io real-time patterns. Use while writing or editing frontend code as an implementation guardrail, or run a formal review that files one backlog task per finding.
allowed-tools: Read Grep Glob Bash(wc *) Bash(ls *) Bash(tree *) Bash(git rev-parse:*) Bash(git log:*) Bash(ops backlog:*) Bash(eslint *) Bash(npx eslint *) Bash(bunx eslint *) Bash(tsc *) Bash(npx tsc *) Bash(bunx tsc *)
license: Apache-2.0
---

# Web Code Review

Review React + TypeScript + Vite frontend code against all rule categories: React idioms & hooks, TypeScript type safety, async & error handling, performance, accessibility, security (XSS / Web Crypto / secrets / OWASP), complexity, readability, architecture, API design, duplication, test quality, and real-time (socket.io) patterns.

## Applicability

- Use this skill for formal frontend code reviews (React/TypeScript/Vite SPAs).
- Also use this skill as an implementation guardrail when making non-trivial frontend code changes: read the relevant rules, keep the change within those constraints, and avoid introducing new violations.
- In implementation guardrail mode, do not create backlog tasks unless the user explicitly asked for a formal review. Treat the rules as acceptance criteria for the code change and run the project's relevant QA gates (`eslint .`, `tsc -b --noEmit`, the test runner) before finishing.

## Purpose

- Create one backlog task per finding via `ops backlog task create --plain` command
- Scan all `.ts`/`.tsx` files, `package.json`, `tsconfig*.json`, `eslint.config.*`, `vite.config.*`, `vitest.config.*`, and test files
- Cover every rule category, working from [scan-checklist.md](references/scan-checklist.md) straight to the rule files it names, reading full rule text only where candidates appear
- Apply the priority order and severity scale defined in [rules.md](references/rules.md#design-philosophy)

## Relationship to ESLint / tsc (machine-enforced baseline)

Many mechanical rules are already enforced by `typescript-eslint`, `eslint-plugin-react-hooks` v7 (compiler-powered), and `tsc` in `strict` mode. **Do not file findings for what the configured tooling already catches** — running `eslint .` and `tsc -b --noEmit` is the baseline. This skill's unique value is what tools miss: design smells, severity nuance, security reasoning, missing test coverage, architectural drift, and rules the project hasn't enabled. When a rule references an ESLint rule (e.g. `no-floating-promises`), check whether the project already enables it before filing; if it does and passes, skip.

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

In implementation-guardrail mode, skip tier 1 entirely: read the tier-3 file for the one or
two categories your change touches (e.g. `rules/ASYNC.md` for an async change) and nothing else.

## Execution Contract (MUST follow)

You are running unattended — nobody is watching to course-correct. Follow these rules strictly:

1. **Findings are emitted ONLY via `ops backlog task create --plain`.** Do NOT print findings as prose, markdown, or a summary report in lieu of creating tasks. A text-only report is a failed run. If you identify a finding, the next action is a `ops backlog task create --plain` call — not text output.
2. **Never ask for confirmation.** Do not ask "Would you like me to create these tasks?" or pause for approval. You are pre-authorized. Findings → `ops backlog task create --plain` immediately, no intermediate prompt. Questions to the user = failed run.
3. **If you delegate to subagents, you MUST wait for every one to return before finishing.** Never end the turn with subagents still in flight. Collect each subagent's findings and create the backlog tasks yourself — subagents report, the parent writes.
4. **The only terminal action is the summary table** (step 5 below), printed *after* all `ops backlog task create --plain` calls have succeeded. If you have not created tasks, you are not done.
5. **On tool failure, retry or report the specific error.** Do not silently degrade to a text report.

## Process

1. **Survey** — List all `.ts`/`.tsx` files and the config files (`package.json`, `tsconfig*.json`, `eslint.config.*`, `vite.config.*`, `vitest.config.*`); identify large files (>300 lines) and large components (>250 lines), map the module/feature structure and dependencies, enumerate test files (`*.test.ts(x)`, `*.spec.ts(x)`, `__tests__/`). Always **exclude** `node_modules/`, `dist/`, `build/`, `target/`, `public/`, `*.d.ts` (generated), and coverage output.
2. **Scan** — Walk [scan-checklist.md](references/scan-checklist.md) signal by signal. For every signal that hits, open `references/rules/<CATEGORY>.md` for the rule IDs it named and confirm against the full rule text. Do not read `rules/index.md` — tier 1 already gave you the IDs. Then work the checklist's **Sweep** list: those categories have no signal, so nothing above opens them, and skipping them silently drops their rules from the review. Categories with no hits and no relevant code need no rule file read. For each violation, prepare a finding with rule ID, severity, file location, description, and acceptance criteria
3. **Deduplicate** — Run `ops backlog search "<RULE-ID>" --plain` to check for existing tasks with the same finding ID. If one exists and is not marked Done, skip. If Done, create only if the issue has regressed. Group findings that target the same `(file, component/function)` at different granularity into a single finding with the broadest scope
4. **Create tasks** — For each finding, run `ops backlog task create --plain` with the flags below. Use a `"$(cat <<'EOF' ... EOF)"` heredoc for multi-line values (do NOT use `$'...'` ANSI-C quoting — it triggers an `ansi_c_string` safety prompt on every call).
5. **Summarize** — run `ops backlog task list --status 'Triage' --plain`

### Calibration rules (always apply before filing)

Counts from a raw grep are signal, not findings. Before turning a grep count into a finding:

- **Always scope out test code and config** for production-quality rules (READ-8 `console.log`, TS-1 `any`, TS-3 non-null `!`, ASYNC clones, etc.). Exclude anything inside a test file (`*.test.ts(x)`, `*.spec.ts(x)`, `__tests__/`, `__mocks__/`), a Vite/ESLint/Vitest config file, a `.d.ts` declaration, or generated code. A finding that disappears when test/config code is excluded is not a finding — do not file it.
- **Prefer a file:line candidate list over a raw count.** Put the list in the task description and let the reviewer verify. Never report aggregate counts like "63 `any`s" without the per-file breakdown behind them — those numbers routinely run inflated by test mocks, type-shim files, and third-party shims.
- **Rules with known false-positive patterns (TS-1/TS-2, TEST-1, REACT-7, ASYNC-7)** have a `**Scanning guidance:**` block in their detailed rule references. Read that guidance before filing — if every candidate falls under an accepted idiom (documented brand cast, DOMPurify-sanitized HTML, deliberate `void` fire-and-forget, assertion-helper test), do not file.
- **Respect documented justifications.** A cast with an adjacent comment explaining the invariant (e.g. `as unknown as readonly RemoteExcalidrawElement[]` for a missing upstream brand), a `// eslint-disable-next-line` with a written rationale, or a `dangerouslySetInnerHTML` fed by a sanitizer is one severity level down — often not a finding (see [classification notes](references/rules-classification.md)).
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
  -l "code-review-web,<category>" \
  --priority <critical|high|medium|low> \
  --modified-file "<path>" \
  --ac "<acceptance criterion 1>" \
  --ac "<acceptance criterion 2>" \
  --plain
```

**`--modified-file` is required.** Pass one flag per file the finding touches,
repo-root-relative and **without** the `:<line>` suffix (`src/components/Foo.tsx`, not
`src/components/Foo.tsx:42`). This is the machine-readable twin of the `**File**:` line in
the description: `code-review-triage` reads it to compute each wave's file scope and merge
order, and `ops backlog search --modified-file <path>` finds every finding touching a path. A
finding filed without it is invisible to both.

Map severity to `--priority`: critical→critical, high→high, medium→medium, low→low. The `<category>` label is the lowercased rule-category name (`react`, `typescript`, `async`, `perf`, `a11y`, `structure`, `duplication`, `security`, `tests`, `realtime`).

## Rule Categories and Severity Scale

See [rules.md](references/rules.md#finding-ids-and-categories) for the canonical rule-category table and severity scale. Severity: Critical > High > Medium > Low, mirroring the priority order Safety/security > correctness > maintainability > style.

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
  - [`rules/REACT.md`](references/rules/REACT.md) — React components, hooks & effects (7 KB)
  - [`rules/TS.md`](references/rules/TS.md) — TypeScript type safety & modeling (4 KB)
  - [`rules/ASYNC.md`](references/rules/ASYNC.md) — Async & error handling (3 KB)
  - [`rules/PERF.md`](references/rules/PERF.md) — Performance (2 KB)
  - [`rules/A11Y.md`](references/rules/A11Y.md) — Accessibility (2 KB)
  - [`rules/FN.md`](references/rules/FN.md) — Functions & structure (2 KB)
  - [`rules/READ.md`](references/rules/READ.md) — Readability (2 KB)
  - [`rules/ARCH.md`](references/rules/ARCH.md) — Architecture & modules (2 KB)
  - [`rules/API.md`](references/rules/API.md) — Component API design (1 KB)
  - [`rules/CL.md`](references/rules/CL.md) — Cognitive load (1 KB)
  - [`rules/DUP.md`](references/rules/DUP.md) — Duplication (2 KB)
  - [`rules/SEC.md`](references/rules/SEC.md) — Security (XSS, Web Crypto, secrets, fetch, build) (7 KB)
  - [`rules/TEST.md`](references/rules/TEST.md) — Test quality (Vitest + RTL) (5 KB)
  - [`rules/RT.md`](references/rules/RT.md) — Real-time (socket.io-client / WebSocket) (3 KB)
- [Classification notes](references/rules-classification.md) — justified violations and SEC classification guidance
- [OWASP Top 10:2025](references/owasp-2025.md) — A01--A10 mapping for security findings
- [Anti-patterns](references/anti-patterns.md) — Common cross-cutting anti-patterns
- [Flakiness patterns](references/flakiness-patterns.md) — Root causes and mitigations for flaky frontend tests
- [OpenAI agent metadata](assets/openai.yaml) — Optional agent configuration for compatible runtimes
