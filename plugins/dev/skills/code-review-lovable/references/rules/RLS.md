# RLS rules

Postgres schema, Row Level Security and SQL functions as shipped in `supabase/migrations/*.sql`.
Grounded in the Supabase docs (Row Level Security, Database Functions, Storage access control,
Securing your API) and the PostgreSQL manual (`CREATE POLICY`, `CREATE FUNCTION`, `CREATE VIEW`).

**Judge the final state.** Replay the migrations in order before filing. A table created
without RLS in `0001` and fixed in `0007` is not a finding.

## Access control (typical severity: Critical)

**Detection heuristics** — search for: `create table` in `public` without a matching `enable row
level security`; `using (true)` / `with check (true)`; `to anon`; `grant .* to anon`;
`security definer`; `create view`; `insert into storage.buckets` with `public`.

- **RLS-1.** Every table in an exposed schema (`public` by default) has `alter table … enable row
  level security`. RLS is still off by default for new tables. Without it, anyone holding the
  publishable key (`sb_publishable_…`, or the legacy `anon` key) can read and write every row
  through the Data API. A table with policies written but RLS never enabled (advisor lint
  `policy_exists_rls_disabled`) is the same finding. A table with RLS enabled and **no** policies
  is closed, which is safe, and is not this finding. Grants are a separate layer. Since
  2026-05-30 for new projects, and 2026-10-30 for all projects, a new table reaches the Data API
  only after an explicit `grant … to anon` / `authenticated`. Grants decide whether the table is
  reachable at all, and RLS decides which rows. Older tables keep their grants, so RLS remains the
  row boundary. Advisor lint: `rls_disabled_in_public`.
  — supabase.com/docs/guides/database/postgres/row-level-security,
  supabase.com/changelog/45329-breaking-change-tables-not-exposed-to-data-and-graphql-api-automatically
- **RLS-2.** Write policies (`INSERT`, `UPDATE`, `DELETE`, `ALL`) bind rows to the caller:
  `using ((select auth.uid()) = user_id)` and, for inserts, `with check ((select auth.uid()) =
  user_id)`. `using (true)` / `with check (true)` on a write lets any signed-in user, or anon if
  the policy is `to public`, modify everyone's data. `to authenticated` alone is not ownership.
  **Scanning guidance:** `using (true)` on a `SELECT` policy for data that is public by design is
  correct. File it only when the table holds per-user or private data. A **guest-submission
  table** (a restock alert, a contact or request form, a waitlist) with an `INSERT … with check
  (true)` policy `to anon, authenticated` and **no** anon `SELECT` / `UPDATE` / `DELETE` policy is
  also legitimate. An insert-only policy cannot touch anyone else's rows, so do not file it as
  "anyone can modify everyone's data". Judge such a table on three things instead: the owner
  column (RLS-3), abuse limits (a length `check` per RLS-9 and a rate limit or captcha, *Medium*),
  and whether the browser can read back what it wrote (it cannot without a `SELECT` policy, so an
  `.insert().select()` there fails).
- **RLS-3.** An `INSERT` or `UPDATE` policy must constrain the **owner column of the new row**. An
  `UPDATE` with `using (auth.uid() = user_id)` and an explicit `with check (true)` lets a user
  reassign their row to someone else. If `WITH CHECK` is omitted, Postgres reuses `USING`, which is
  fine. An explicit `with check (true)` is the bug. A guest-submission `INSERT` (RLS-2) that has a
  nullable `user_id` needs `with check (user_id is null or user_id = (select auth.uid()))`.
  With `with check (true)`, anyone can file rows attributed to another user, which that user then
  sees through their own `SELECT` policy. *(High.)* — postgresql.org/docs/current/sql-createpolicy.html
- **RLS-4.** `security definer` functions run as their owner and bypass RLS. Each one must
  (a) `set search_path = ''` (or a fixed schema) so a caller cannot shadow `public` objects,
  (b) perform its own authorization check against `auth.uid()`, and (c) be reachable only by the
  callers it is meant for. Postgres grants `EXECUTE` to `PUBLIC` on every new function, so a revoke
  from `anon` alone changes nothing, and every function in `public` is callable via
  `supabase.rpc()` by anyone with the publishable key. Pick the fix by what the function is for:
  - **Called only by triggers or other SQL:** `revoke execute on function … from public, anon,
    authenticated`.
  - **Called inside RLS policies** (a `has_role()` helper, see AUTH-1 / RLS-7): the policy runs as
    the querying role, so that role needs `EXECUTE`. Revoking it from `authenticated` makes every
    policy that calls the helper fail with `permission denied` for signed-in users. Move the helper
    to a schema the Data API does not expose (for example `private`), `revoke … from public`, and
    `grant execute … to authenticated` (and to `anon` only if an `anon` policy calls it). It then
    keeps working in policies without being an RPC.
  - **A deliberate RPC:** keep it in `public`, grant it only to the roles that should call it, and
    rely on check (b).

  Advisor lint: `function_search_path_mutable`.
  — supabase.com/docs/guides/database/functions#security-definer-vs-invoker
- **RLS-5.** Views in `public` run with the **view owner's** privileges and bypass the base
  tables' RLS. Create them `with (security_invoker = true)` (Postgres 15+), or keep them out of
  the exposed schema. Advisor lint: `security_definer_view`. — supabase.com/docs/guides/database/postgres/row-level-security#views
- **RLS-6.** Storage: a bucket holding per-user files is not `public`. A public bucket skips
  only the **read** check and serves every object to anyone with the URL. Uploads, updates and
  deletes still go through `storage.objects` policies, so a public bucket also needs write
  policies. Those policies scope by path, as in
  `(storage.foldername(name))[1] = (select auth.uid()::text)`, and uploads use that path.
  **Scanning guidance:** on Lovable Cloud a storage tool creates buckets, usually without a
  migration (look for a comment such as "bucket created via tool"), so the bucket's `public` flag
  is not in the repo. Infer it from what you can see: a `SELECT` policy on `storage.objects` with
  no role and no owner predicate, or `getPublicUrl(` on the bucket, means anyone can read it. State
  in the finding that the flag itself was not visible. A missing bucket migration is not RLS-8.
  — supabase.com/docs/guides/storage/security/access-control
- **RLS-7.** No policy may query the table it protects (a `profiles` policy that selects from
  `profiles` to check a role). It fails with `infinite recursion detected in policy` (42P17), or
  it works by accident and stops when the policy changes. Move the lookup into a
  `security definer` helper (see AUTH-1) that follows RLS-4's policy-helper case. The helper must be owned by a role that
  bypasses RLS on the looked-up table, such as `postgres`.
- **RLS-11.** Grants match intent. A `grant all … to anon` (or `to anon` on a write privilege) on a
  table holding private data widens the surface RLS has to hold alone, so grant the privileges
  the client uses to the role that uses them. Conversely, a table created after the explicit-grants
  change (see RLS-1) and queried from `src/` with no `grant … to authenticated` fails with a
  permission error in production. That second case is a correctness finding (High), not security.
  — supabase.com/changelog/45329-breaking-change-tables-not-exposed-to-data-and-graphql-api-automatically

## Integrity & lifecycle (typical severity: Medium--High)

- **RLS-8.** Schema changes land as **new** migration files. Never edit a migration that has
  already been applied, and never change the schema in the dashboard without a migration. Each
  divergence is a database that cannot be rebuilt from the repo, and remote changes made outside
  migrations make `supabase db push` fail. Dashboard edits belong on the local stack, captured
  with `supabase db diff`. The fix for any RLS finding is a new migration. On Lovable Cloud, Lovable
  writes and applies the migration for each approved schema change, and creates storage buckets and
  secrets through its own tools rather than through migrations. Those tool-made objects are not
  RLS-8 divergence. A migration file whose content changed after a later one exists still is.
  — supabase.com/docs/guides/deployment/database-migrations
- **RLS-9.** Invariants the UI validates are also enforced in the database: `not null`,
  `check` (length, range, enum), `unique`, and foreign keys with a deliberate `on delete`. A zod
  schema in the browser is advisory, because the REST API accepts whatever the anon key can send
  (see FORM-2).
- **RLS-10.** Policy predicates call `auth.uid()` / `auth.jwt()` wrapped as `(select auth.uid())`
  so Postgres evaluates them once per statement, not per row. The columns they compare
  (`user_id`, `org_id`) are indexed. Policies name their role with `to authenticated` so that anon
  requests skip them. Unwrapped calls on a large table are a full scan with a function call per
  row. Advisor lint: `auth_rls_initplan`. Two permissive policies for the same role and command
  (often a second `create policy` added by a later prompt, sometimes inside an `if not exists`
  block under a new name) are all evaluated and `OR`ed together. That costs time on every row and
  hides which one is meant to govern, so drop the duplicate. Advisor lint:
  `multiple_permissive_policies`. *(Typical severity: Medium.)*
  — supabase.com/docs/guides/database/postgres/row-level-security-performance
