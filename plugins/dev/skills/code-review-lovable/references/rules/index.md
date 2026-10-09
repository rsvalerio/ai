# Lovable stack rule index

One line per rule, enough to decide whether a rule is in play. Before filing, read the rule's
full text in the category file linked from its heading. Never file from the index line alone.

## RLS — Database & RLS · [rules/RLS.md](RLS.md)

- **RLS-1** Every `public` table has RLS enabled. Without it the anon key reads and writes everything.
- **RLS-2** Write policies bind rows to `auth.uid()`. No `using (true)` / `with check (true)` on writes, except an insert-only guest-submission table.
- **RLS-3** INSERT/UPDATE policies constrain the new row's owner column. An explicit `with check (true)` lets users reassign rows or file them as someone else.
- **RLS-4** `security definer` functions set `search_path`, authorize internally, and are not RPC-exposed unless intended.
- **RLS-5** Views in `public` use `security_invoker = true`, or they bypass base-table RLS.
- **RLS-6** User-private storage buckets are not public. Object policies scope by the user's folder. Tool-made buckets: an anon `SELECT` policy is exposure; `getPublicUrl` is only a signal.
- **RLS-7** No policy queries its own table. Use a `security definer` helper to avoid recursion.
- **RLS-8** Schema changes are new migrations. Never edit an applied one or change the dashboard only. Lovable Cloud tool-made buckets and secrets are not this.
- **RLS-9** Data invariants are enforced by DB constraints, not only by the form's zod schema.
- **RLS-10** Wrap `auth.uid()` as `(select auth.uid())` in policies, index the compared columns, and drop a permissive policy only when another already implies it.
- **RLS-11** Grants match intent: no broad `anon` grants on private tables, and every client-used table is granted.

## SUPA — Supabase client · [rules/SUPA.md](SUPA.md)

- **SUPA-1** Read `error` on every supabase-js call. It returns errors instead of throwing.
- **SUPA-2** Use `.maybeSingle()` when zero rows is legitimate. `.single()` errors on zero rows.
- **SUPA-3** Bound list queries with `.range()` / `.limit()`. Max-rows truncates silently. Select only the columns you need.
- **SUPA-4** Never ship a service-role or secret key to the browser. The anon key is fine.
- **SUPA-5** Never interpolate user input into `.or()` / `.filter()` / `.order()` strings.
- **SUPA-6** Writes that must succeed together run in one Postgres function or Edge Function, not sequential client calls.
- **SUPA-7** Use the single shared client. No extra `createClient` in components.
- **SUPA-8** Realtime channels are removed on cleanup and filtered server-side.
- **SUPA-9** Serve private files by signed URL. Upload paths are unique per user.
- **SUPA-10** Type the client with generated `Database` types kept in sync. Regenerate rather than cast.

## AUTH — Auth · [rules/AUTH.md](AUTH.md)

- **AUTH-1** Roles live in a non-writable `user_roles` table checked via a `has_role()` definer function, not a profile column.
- **AUTH-2** Client-side gating is UX. Enforce the same rule in RLS or the Edge Function.
- **AUTH-3** One provider subscribes to `onAuthStateChange` once and unsubscribes. Before supabase-js 2.107, never await client calls in the callback.
- **AUTH-4** Clear user-scoped caches and persisted Zustand stores on sign-out and on user change.
- **AUTH-5** Do not persist tokens yourself. The client manages the session.
- **AUTH-6** Auth emails and OAuth (including `lovable.auth.signInWithOAuth`) pass an explicit, allow-listed redirect URL.
- **AUTH-7** Validate post-login redirect parameters as same-origin relative paths.

## EDGE — Edge Functions · [rules/EDGE.md](EDGE.md)

- **EDGE-1** Derive the user in the handler, never from the body. `verify_jwt` alone is not user auth. Justify every `verify_jwt = false`.
- **EDGE-2** Prefer the caller-scoped client. Scope every service-role query to the verified user. No hybrid service-role + caller-header client.
- **EDGE-3** Paid, quota-spending or value-minting (discount code, gift card) functions require auth and a per-user limit.
- **EDGE-4** Check the method and schema-validate the body before any side effect.
- **EDGE-5** Webhooks verify the signature on the raw body and are idempotent on the event ID.
- **EDGE-6** Handle preflight. Restrict origins for privileged functions. Never reflect Origin with credentials.
- **EDGE-7** Secrets from env, fail closed. Generic error bodies with correct statuses. Timeouts on outbound fetch.
- **EDGE-8** Reserve the DB row before an irreversible external side effect, make it idempotent, and reconcile unknown outcomes before retrying.
- **EDGE-9** Current, pinned imports (`Deno.serve`, `npm:` supabase-js); shared constants in `_shared/`.

## QRY — Server state · [rules/QRY.md](QRY.md)

- **QRY-1** Query keys include every variable the `queryFn` reads. One literal key is never shared by different `queryFn` arguments.
- **QRY-2** `queryFn` / `mutationFn` throw on supabase `error`, so failures reach the error state.
- **QRY-3** Mutations invalidate or update affected queries. Optimistic updates roll back on error.
- **QRY-4** Keep server state in the cache. No `useEffect` fetches and no copying `data` into state or a Zustand store.
- **QRY-5** Use `enabled` for dependent queries. Create the `QueryClient` once.
- **QRY-6** Render loading, error, empty and not-yet-enabled states. `isPending` never clears on a disabled query.
- **QRY-7** Persisted Zustand stores carry `version` + `migrate`, `partialize` to client state, and respect rehydration.

## FORM — Forms · [rules/FORM.md](FORM.md)

- **FORM-1** Validate with zod through `zodResolver` (or `safeParse` feeding the payload). The form type is `z.infer` of the schema.
- **FORM-2** Enforce protective schema rules server-side too (constraint or Edge Function).
- **FORM-3** Coerce numbers and dates, mapping `""` away first so it does not become `0`. Map empty optional fields to `null`.
- **FORM-4** Disable submit while pending, surface server errors, and act only on success.
- **FORM-5** Use the `Form*` or `Field` composition so labels and errors are ARIA-linked.

## UI — Design system · [rules/UI.md](UI.md)

- **UI-1** Use semantic design tokens, not raw palette colours or hex values, in feature components.
- **UI-2** Never build Tailwind class names dynamically. Map to full class strings.
- **UI-3** Merge `className` with `cn()` so overrides win.
- **UI-4** Keep `src/components/ui/` generic and vendored. Use variants, not forks.
- **UI-5** Dialog-like content has a Title. Below Radix 1.1.20, it also has a Description or opts out explicitly.
- **UI-6** Use `asChild` instead of nesting interactive elements. Give the slot one child.
- **UI-7** Use one toast system, not both shadcn Toaster and sonner.

## SHOP — Shopify commerce · [rules/SHOP.md](SHOP.md)

- **SHOP-1** Only the public Storefront token reaches the browser. Private Storefront, Admin (`shpat_`) and app secrets stay server-side.
- **SHOP-2** Read top-level `errors` and mutation `userErrors` (GraphQL fails with 200). Throw, never return `undefined`, in a `queryFn`.
- **SHOP-3** The price shown is the price charged. Savings come from selling plans or Shopify discounts, not client math.
- **SHOP-4** The Shopify cart is the source of truth. Revalidate a persisted `cartId`, rebuild lines from the response, use the returned `checkoutUrl`.
- **SHOP-5** One API version constant, inside Shopify's 12-month support window. Retired versions silently fall forward.

## LOV — Scaffold hygiene · [rules/LOV.md](LOV.md)

- **LOV-1** Add a real typecheck gate, then tighten the scaffold's loose tsconfig/ESLint baseline in stages, starting with `strictNullChecks`.
- **LOV-2** Run `componentTagger()` only in development. `lovable-tagger` is a devDependency.
- **LOV-3** Use one package manager and one committed lockfile.
- **LOV-4** Do not hand-edit Lovable-generated files (Supabase client/types, `previewAuthStorage.ts`, `integrations/lovable/`).
- **LOV-5** Remove dead pages, near-duplicate components and unused shadcn primitives and deps.
- **LOV-6** No placeholder behaviour (fake saves, mock data, hardcoded auth) on reachable paths. Read `.lovable/plan.md` first.
- **LOV-7** Replace scaffold `index.html` metadata with the app's own.
