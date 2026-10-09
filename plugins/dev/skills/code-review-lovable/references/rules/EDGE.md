# EDGE rules

Supabase Edge Functions (`supabase/functions/<name>/index.ts`, Deno) and their settings in
`supabase/config.toml`. Grounded in the Supabase Edge Functions docs (auth, CORS, secrets,
webhooks) and the OWASP API Security Top 10.

## Authentication & authorization (typical severity: Critical)

**Detection heuristics** — search for: `verify_jwt = false` in `config.toml`;
`SUPABASE_SERVICE_ROLE_KEY` / `SUPABASE_SECRET_KEYS`; `await req.json()` followed by `user_id` / `userId`;
`Access-Control-Allow-Origin`; `stripe` / `svix` / `webhook`; `api.openai.com`, `ai.gateway`, or
another paid upstream; `X-Shopify-Access-Token` / `/admin/api/` / `price_rules` /
`discount_codes`; a service-role `createClient` that also sets `global.headers.Authorization`.

- **EDGE-1.** A function that acts for a user derives the user **in the handler**, from a
  verified token. The current pattern is `withSupabase({ auth: 'user' })` from
  `npm:@supabase/server`, which gives `ctx.userClaims` and an RLS-scoped client. The older
  pattern is `supabase.auth.getUser(jwt)`, or `auth.getClaims()` with asymmetric signing keys.
  It never trusts a `user_id` in the request body. `verify_jwt = true`, the default, is **not**
  user authentication: for migration compatibility it also accepts the public publishable key.
  Every `verify_jwt = false` under `[functions.<name>]` in `config.toml` is justified by another
  mechanism in the function, such as a webhook signature (EDGE-5) or a shared secret.
  `sb_publishable_` / `sb_secret_` keys travel on the `apikey` header. They are not JWTs, so code
  that expects them as `Authorization: Bearer` JWTs is wrong.
  — supabase.com/docs/guides/functions/auth, supabase.com/docs/guides/functions/auth-headers
- **EDGE-2.** A client built with the service-role key bypasses RLS. Prefer a client that
  forwards the caller's `Authorization` header so RLS applies. Where service-role is needed,
  scope every query explicitly to the verified user and keep that client out of code paths that
  do not need it. Use two named clients when a function needs both. **The hybrid client is a
  finding:** `createClient(url, SERVICE_ROLE_KEY, { global: { headers: { Authorization:
  req.headers.get('Authorization') } } })`. supabase-js sends a caller-supplied `Authorization`
  header in place of the key's, so PostgREST runs that client's queries as the **caller**, with RLS.
  The service-role key buys nothing there, and a write the function believed was privileged fails
  with `42501` or matches zero rows. A typical case is an insert into a table with no `INSERT`
  policy. Meanwhile the code reads as if it bypasses RLS, so the next edit trusts it to. Pick one
  role per client. *(High; Critical if a path drops the header and falls back to real service role.)*
  — supabase.com/docs/guides/functions/auth
- **EDGE-3.** A function that spends money or quota (an LLM, email or SMS provider, or a paid
  API) or **mints value** (a discount code, gift card, price rule, store credit or referral reward,
  usually through the Shopify Admin API) requires authentication and enforces a per-user limit (a
  counter row, a rate limit, a plan check, a `unique` constraint on the reward row). An
  unauthenticated or unmetered endpoint is a bill anyone can run up. One that mints value is
  a coupon printer. The Lovable AI gateway (`ai.gateway.lovable.dev`, `LOVABLE_API_KEY`) is
  billed per call to the workspace, so it counts as paid.
  — owasp.org API4:2023 Unrestricted Resource Consumption

## Request handling (typical severity: High)

- **EDGE-4.** Validate the request: check the method, then parse the body with a schema (zod)
  and reject with `400` before any side effect. A `req.json()` destructured straight into a query
  or an upstream prompt is untrusted input.
- **EDGE-5.** Webhooks verify the provider's signature over the **raw** body (`await req.text()`
  before parsing). For Stripe on Deno that is
  `constructEventAsync(body, sig, secret, undefined, Stripe.createSubtleCryptoProvider())`, because
  the synchronous `constructEvent` throws there. They are idempotent on the event ID, because
  providers retry.
- **EDGE-6.** CORS: answer `OPTIONS` preflight, either through `withSupabase` (which handles it)
  or with the `corsHeaders` exported from `npm:@supabase/supabase-js/cors` (2.95+). Hand-written
  allow-header lists must include `x-retry-count`, because postgrest-js retries idempotent
  requests. Allow only the app's origins for functions that
  carry user authority. Never reflect the request `Origin` together with
  `Access-Control-Allow-Credentials: true`. The scaffold's `*` is acceptable for bearer-token
  functions with no cookie auth, so judge the function, not the header.
- **EDGE-7.** Secrets come from `Deno.env.get(…)` and the function fails closed when one is
  missing. Errors return a generic message and a correct status (`401`, `403`, `400`, `500`).
  Upstream response bodies, stack traces and SQL errors stay in the server log, not the response.
  Outbound `fetch` calls carry a timeout (`AbortSignal.timeout(ms)`).
  — supabase.com/docs/guides/functions/secrets
- **EDGE-8.** An irreversible external side effect comes after the database has reserved it, and
  is idempotent. Examples are minting a Shopify discount code, charging a card, or sending an
  email. Reserve first: insert the row, with a `unique` constraint on what makes it one-off, such
  as `referred_user_id`. Then perform the external call, and record its result on the row. "Call
  out, then insert" leaks a live code or a charge whenever the insert fails, through RLS, a
  constraint or a timeout. It also mints twice when the client retries or two tabs race the
  "already claimed?" check. A loop that mints per row, such as rewarding each pending referral,
  claims each row first: `update … set status = 'processing' where id = … and status = 'joined'
  returning id`. Only then does it call out. The call's outcome can also be **unknown**: a
  timeout or a dropped connection after the request left says nothing about whether it happened,
  so a blind retry can mint or charge twice and a blind give-up can strand a live code. Make the
  retry safe at the provider. Send its idempotency key where it has one (Stripe's
  `Idempotency-Key`), built from the reserved row's id. Where it has none, make the external
  identifier deterministic from that row, such as a discount code derived from the row id, so a
  second create collides instead of minting. Failing both, look the result up at the provider
  before retrying, and leave the row in its `processing` state for a reconciler rather than
  resetting it. Webhooks are EDGE-5. *(Typical severity: High.)*
- **EDGE-9.** Imports are current and pinned in one place. Lovable's older function template
  imports `serve` from `https://deno.land/std@0.168.0/http/server.ts`, which `Deno.serve`
  replaces, and `https://esm.sh/@supabase/supabase-js@2.x` pinned at whatever version was current
  when the function was written. A function client many minor versions behind the app's
  `@supabase/supabase-js` misses auth and PostgREST fixes the browser already has. Prefer
  `npm:@supabase/supabase-js@2` (or `npm:@supabase/server`, EDGE-1). Put shared helpers and
  constants (CORS headers, API versions, a store domain) in `supabase/functions/_shared/`, not
  copied per function. *(Typical severity: Low.)*
