# EDGE rules

Supabase Edge Functions (`supabase/functions/<name>/index.ts`, Deno) and their settings in
`supabase/config.toml`. Grounded in the Supabase Edge Functions docs (auth, CORS, secrets,
webhooks) and the OWASP API Security Top 10.

## Authentication & authorization (typical severity: Critical)

**Detection heuristics** — search for: `verify_jwt = false` in `config.toml`;
`SUPABASE_SERVICE_ROLE_KEY` / `SUPABASE_SECRET_KEYS`; `await req.json()` followed by `user_id` / `userId`;
`Access-Control-Allow-Origin`; `stripe` / `svix` / `webhook`; `api.openai.com`, `ai.gateway`, or
another paid upstream.

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
  do not need it. — supabase.com/docs/guides/functions/auth
- **EDGE-3.** A function that spends money or quota (an LLM, email or SMS provider, or a paid
  API) requires authentication and enforces a per-user limit (a counter row, a rate limit, a plan
  check). An unauthenticated or unmetered endpoint is a bill anyone can run up.
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
