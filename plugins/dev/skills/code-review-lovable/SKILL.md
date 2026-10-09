---
name: code-review-lovable
description: Reviews Lovable-style apps — Vite + React + TypeScript + Tailwind + shadcn/ui on Supabase or Lovable Cloud (Postgres RLS, Auth, Storage, Edge Functions), TanStack Query, Zustand, react-hook-form + zod, and Shopify Storefront commerce — for the stack layer generic React review misses, such as missing or permissive RLS policies, unchecked supabase-js or GraphQL errors, service-role or Shopify Admin token leaks, unauthenticated or value-minting Edge Functions, cache-key bleed, prices checkout does not charge, client-only validation, design-token drift and scaffold hygiene. Use whenever asked to review such code or say what is wrong with it, including a Supabase migration, Edge Function or supabase-js snippet pasted into the chat; while writing or editing such an app as an implementation guardrail; or to run a formal review that files one backlog task per finding.
allowed-tools: Read Grep Glob Bash(git rev-parse:*) Bash(git log:*) Bash(ops --version) Bash(ops backlog:*) Bash(ops typecheck) Bash(ops lint) Bash(ops explain:*) Bash(npm run lint) Bash(npm test) Bash(npx tsc:*) Bash(npx vitest:*)
license: Apache-2.0
---

# Lovable Stack Code Review

Review the **stack layer** of a Lovable-generated (or Lovable-shaped) app: Supabase schema and
RLS migrations, supabase-js usage, Supabase Auth (including Lovable Cloud's managed OAuth), Edge
Functions, TanStack Query and persisted Zustand stores, forms (zod, with or without
react-hook-form), shadcn/ui + Tailwind, Shopify Storefront commerce when the app uses Lovable's
Shopify integration, and the Lovable scaffold itself.

This skill is an **overlay on `code-review-web`**, not a replacement. Generic React, TypeScript,
async, a11y, XSS and test rules stay in `code-review-web`. Rules here exist only because this
stack makes something easy to get wrong. A formal review of a Lovable app runs both skills.
Their rule prefixes do not overlap and their identity keys cannot collide.

## Applicability

- Use this skill when the repo has the stack's fingerprints: `src/integrations/supabase/client.ts`,
  a `supabase/` directory (`migrations/`, `functions/`, `config.toml`), `components.json`
  (shadcn), `@tanstack/react-query` in `package.json`, `lovable-tagger` in `vite.config.ts`, or a
  `.lovable/` directory. `@lovable.dev/cloud-auth-js` or `src/integrations/lovable/` means
  **Lovable Cloud**: the same Supabase stack, but buckets, secrets and auth settings are managed
  by Lovable's tools and are not in the repo. `X-Shopify-Storefront-Access-Token` or a
  `*.myshopify.com` domain (usually in `src/lib/shopify.ts`) puts the `SHOP` category in play.
  `zustand` with `persist` puts QRY-7 in play. A stack with only some of these fingerprints still
  qualifies. Categories whose code is absent
  cost nothing. A formal review covers a package, directory or repository, or is any request to
  file findings; the Execution Contract and Process below apply to it only.
- Also use it as an implementation guardrail for non-trivial changes in such an app, especially
  any change that touches a migration, an RLS policy, an Edge Function or auth. Read the tier-3
  file for the category you touch, keep the change inside it, and run the QA gates: `ops
  typecheck` / `ops lint` where the repo has an `.ops.toml`, otherwise the repo's own scripts
  (`npm run lint`, `npx tsc -p tsconfig.app.json --noEmit`, `npm test`). A scaffold's root
  `tsconfig.json` has `"files": []`, so point `tsc` at the app config. Do not file
  backlog tasks in guardrail mode unless the user asked for a formal review.
- **Ad-hoc review** — a migration, policy, Edge Function or component pasted into the
  conversation, or a question about one snippet ("what is wrong with this?"): answer in chat.
  Read the tier-3 file for each category the code touches, cite the rule ID for every problem you
  name, order them by the [severity scale](references/rules.md#severity-scale), and file no backlog
  tasks unless the user asks for them. Generic React/TS problems in the same snippet cite
  `code-review-web`'s IDs. A problem no rule covers is still worth naming; say it has no rule.
  The calibration rules below still apply: the publishable key is not a leak, and a single
  migration may be superseded by one you cannot see, so say so rather than assert the final state.
- Most of the stack's real authorization lives in SQL. A review that reads only `src/` has
  skipped the part most likely to hold a Critical finding.

## Purpose

- Create one backlog task per finding via `ops backlog task create --plain`.
- Scan `supabase/migrations/*.sql`, `supabase/functions/**/*.ts`, `supabase/config.toml`, the
  `.ts`/`.tsx` sources under `src/`, `package.json`, `tsconfig*.json`, `eslint.config.*`,
  `vite.config.*`, `tailwind.config.*`, `src/index.css`, `components.json`, `index.html` and,
  as context rather than code, `.lovable/plan.md`.
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
an Edge Function (EDGE-7). A Shopify credential is the exception: the token class decides, so it
is filed here as SHOP-1, and the **public** Storefront token is filed nowhere (see the
calibration rules).

## Loading rules (token discipline)

Same three tiers as `code-review-web`. Read only as deep as the finding requires.

| Tier | File | When to read |
|------|------|--------------|
| 1 | [scan-checklist.md](references/scan-checklist.md) | Start of every scan. Signal → rule IDs. |
| 2 | [rules/index.md](references/rules/index.md) | **Not part of a scan.** For resolving a rule ID you hold without a signal. |
| 3 | `references/rules/<CATEGORY>.md` | Full rule text. **Required before filing** — never file from a one-liner. |

In guardrail and ad-hoc review modes skip tier 1: read the tier-3 file for the category your
change, or the code under review, touches (`rules/RLS.md` for a migration, `rules/EDGE.md` for a
function) and nothing else.

## Execution Contract (MUST follow)

Formal review only — guardrail and ad-hoc review modes answer in chat instead. Identical to
`code-review-web`'s contract. In short:

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
   candidate and a clean report proves nothing about RLS-2 / RLS-3. Read `.lovable/plan.md` if
   present, for what Lovable is mid-way through and what waits on setup outside the repo
   (LOV-6). On Lovable Cloud, note what the repo cannot show: bucket `public` flags, secrets and
   the auth redirect allow list. Findings that depend on them say so rather than guess. If the app
   uses Shopify, list the Storefront helper, the cart store and every pinned API version. A formal
   review needs `.backlog/tasks/`. If `ops backlog task list` reports none, stop and tell the user
   to run `ops backlog init`; do not create it yourself. **Exclude** `node_modules/`, `dist/`,
   `supabase/.temp/` and `src/components/ui/` (vendored shadcn, scanned only for UI-4 and for
   LOV-5's unused primitives). Also
   exclude `src/integrations/supabase/types.ts`, which is generated and scanned only for SUPA-10
   and LOV-4 drift.
2. **Scan** — Walk [scan-checklist.md](references/scan-checklist.md). For the SQL categories,
   reconstruct the **final** schema state from the ordered migrations before judging a table: a
   later migration may enable RLS or drop a policy. A finding against an intermediate state is
   a false positive.
3. **Deduplicate** — Identity key `<RULE-ID>:<path>:<enclosing item>`. The enclosing item is the
   component, hook or function, or the Edge Function name. For SQL, the key must come out the same
   on every run, so fix both parts. `<path>` is the **earliest migration that creates the object
   the rule is about**: the table for RLS-1/2/3/9/10/11, the function for RLS-4, the view for
   RLS-5, the bucket for RLS-6, and the policy for RLS-7. `<enclosing item>` is that object's
   schema-qualified name (`public.notes`, `public.has_role`). Use it even when the defect sits
   in a later migration, and never key the migration that happened to show the defect. One
   table's missing RLS is one finding however many migrations touch it. For the project-wide
   findings, key the file the rule names: SHOP-5 at the browser file holding the version constant,
   QRY-1's shared literal key at the first file using it (enclosing item: the key, `['products']`),
   and QRY-7 at the store file. List every `file:line` in the description.
4. **Create tasks** — see below.
5. **Summarize** — `ops backlog task list --status 'Triage' --plain`.

### Calibration rules (always apply before filing)

- **The anon / publishable key is public by design.** `VITE_SUPABASE_URL` and
  `VITE_SUPABASE_PUBLISHABLE_KEY` (or `..._ANON_KEY`) in `client.ts` or a committed `.env` are
  not a secret leak. Neither is the anon JWT that the generated `client.ts` often hardcodes as a
  literal. Do not file SEC-10 or SUPA-4 for them. Only a **service-role** key or a
  third-party secret is a leak.
- **The public Shopify Storefront token is public by design.** A hardcoded
  `X-Shopify-Storefront-Access-Token` value in `src/lib/shopify.ts` is how Shopify intends browser
  storefronts to work. Do not file SEC-10 or SHOP-1 for it. A private Storefront token, an Admin
  token (`shpat_`) or an app secret (`shpss_`) in the browser is SHOP-1, Critical.
- **Guest-submission tables are not open writes.** An insert-only `with check (true)` for `anon`
  on a form table (restock alerts, contact, waitlist) is judged on its owner column and abuse
  limits (RLS-2 / RLS-3), not filed as "anyone can modify everyone's data".
- **Lovable Cloud objects made by tools are not migration drift.** A bucket or secret with no
  migration is expected there (RLS-6, RLS-8).
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
the same migration as the identity key's `<path>` so triage can order the wave, and say in the
acceptance criteria that the fix lands as a new migration file.

`<category>` is the lowercased prefix (`rls`, `supa`, `auth`, `edge`, `qry`, `form`, `ui`, `shop`,
`lov`).

## Finding ID Prefixes

| Prefix | Category | Rule file |
|--------|----------|-----------|
| `RLS` | Postgres schema, RLS policies, SQL functions, storage policies | [rules/RLS.md](references/rules/RLS.md) |
| `SUPA` | supabase-js client usage (queries, errors, realtime, storage, types) | [rules/SUPA.md](references/rules/SUPA.md) |
| `AUTH` | Supabase Auth flows, sessions, roles | [rules/AUTH.md](references/rules/AUTH.md) |
| `EDGE` | Supabase Edge Functions (Deno) | [rules/EDGE.md](references/rules/EDGE.md) |
| `QRY` | TanStack Query and persisted Zustand stores | [rules/QRY.md](references/rules/QRY.md) |
| `FORM` | react-hook-form + zod | [rules/FORM.md](references/rules/FORM.md) |
| `UI` | shadcn/ui + Tailwind design system | [rules/UI.md](references/rules/UI.md) |
| `SHOP` | Shopify Storefront / Admin API (tokens, GraphQL errors, prices, cart, versions) | [rules/SHOP.md](references/rules/SHOP.md) |
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
  [FORM](references/rules/FORM.md), [UI](references/rules/UI.md), [SHOP](references/rules/SHOP.md),
  [LOV](references/rules/LOV.md)
- [OpenAI agent metadata](assets/openai.yaml)
