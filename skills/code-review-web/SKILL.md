---
name: code-review-web
description: Reviews web frontend code (React + TypeScript + Vite SPAs) and acts as an implementation guardrail for frontend changes, covering React idioms and hooks, TypeScript type safety, async/error handling, performance/re-renders, accessibility, security (XSS, Web Crypto, secrets, OWASP), complexity, readability, architecture, duplication, test quality, and real-time/socket.io usage. Use during authoring or editing of React/TypeScript code to prevent rule violations before they ship, and for formal reviews where findings are filed as backlog tasks.
allowed-tools: Read Grep Glob Bash(wc *) Bash(ls *) Bash(tree *) Bash(git rev-parse:*) Bash(git log:*) Bash(backlog task:*) Bash(backlog search:*) Bash(eslint *) Bash(npx eslint *) Bash(bunx eslint *) Bash(tsc *) Bash(npx tsc *) Bash(bunx tsc *)
license: Apache-2.0
---

# Web Code Review

Review React + TypeScript + Vite frontend code against all rule categories: React idioms & hooks, TypeScript type safety, async & error handling, performance, accessibility, security (XSS / Web Crypto / secrets / OWASP), complexity, readability, architecture, API design, duplication, test quality, and real-time (socket.io) patterns.

## Applicability

- Use this skill for formal frontend code reviews (React/TypeScript/Vite SPAs).
- Also use this skill as an implementation guardrail when making non-trivial frontend code changes: read the relevant rules, keep the change within those constraints, and avoid introducing new violations.
- In implementation guardrail mode, do not create backlog tasks unless the user explicitly asked for a formal review. Treat the rules as acceptance criteria for the code change and run the project's relevant QA gates (`eslint .`, `tsc -b --noEmit`, the test runner) before finishing.

## Purpose

- Create one backlog task per finding via `backlog task create --plain` command
- Scan all `.ts`/`.tsx` files, `package.json`, `tsconfig*.json`, `eslint.config.*`, `vite.config.*`, `vitest.config.*`, and test files
- Check every rule category in [rules.md](references/rules.md)
- Apply the priority order and severity scale defined in [rules.md](references/rules.md#design-philosophy)

## Relationship to ESLint / tsc (machine-enforced baseline)

Many mechanical rules are already enforced by `typescript-eslint`, `eslint-plugin-react-hooks` v7 (compiler-powered), and `tsc` in `strict` mode. **Do not file findings for what the configured tooling already catches** — running `eslint .` and `tsc -b --noEmit` is the baseline. This skill's unique value is what tools miss: design smells, severity nuance, security reasoning, missing test coverage, architectural drift, and rules the project hasn't enabled. When a rule references an ESLint rule (e.g. `no-floating-promises`), check whether the project already enables it before filing; if it does and passes, skip.

## Execution Contract (MUST follow)

You are running unattended — nobody is watching to course-correct. Follow these rules strictly:

1. **Findings are emitted ONLY via `backlog task create --plain`.** Do NOT print findings as prose, markdown, or a summary report in lieu of creating tasks. A text-only report is a failed run. If you identify a finding, the next action is a `backlog task create --plain` call — not text output.
2. **Never ask for confirmation.** Do not ask "Would you like me to create these tasks?" or pause for approval. You are pre-authorized. Findings → `backlog task create --plain` immediately, no intermediate prompt. Questions to the user = failed run.
3. **If you delegate to subagents, you MUST wait for every one to return before finishing.** Never end the turn with subagents still in flight. Collect each subagent's findings and create the backlog tasks yourself — subagents report, the parent writes.
4. **The only terminal action is the summary table** (step 5 below), printed *after* all `backlog task create --plain` calls have succeeded. If you have not created tasks, you are not done.
5. **On tool failure, retry or report the specific error.** Do not silently degrade to a text report.

## Process

1. **Survey** — List all `.ts`/`.tsx` files and the config files (`package.json`, `tsconfig*.json`, `eslint.config.*`, `vite.config.*`, `vitest.config.*`); identify large files (>300 lines) and large components (>250 lines), map the module/feature structure and dependencies, enumerate test files (`*.test.ts(x)`, `*.spec.ts(x)`, `__tests__/`). Always **exclude** `node_modules/`, `dist/`, `build/`, `target/`, `public/`, `*.d.ts` (generated), and coverage output.
2. **Scan** — Check all rule categories from [rules.md](references/rules.md) against the codebase. For each violation, prepare a finding with rule ID, severity, file location, description, and acceptance criteria
3. **Deduplicate** — Run `backlog search "<RULE-ID>" --plain` to check for existing tasks with the same finding ID. If one exists and is not marked Done, skip. If Done, create only if the issue has regressed. Group findings that target the same `(file, component/function)` at different granularity into a single finding with the broadest scope
4. **Create tasks** — For each finding, run `backlog task create --plain` with the flags below. Use a `"$(cat <<'EOF' ... EOF)"` heredoc for multi-line values (do NOT use `$'...'` ANSI-C quoting — it triggers an `ansi_c_string` safety prompt on every call).
5. **Summarize** — run `backlog task list --status 'Triage' --plain`

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
backlog task create "<RULE-ID>: <Title>" \
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
order, and `backlog search --modified-file <path>` finds every finding touching a path. A
finding filed without it is invisible to both.

Map severity to `--priority`: critical→critical, high→high, medium→medium, low→low. The `<category>` label is the lowercased rule-category name (`react`, `typescript`, `async`, `perf`, `a11y`, `structure`, `duplication`, `security`, `tests`, `realtime`).

## Rule Categories and Severity Scale

See [rules.md](references/rules.md#finding-ids-and-categories) for the canonical rule-category table and severity scale. Severity: Critical > High > Medium > Low, mirroring the priority order Safety/security > correctness > maintainability > style.

## Scan Checklist

Survey for these signals, then check against the corresponding rules:

| Signal | Rules to check |
|--------|----------------|
| `useEffect` doing data fetching without cleanup / abort | REACT-7, ASYNC-3 |
| `useEffect` computing derived state, or doing work that belongs in an event handler | REACT-5, REACT-6 |
| `// eslint-disable*next*line react-hooks/exhaustive-deps` | REACT-4 |
| Reflexive `useMemo`/`useCallback`/`memo` (React Compiler era) *(see REACT-10 scanning guidance)* | REACT-10 |
| Array index as `key` in a reorderable/editable list | REACT-12 |
| `forwardRef` in new code; `<Context.Provider>` instead of `<Context value>` | REACT-13, REACT-14 |
| `any` / `as unknown as` double-cast / non-null `!` in non-test code *(exclude `.d.ts`, mocks, documented brand casts — see TS-1/TS-2 scanning guidance)* | TS-1, TS-2, TS-3 |
| Boolean/optional flag soup for mutually-exclusive states | TS-5 |
| Type-only imports without `import type` | TS-9 |
| `switch` over a union without a `never` exhaustiveness default | TS-11 |
| Floating promise; promise passed to `if`/`&&`/void callback | ASYNC-1, ASYNC-2 |
| `fetch` without `response.ok` check, or without timeout/`AbortController` | ASYNC-4, ASYNC-5 |
| Async state set after await with no race/stale guard | ASYNC-3 |
| No error boundary around a subtree that can throw | ASYNC-6 |
| Context provider value rebuilt every render (new object/array/fn) | PERF-2 |
| Expensive compute in render body; missing list virtualization; no route/code splitting | PERF-3, PERF-4, PERF-5 |
| `div`/`span` with `onClick` and no keyboard handling; missing `alt`/label | A11Y-1, A11Y-2 |
| `dangerouslySetInnerHTML` / `innerHTML` with untrusted data | SEC-1, SEC-2 |
| User-controlled URL in `href`/`src` without scheme allowlist (`javascript:`/`data:`) | SEC-3 |
| AES-GCM IV reuse; `Math.random` for security values; extractable keys; key/plaintext in logs | SEC-5, SEC-6, SEC-7, SEC-8 |
| Hardcoded secret/token in source; secret assumed safe behind `VITE_`; capability token in query string | SEC-9, SEC-10, SEC-11 |
| Unvalidated fetch/WebSocket response shape; sensitive data in `console`/telemetry | SEC-12, SEC-13 |
| Production source maps; unaudited/unpinned dependencies | SEC-14, SEC-15 |
| socket.io inbound message used without validation; authz only at connect; no message/rate bound | RT-1, RT-2, RT-3 |
| Volatile events not throttled; persisted broadcasts not debounced; no echo dedup | RT-4, RT-5 |
| Component file >250 lines; fn >50 lines; nesting >4; params >5 | ARCH-1, FN-1, FN-2, FN-3 |
| `console.log`/`console.debug` left in production code | READ-8 |
| Mixed concerns (fetch + UI + business logic) in one component; circular imports | ARCH-2, ARCH-5 |
| Duplicated JSX/logic/fetch/type blocks (3+) | DUP-1, DUP-2, DUP-3 |
| Test without assertion; `getByTestId` where a role query fits; `fireEvent` over `userEvent` | TEST-1, TEST-3, TEST-4 |
| Security-critical unit (crypto, parsing, auth) with no test | TEST-5, TEST-6 |

## Concurrency

This skill is read-only on the codebase and creates tasks only via the `backlog` CLI. Multiple instances can run in parallel — each finding gets its own task, so there are no write conflicts.

Finish all reviews before running `code-review-triage`, so the resulting waves capture every finding. Reviews are also safe to run while waves are executing — they only add new `Triage` tasks and never touch wave state — but findings filed mid-wave land in the *next* triage pass, not the current one.

## References

- [Rules index](references/rules.md) — Category table, severity scale, design philosophy, and links to all detailed rule references
- [Core rules](references/rules-core.md) — REACT, TS, ASYNC, PERF, A11Y
- [Structure rules](references/rules-structure.md) — FN, READ, ARCH, API
- [Duplication rules](references/rules-duplication.md) — DUP
- [Security rules](references/rules-security.md) — SEC (XSS, Web Crypto, secrets, fetch, build)
- [Test rules](references/rules-tests.md) — TEST (Vitest + React Testing Library)
- [Real-time rules](references/rules-realtime.md) — RT (socket.io-client / WebSocket)
- [Classification notes](references/rules-classification.md) — justified violations and SEC classification guidance
- [OWASP Top 10:2025](references/owasp-2025.md) — A01--A10 mapping for security findings
- [Anti-patterns](references/anti-patterns.md) — Common cross-cutting anti-patterns
- [Flakiness patterns](references/flakiness-patterns.md) — Root causes and mitigations for flaky frontend tests
- [OpenAI agent metadata](assets/openai.yaml) — Optional agent configuration for compatible runtimes
