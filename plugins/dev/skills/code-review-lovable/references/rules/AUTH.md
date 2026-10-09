# AUTH rules

Supabase Auth in a client-rendered SPA. Grounded in the Supabase Auth docs
(supabase.com/docs/guides/auth) and the `onAuthStateChange` reference.

## Authorization (typical severity: Critical)

**Detection heuristics** — search for: `role`, `is_admin`, `isAdmin` on a `profiles` table or
type; `ProtectedRoute` / `AdminRoute`; `if (user.email === '…')`; `.update({ role`.

- **AUTH-1.** Roles live in a dedicated table (`user_roles (user_id, role app_role)`) that users
  cannot write. They are checked through a `security definer` function (`has_role(auth.uid(),
  'admin')`) that is used in RLS policies and follows RLS-4's policy-helper case: unexposed
  schema, still executable by `authenticated`. A `role` / `is_admin` column on a
  `profiles` row the user can `UPDATE` is a self-service privilege escalation: RLS is row-level
  and cannot stop a user changing one column of their own row.
- **AUTH-2.** Gating a route, a button or a feature on the client (`<AdminRoute>`,
  `if (isPro)`) is UX. The same rule is enforced in RLS or in the Edge Function that does the
  work. A hardcoded admin email or user ID in `src/` is both a client-only check and a disclosure.
  — owasp.org/Top10/2025 A01

## Session lifecycle (typical severity: High)

- **AUTH-3.** One auth provider owns the session. It subscribes to `onAuthStateChange` once,
  right after the client is created, stores both `session` and `user`, and unsubscribes in its
  Effect cleanup. The listener receives `INITIAL_SESSION` once the stored session loads, so a
  separate `getSession()` call is optional, and two sources that disagree are a race. A provider
  that registers the listener first and then calls `getSession()` is fine. Version matters for what the callback may do. Before supabase-js 2.107, the callback ran
  under the auth lock, so awaiting another Supabase call inside it could deadlock, and the fix is
  to defer with `setTimeout(…, 0)`. From 2.107 callbacks may be `async` and call auth methods.
  On every version, never trigger a refresh from a `TOKEN_REFRESHED` event. Check the installed
  version in the lockfile before filing the deadlock half of this rule.
  — supabase.com/docs/reference/javascript/auth-onauthstatechange
- **AUTH-4.** On sign-out (and on user change), clear user-scoped client state: call
  `queryClient.clear()` or remove user-keyed queries, and reset stores and `localStorage` drafts.
  Otherwise the next user on the same browser sees the previous user's cached data until
  refetch. Zustand `persist` stores (QRY-7) survive `signOut` and reloads. Each one holding
  per-user data, such as a wishlist, preferences, a referral code or a cart tied to an account, is
  reset in the same handler (`useStore.persist.clearStorage()` plus a reset action). A store that
  is deliberately per-device, such as a guest cart or a compare tray, says so in a comment. Put
  the clearing in the one auth provider's `SIGNED_OUT` branch, not in each sign-out button.
- **AUTH-5.** Do not persist tokens yourself. The supabase client already stores and refreshes
  the session. A copy in `localStorage` / a context goes stale on refresh and outlives sign-out.

## Redirects (typical severity: Medium--High)

- **AUTH-6.** `signUp` / `signInWithOtp` / `signInWithOAuth` / `resetPasswordForEmail` pass an
  explicit `emailRedirectTo` / `redirectTo` built from `window.location.origin`, and that URL is in
  the project's Redirect URLs allow list. Without it, links fall back to the Site URL, which is
  often the Lovable preview domain, and break in production. On Lovable Cloud, managed OAuth goes
  through the generated `lovable.auth.signInWithOAuth(provider, { redirect_uri })`
  (`src/integrations/lovable/index.ts`, `@lovable.dev/cloud-auth-js`), which then calls
  `supabase.auth.setSession`. The same rule applies to its `redirect_uri`. Read its result too:
  it returns `{ redirected }` or `{ error }` and does not throw (SUPA-1). The allow list lives in
  the project's auth settings, in Lovable Cloud or the Supabase dashboard, not in the repo, so a
  finding names the URL to allow rather than asserting it is missing.
  — supabase.com/docs/guides/auth/redirect-urls
- **AUTH-7.** A post-login `?redirect=` / `?next=` parameter is validated as a same-origin
  relative path before `navigate()` / `window.location` uses it. Otherwise it is an open
  redirect.
