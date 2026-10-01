---
name: code-review-lovable
description: Reviews Lovable-style apps — Vite + React + TypeScript + Tailwind + shadcn/ui on Supabase (Postgres RLS, Auth, Storage, Edge Functions) with TanStack Query and react-hook-form + zod — for the stack layer generic React review misses, such as missing or permissive RLS policies, unchecked supabase-js errors, service-role leaks, unauthenticated Edge Functions, cache-key bleed, client-only validation, design-token drift and scaffold hygiene. Use while writing or editing such an app as an implementation guardrail, or run a formal review that files one backlog task per finding.
allowed-tools: Read Grep Glob Bash(git rev-parse:*) Bash(git log:*) Bash(ops --version) Bash(ops backlog:*) Bash(ops typecheck) Bash(ops lint) Bash(ops explain:*)
license: Apache-2.0
---

# Lovable Stack Code Review

Review the **stack layer** of a Lovable-generated (or Lovable-shaped) app: Supabase schema and
RLS migrations, supabase-js usage, Supabase Auth, Edge Functions, TanStack Query, forms
(react-hook-form + zod), shadcn/ui + Tailwind, and the Lovable scaffold itself.

This skill is an **overlay on `code-review-web`**, not a replacement. Generic React, TypeScript,
async, a11y, XSS and test rules stay in `code-review-web`. Rules here exist only because this
stack makes something easy to get wrong. A formal review of a Lovable app runs both skills.
Their rule prefixes do not overlap and their identity keys cannot collide.

## Applicability

- Use this skill when the repo has the stack's fingerprints: `src/integrations/supabase/client.ts`,
  a `supabase/` directory (`migrations/`, `functions/`, `config.toml`), `components.json`
  (shadcn), `@tanstack/react-query` in `package.json`, or `lovable-tagger` in `vite.config.ts`.
  A stack with only some of these fingerprints still qualifies. Categories whose code is absent
  cost nothing.
- Also use it as an implementation guardrail for non-trivial changes in such an app, especially
  any change that touches a migration, an RLS policy, an Edge Function or auth. Read the tier-3
  file for the category you touch, keep the change inside it, and run the QA gates. Do not file
  backlog tasks in guardrail mode unless the user asked for a formal review.
- Most of the stack's real authorization lives in SQL. A review that reads only `src/` has
  skipped the part most likely to hold a Critical finding.

## Purpose

- Create one backlog task per finding via `ops backlog task create --plain`.
- Scan `supabase/migrations/*.sql`, `supabase/functions/**/*.ts`, `supabase/config.toml`, the
  `.ts`/`.tsx` sources under `src/`, `package.json`, `tsconfig*.json`, `eslint.config.*`,
  `vite.config.*`, `tailwind.config.*`, `src/index.css`, `components.json` and `index.html`.
- Cover every rule category: work from [scan-checklist.md](references/scan-checklist.md)
  straight to the rule files it names.
- Apply the severity scale in [rules.md](references/rules.md#severity-scale). One stack-specific
  bias applies: the anon key is public, so **RLS is the authorization layer**. A gap in it is
  Critical by default, never "defence in depth".

## Relationship to code-review-web and the tooling baseline

`code-review-web` assumes `tsc --strict` and a configured ESLint are a real baseline and skips
what they catch. The Lovable scaffold ships a deliberately loose one: `strict: false` and
`noImplicitAny: false` in `tsconfig.app.json`, `strictNullChecks: false` in the root
`tsconfig.json`, and `no-unused-vars` off. The root `tsconfig.json` has `"files": []`, so a bare
`tsc --noEmit` checks nothing. Check the actual config before you trust it: a weak baseline is
itself finding LOV-1, and while it stands, do not skip a rule on the grounds that "the tooling
catches it".

The scaffold is also **React 18** (with Vite 5 and Tailwind v3). `code-review-web`'s React 19
rules (REACT-13 `forwardRef`, REACT-14 `<Context value>`, REACT-18 to REACT-20 Actions, `use()`
and metadata) do not apply until the app upgrades. Check `react` in `package.json` before filing
them.

Do not re-file here what `code-review-web` owns. A raw `dangerouslySetInnerHTML` is SEC-1
there, an `any` is TS-1 there, and a missing `alt` is A11Y-2 there. File here only when the
stack is what makes the code wrong. An unchecked `{ data }` from supabase-js is SUPA-1, not
ASYNC-4. A third-party secret (an OpenAI, Stripe or Resend key) in `src/` or a `VITE_*` variable
is `code-review-web` SEC-10 / SEC-11. In this stack the fix it names is a Supabase secret read by
an Edge Function (EDGE-7).

## Loading rules (token discipline)

Same three tiers as `code-review-web`. Read only as deep as the finding requires.

| Tier | File | When to read |
|------|------|--------------|
| 1 | [scan-checklist.md](references/scan-checklist.md) | Start of every scan. Signal → rule IDs. |
| 2 | [rules/index.md](references/rules/index.md) | **Not part of a scan.** For resolving a rule ID you hold without a signal. |
| 3 | `references/rules/<CATEGORY>.md` | Full rule text. **Required before filing** — never file from a one-liner. |

In guardrail mode skip tier 1: read the tier-3 file for the category your change touches
(`rules/RLS.md` for a migration, `rules/EDGE.md` for a function) and nothing else.

## Execution Contract (MUST follow)

Identical to `code-review-web`'s contract. In short:

1. Findings are emitted **only** via `ops backlog task create --plain`. A prose report in their
   place is a failed run.
2. Never ask for confirmation. You are pre-authorized to file.
3. Wait for every subagent you delegate to. Subagents report, the parent files.
4. The only terminal action is the summary (step 5), printed after all tasks exist.
5. On tool failure, retry or report the specific error.

## Process

1. **Survey** — Requires `ops` 0.74.0 or newer (`ops --version`). Confirm the stack fingerprints
   above and note which categories are in play. List migrations in order, Edge Functions,
   `config.toml` function settings, routes (`src/App.tsx`), and pages. Read `tsconfig*.json` and
   the ESLint config so you know the real baseline (LOV-1). If the repo carries output from
   Lovable's security scan or the Supabase database advisors, read it as input. Those tools check
   that RLS **exists**, not that the policies are correct, so an open finding there is a
   candidate and a clean report proves nothing about RLS-2 / RLS-3. **Exclude** `node_modules/`, `dist/`,
   `supabase/.temp/` and `src/components/ui/` (vendored shadcn, scanned only for UI-4). Also
   exclude `src/integrations/supabase/types.ts`, which is generated and scanned only for SUPA-10
   and LOV-4 drift.
2. **Scan** — Walk [scan-checklist.md](references/scan-checklist.md). For the SQL categories,
   reconstruct the **final** schema state from the ordered migrations before judging a table: a
   later migration may enable RLS or drop a policy. A finding against an intermediate state is
   a false positive.
3. **Deduplicate** — Identity key `<RULE-ID>:<path>:<enclosing item>`. The enclosing item is the
   component, hook or function, the Edge Function name, or for SQL the **table, policy or function
   name**, not the migration file. One table's missing RLS is one finding however many
   migrations touch it. List every `file:line` in the description.
4. **Create tasks** — see below.
5. **Summarize** — `ops backlog task list --status 'Triage' --plain`.

### Calibration rules (always apply before filing)

- **The anon / publishable key is public by design.** `VITE_SUPABASE_URL` and
  `VITE_SUPABASE_PUBLISHABLE_KEY` (or `..._ANON_KEY`) in `client.ts` or a committed `.env` are
  not a secret leak. Neither is the anon JWT that the generated `client.ts` often hardcodes as a
  literal. Do not file SEC-10 or SUPA-4 for them. Only a **service-role** key or a
  third-party secret is a leak.
- **Judge RLS on the final migration state**, as in step 2.
- **`using (true)` is not always wrong.** On a `SELECT` policy for data that is public by design
  (a published catalog, public profiles' display names), it is correct. Say why it is public, or
  do not file. On `INSERT` / `UPDATE` / `DELETE` it is almost always a finding.
- **The Lovable scaffold's defaults are findings once, not per file.** The loose tsconfig, both
  toasters mounted, and the unused shadcn primitives are each one finding at the config or root
  file, not one per occurrence.
- **Placeholder code** (LOV-6) is filed only when it sits on a reachable path that a user would
  believe works. A clearly labelled demo route is not a finding.
- Same as `code-review-web`: exclude tests and config for production-quality rules, prefer a
  `file:line` candidate list to a count, and mark imprecise scans with
  `<!-- scan confidence: candidates to inspect -->`.

## Creating a Task

```bash
ops backlog task create "<RULE-ID>: <Title>" \
  -d "$(cat <<'EOF'
**File**: `<path>:<line>`

**What**: <what is wrong>

**Why it matters**: <impact>
EOF
)" \
  -s "Triage" \
  -l "code-review-lovable,<category>" \
  --priority <critical|high|medium|low> \
  --modified-file "<path>" \
  --ac "<acceptance criterion 1>" \
  --unless-exists "<RULE-ID>:<path>:<enclosing item>" \
  --plain
```

**`--modified-file` is required**, one per touched path, repo-root-relative, no `:<line>`. An
RLS fix is a **new** migration, not an edit to an applied one (RLS-8). For an RLS finding, pass
the migration that introduced the table so triage can order the wave, and say in the
acceptance criteria that the fix lands as a new migration file.

`<category>` is the lowercased prefix (`rls`, `supa`, `auth`, `edge`, `qry`, `form`, `ui`, `lov`).

## Finding ID Prefixes

| Prefix | Category | Rule file |
|--------|----------|-----------|
| `RLS` | Postgres schema, RLS policies, SQL functions, storage policies | [rules/RLS.md](references/rules/RLS.md) |
| `SUPA` | supabase-js client usage (queries, errors, realtime, storage, types) | [rules/SUPA.md](references/rules/SUPA.md) |
| `AUTH` | Supabase Auth flows, sessions, roles | [rules/AUTH.md](references/rules/AUTH.md) |
| `EDGE` | Supabase Edge Functions (Deno) | [rules/EDGE.md](references/rules/EDGE.md) |
| `QRY` | TanStack Query | [rules/QRY.md](references/rules/QRY.md) |
| `FORM` | react-hook-form + zod | [rules/FORM.md](references/rules/FORM.md) |
| `UI` | shadcn/ui + Tailwind design system | [rules/UI.md](references/rules/UI.md) |
| `LOV` | Lovable scaffold and AI-iteration hygiene | [rules/LOV.md](references/rules/LOV.md) |

## Severity Scale

See [rules.md](references/rules.md#severity-scale). Critical > High > Medium > Low, mirroring
security > correctness > maintainability > style.

## Scan Checklist

[scan-checklist.md](references/scan-checklist.md) — read at the start of every scan.

## Concurrency

Read-only on the codebase. It writes only through `ops backlog`. It is safe to run in parallel
with `code-review-web` over the same repo, and that is the recommended way to review a Lovable
app. Finish both before `code-review-triage`.

## References

- [Rules](references/rules.md) — category table, severity scale, design philosophy
- [Scan checklist](references/scan-checklist.md) — signal → rules (tier 1)
- [Rule index](references/rules/index.md) — one line per rule (tier 2)
- Full rules, one file per category (tier 3): [RLS](references/rules/RLS.md),
  [SUPA](references/rules/SUPA.md), [AUTH](references/rules/AUTH.md),
  [EDGE](references/rules/EDGE.md), [QRY](references/rules/QRY.md),
  [FORM](references/rules/FORM.md), [UI](references/rules/UI.md), [LOV](references/rules/LOV.md)
- [OpenAI agent metadata](assets/openai.yaml)
