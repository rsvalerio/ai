# SUPA rules

supabase-js v2 usage in browser code. Grounded in the supabase-js reference
(supabase.com/docs/reference/javascript) and the PostgREST docs.

## Errors & result shape (typical severity: High)

**Detection heuristics** — search for: `const { data } = await supabase`, `.single()`,
`.select('*')` without `.range` / `.limit`, `functions.invoke(` without an `error` read.

- **SUPA-1.** Read `error` on every supabase-js call. The client **returns** `{ data, error }`
  and does not throw, so `const { data } = await supabase.from(…)` turns a failed write, an RLS
  denial or a network error into "no rows" and the UI carries on. Branch on `error` and surface
  it, or throw it inside a query function (QRY-2). The same applies to `auth.*`, `storage.*`,
  `rpc` and `functions.invoke`. — supabase.com/docs/reference/javascript/select
  **Scanning guidance:** an RLS-denied `UPDATE` / `DELETE` returns **no error and zero rows**.
  Where it matters, a write that must affect a row should `.select()` and check that a row came
  back.
- **SUPA-2.** Use `.maybeSingle()` when zero rows is a legitimate outcome (a profile not created
  yet, an optional setting). `.single()` returns an error (`PGRST116`) for zero rows, which code
  then either crashes on or swallows as a generic failure.
  — supabase.com/docs/reference/javascript/maybesingle
- **SUPA-3.** Bound every list query with `.range()` / `.limit()` and paginate. The API
  silently caps results at the project's max-rows setting (1000 by default), so an unbounded
  `select` truncates without error once data grows. Select the columns you render instead of
  `*`, which over-fetches and ships columns the UI should not see.

## Safety (typical severity: Critical--High)

- **SUPA-4.** Browser code uses only the anon / publishable key. A `service_role` / secret key
  anywhere under `src/`, in a `VITE_*` variable, or in `index.html` bypasses every RLS policy for
  whoever opens devtools. The anon key in `client.ts` is public by design and is **not** this
  finding. — supabase.com/docs/guides/api/api-keys
- **SUPA-5.** Do not interpolate user input into PostgREST filter strings: ``.or(`title.ilike.%${q}%`)``,
  `.filter(col, op, raw)`, or a dynamic column name in `.order(userValue)`. Commas, dots and
  parentheses in the input rewrite the filter. Use the typed builders
  (``.ilike('title', `%${q}%`)``), escape reserved characters, or allowlist column names.
  — postgrest.org/en/stable/references/api/tables_views.html#horizontal-filtering
- **SUPA-6.** Multi-step writes that must succeed together, such as an order with its line items
  or a transfer between rows, do not run as sequential client calls. A failure midway leaves half
  the data written. Move them into a Postgres function called via `rpc` (one transaction) or into
  an Edge Function.

## Lifecycle & typing (typical severity: Medium)

- **SUPA-7.** Import the one client from `@/integrations/supabase/client`. A second `createClient`
  in a component or hook creates a separate auth state and a "Multiple GoTrueClient instances"
  warning, and sessions desync.
- **SUPA-8.** Realtime: every `supabase.channel(…).subscribe()` in an Effect is torn down with
  `supabase.removeChannel(channel)` in the cleanup. Subscriptions use a server-side `filter` (for
  example `user_id=eq.${id}`) rather than receiving the whole table and filtering in JS. Leaked
  channels multiply handlers on every remount. — supabase.com/docs/guides/realtime/postgres-changes
- **SUPA-9.** Storage: private files are served through `createSignedUrl` with a short expiry,
  never `getPublicUrl` (which only works for public buckets, see RLS-6). Uploads validate type
  and size client-side for UX. Object paths are unique per user, not the raw file name, which
  collides and overwrites.
- **SUPA-10.** The client is typed with the generated `Database` type, and that type matches
  the migrations. `supabase as any`, `from('x' as any)` or a hand-written row interface that
  shadows the generated one means the types are stale. Regenerate them rather than casting.
  — supabase.com/docs/guides/api/rest/generating-types
