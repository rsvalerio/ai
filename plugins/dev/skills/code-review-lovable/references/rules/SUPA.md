# SUPA rules

supabase-js v2 usage in browser code. Grounded in the supabase-js reference
(supabase.com/docs/reference/javascript) and the PostgREST docs.

## Errors & result shape (typical severity: High)

**Detection heuristics** — search for: `const { data } = await supabase`, `.single()`,
`.select('*')` without `.range` / `.limit`, `functions.invoke(` without an `error` read.

- **SUPA-1.** Read `error` on every supabase-js call. Unless a query opts in with
  `.throwOnError()` (or the client sets `throwOnError`), the client **returns** `{ data, error }`
  and does not throw, so `const { data } = await supabase.from(…)` turns a failed write, an RLS
  denial or a network error into "no rows" and the UI carries on. Branch on `error` and surface
  it, or throw it inside a query function (QRY-2). The same applies to `auth.*`, `storage.*`,
  `rpc` and `functions.invoke`. — supabase.com/docs/reference/javascript/select
  **Scanning guidance:** failures do not all look alike. A missing table grant returns a
  permission error. An `INSERT` blocked by RLS returns error `42501`. An `UPDATE` / `DELETE`
  whose policy filters the row out returns **no error and zero rows**. Where it matters, a write
  that must affect a row should `.select()` and check that a row came back. A query chained with
  `.throwOnError()` is compliant.
- **SUPA-2.** Use `.maybeSingle()` when zero rows is a legitimate outcome (a profile not created
  yet, an optional setting). `.single()` returns an error (`PGRST116`) for zero rows, which code
  then either crashes on or swallows as a generic failure. `.maybeSingle()` returns `null` for zero
  rows and still errors on more than one.
  — supabase.com/docs/reference/javascript/maybesingle
- **SUPA-3.** Bound every list query with `.range()` / `.limit()` and paginate. The API
  silently caps results at the project's max-rows setting (1000 by default), so an unbounded
  `select` truncates without error once data grows. Select the columns you render instead of
  `*`, which over-fetches and ships columns the UI should not see.

## Safety (typical severity: Critical--High)

- **SUPA-4.** Browser code uses only the publishable key (`sb_publishable_…`, or the legacy
  `anon` JWT). A secret key (`sb_secret_…`, or the legacy `service_role` JWT) anywhere under
  `src/`, in a `VITE_*` variable, or in `index.html` bypasses every RLS policy. Supabase rejects
  `sb_secret_` keys sent with a browser `User-Agent`, but that does not make a shipped one safe:
  it still works from curl or a script, and a legacy `service_role` JWT has no such block. The
  publishable key in `client.ts` is public by design and is **not** this finding.
  — supabase.com/docs/guides/getting-started/api-keys
- **SUPA-5.** Do not interpolate user input into PostgREST filter strings: ``.or(`title.ilike.%${q}%`)``,
  `.filter(col, op, raw)`, or a dynamic column name in `.order(userValue)`. Commas, dots and
  parentheses in the input rewrite the filter. postgrest-js documents that these methods take raw
  PostgREST syntax that the caller must sanitize. Use the typed builders
  (``.ilike('title', `%${q}%`)``), or wrap the value in double quotes with `"` and `\` escaped
  (the reserved characters are `, . : * ( )`), and allowlist column names.
  — postgrest.org/en/stable/references/api/url_grammar.html#reserved-characters
- **SUPA-6.** Multi-step writes that must succeed together, such as an order with its line items
  or a transfer between rows, do not run as sequential client calls. A failure midway leaves half
  the data written. Move them into a Postgres function called via `rpc` (one transaction) or into
  an Edge Function.

## Lifecycle & typing (typical severity: Medium)

- **SUPA-7.** Import the one client from `@/integrations/supabase/client`. A second `createClient`
  in a component or hook creates a separate auth state, and the client logs "Multiple
  GoTrueClient instances detected in the same browser context". Concurrent use under one storage
  key has undefined behaviour, and sessions desync.
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
