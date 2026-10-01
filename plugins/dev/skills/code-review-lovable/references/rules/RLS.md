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
  level security`. Without it, anyone holding the public anon key can read and write every row
  through the REST API. A table with RLS enabled and **no** policies is closed, which is safe,
  and is not this finding. — supabase.com/docs/guides/database/postgres/row-level-security
- **RLS-2.** Write policies (`INSERT`, `UPDATE`, `DELETE`, `ALL`) bind rows to the caller:
  `using ((select auth.uid()) = user_id)` and, for inserts, `with check ((select auth.uid()) =
  user_id)`. `using (true)` / `with check (true)` on a write lets any signed-in user, or anon if
  the policy is `to public`, modify everyone's data. `to authenticated` alone is not ownership.
  **Scanning guidance:** `using (true)` on a `SELECT` policy for data that is public by design is
  correct. File it only when the table holds per-user or private data.
- **RLS-3.** An `INSERT` or `UPDATE` policy must constrain the **owner column of the new row**. An
  `UPDATE` with `using (auth.uid() = user_id)` and an explicit `with check (true)` lets a user
  reassign their row to someone else. If `WITH CHECK` is omitted, Postgres reuses `USING`, which is
  fine. An explicit `with check (true)` is the bug. — postgresql.org/docs/current/sql-createpolicy.html
- **RLS-4.** `security definer` functions run as their owner and bypass RLS. Each one must
  (a) `set search_path = ''` (or a fixed schema) so a caller cannot shadow `public` objects,
  (b) perform its own authorization check against `auth.uid()`, and (c) live in a non-exposed
  schema or have `execute` revoked from `anon` / `public` when it is not meant to be an RPC.
  Functions in `public` are callable via `supabase.rpc()` by anyone with the anon key.
  — supabase.com/docs/guides/database/functions#security-definer-vs-invoker
- **RLS-5.** Views in `public` run with the **view owner's** privileges and bypass the base
  tables' RLS. Create them `with (security_invoker = true)` (Postgres 15+), or keep them out of
  the exposed schema. — supabase.com/docs/guides/database/postgres/row-level-security#views
- **RLS-6.** Storage: a bucket holding per-user files is not `public`. `storage.objects`
  policies scope by path, as in `(storage.foldername(name))[1] = (select auth.uid())::text`, and
  uploads use that path. A public bucket serves every object to anyone with the URL.
  — supabase.com/docs/guides/storage/security/access-control
- **RLS-7.** No policy may query the table it protects (a `profiles` policy that selects from
  `profiles` to check a role). It fails with `infinite recursion detected in policy` (42P17), or
  it works by accident and stops when the policy changes. Move the lookup into a
  `security definer` helper (see AUTH-1) that obeys RLS-4.

## Integrity & lifecycle (typical severity: Medium--High)

- **RLS-8.** Schema changes land as **new** migration files. Never edit a migration that has
  already been applied, and never change the schema in the dashboard without a migration. Each
  divergence is a database that cannot be rebuilt from the repo. The fix for any RLS finding is a
  new migration. — supabase.com/docs/guides/deployment/database-migrations
- **RLS-9.** Invariants the UI validates are also enforced in the database: `not null`,
  `check` (length, range, enum), `unique`, and foreign keys with a deliberate `on delete`. A zod
  schema in the browser is advisory, because the REST API accepts whatever the anon key can send
  (see FORM-2).
- **RLS-10.** Policy predicates call `auth.uid()` / `auth.jwt()` wrapped as `(select auth.uid())`
  so Postgres evaluates them once per statement, not per row. The columns they compare
  (`user_id`, `org_id`) are indexed. Unwrapped calls on a large table are a full scan with a
  function call per row. *(Typical severity: Medium.)*
  — supabase.com/docs/guides/database/postgres/row-level-security#rls-performance-recommendations
