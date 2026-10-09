# Lovable Stack Review Rules

All rule IDs for the `code-review-lovable` skill. Targets the stack Lovable scaffolds: Vite +
React + TypeScript + Tailwind + shadcn/ui, Supabase (Postgres + RLS, Auth, Storage, Realtime,
Edge Functions on Deno) or Lovable Cloud (the same Supabase stack, managed by Lovable), TanStack
Query v5, Zustand, react-hook-form + zod, React Router, and Shopify (Storefront API in the
browser, Admin API from Edge Functions) when the app uses Lovable's Shopify integration.

Generic React / TypeScript / async / a11y / XSS / test rules are **not** here. They live in
`code-review-web` and apply to the same app unchanged.

## Finding IDs and Categories

| Category | Prefix | Domain | Detailed rules |
|----------|--------|--------|----------------|
| Database & RLS | `RLS` | Tables, policies, `security definer` functions, views, storage policies, migrations | `rules/RLS.md` |
| Supabase client | `SUPA` | supabase-js errors, `.single()`, row limits, filter injection, realtime, storage, generated types | `rules/SUPA.md` |
| Auth | `AUTH` | Session lifecycle, roles, redirects, client-only gating | `rules/AUTH.md` |
| Edge Functions | `EDGE` | JWT verification, service-role scope, input validation, CORS, webhooks, cost and value-minting abuse, side-effect ordering | `rules/EDGE.md` |
| Server & client state | `QRY` | TanStack Query keys, errors, invalidation, dependent queries; persisted Zustand stores | `rules/QRY.md` |
| Forms | `FORM` | zod schemas, server-side mirror, submit lifecycle | `rules/FORM.md` |
| Design system | `UI` | shadcn/ui composition, Tailwind tokens and class hygiene | `rules/UI.md` |
| Shopify commerce | `SHOP` | Storefront/Admin token classes, GraphQL `errors`/`userErrors`, price truth, cart lifecycle, API versions | `rules/SHOP.md` |
| Scaffold hygiene | `LOV` | Loose tsconfig/ESLint, tagger, generated files, placeholder code, dead artefacts | `rules/LOV.md` |

## Severity Scale

| Level | Meaning |
|-------|---------|
| Critical | Data readable or writable by the wrong user, a leaked privileged key, or an unauthenticated paid or privileged endpoint |
| High | Silent data loss or corruption, auth flow bugs, cross-user cache bleed, a price shown that checkout does not charge |
| Medium | Quality or reliability issue worth addressing |
| Low | Consistency, hygiene, dormant concern |

## Design Philosophy

> "The browser is a public API client with the anon key. Everything it is not allowed to do must
> be impossible in Postgres, not merely hidden in React."

- RLS is the authorization layer, and client checks are UX.
- Every boundary is validated twice: zod in the form for the user, a constraint or function for
  the database.
- Server state belongs to the query cache, keyed by everything it depends on.
- supabase-js never throws, and GraphQL fails with `200`: an unread `error` or `userErrors` is a
  swallowed failure.
- Shopify owns the catalogue, cart and price. The UI shows what Shopify will charge.
- Generated and vendored code is regenerated, not edited.
