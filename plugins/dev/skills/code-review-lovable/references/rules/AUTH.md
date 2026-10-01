# AUTH rules

Supabase Auth in a client-rendered SPA. Grounded in the Supabase Auth docs
(supabase.com/docs/guides/auth) and the `onAuthStateChange` reference.

## Authorization (typical severity: Critical)

**Detection heuristics** — search for: `role`, `is_admin`, `isAdmin` on a `profiles` table or
type; `ProtectedRoute` / `AdminRoute`; `if (user.email === '…')`; `.update({ role`.

- **AUTH-1.** Roles live in a dedicated table (`user_roles (user_id, role app_role)`) that users
  cannot write. They are checked through a `security definer` function (`has_role(auth.uid(),
  'admin')`) that obeys RLS-4 and is used in RLS policies. A `role` / `is_admin` column on a
  `profiles` row the user can `UPDATE` is a self-service privilege escalation: RLS is row-level
  and cannot stop a user changing one column of their own row.
- **AUTH-2.** Gating a route, a button or a feature on the client (`<AdminRoute>`,
  `if (isPro)`) is UX. The same rule is enforced in RLS or in the Edge Function that does the
  work. A hardcoded admin email or user ID in `src/` is both a client-only check and a disclosure.
  — owasp.org/Top10/2025 A01

## Session lifecycle (typical severity: High)

- **AUTH-3.** One auth provider owns the session. It registers `onAuthStateChange` **before**
  calling `getSession()`, so no event is missed between them. It stores both `session` and
  `user`, and it unsubscribes in its Effect cleanup. Do not `await` other supabase calls inside
  the callback, because the callback holds the auth lock and an awaited client call can
  deadlock. Defer with `setTimeout(…, 0)`.
  — supabase.com/docs/reference/javascript/auth-onauthstatechange
- **AUTH-4.** On sign-out (and on user change), clear user-scoped client state: call
  `queryClient.clear()` or remove user-keyed queries, and reset stores and `localStorage` drafts.
  Otherwise the next user on the same browser sees the previous user's cached data until
  refetch.
- **AUTH-5.** Do not persist tokens yourself. The supabase client already stores and refreshes
  the session. A copy in `localStorage` / a context goes stale on refresh and outlives sign-out.

## Redirects (typical severity: Medium--High)

- **AUTH-6.** `signUp` / `signInWithOtp` / `signInWithOAuth` / `resetPasswordForEmail` pass an
  explicit `emailRedirectTo` / `redirectTo` built from `window.location.origin`, and that URL is in
  the project's allowed redirect list. Without it, confirmation links point at the Site URL
  (often the Lovable preview domain) and break in production.
  — supabase.com/docs/guides/auth/redirect-urls
- **AUTH-7.** A post-login `?redirect=` / `?next=` parameter is validated as a same-origin
  relative path before `navigate()` / `window.location` uses it. Otherwise it is an open
  redirect.
