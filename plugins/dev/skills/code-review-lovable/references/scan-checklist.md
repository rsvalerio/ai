# Lovable Stack Scan Checklist

Observable signal → rules to check. Grep for the signal. When it hits, go straight to the full
rule in `rules/<CATEGORY>.md` and confirm there before filing. `rules/index.md` is not a scan
step. Work the SQL rows against the **final** migration state, not a single file.

| Signal | Rules to check |
|--------|----------------|
| `create table` in `public` with no later `enable row level security` for it | RLS-1 |
| `using (true)` / `with check (true)`; policy `to public` / `to anon` on a write; write policy with no `auth.uid()`; guest `INSERT` on a table with a nullable `user_id` | RLS-2, RLS-3 |
| `security definer` without `set search_path`; a `public` function with no `revoke execute … from public` (a revoke from `anon` alone does not count); a policy helper revoked from the role its policies run as | RLS-4 |
| `create view` in `public` without `security_invoker` | RLS-5 |
| `storage.buckets` row with `public` true for user content; `storage.objects` policy not keyed on `foldername`; a `storage.objects` `SELECT` policy open to `anon` with no owner predicate | RLS-6, SUPA-9 |
| A policy on table T whose expression selects from T; `infinite recursion` in issues/logs | RLS-7, AUTH-1 |
| Same migration file modified after a later one exists (`git log`); schema objects used in `src/` with no migration | RLS-8, SUPA-10 |
| Columns with zod `.min`/`.max`/`.email`/enum in a form but no `check`/`not null`/`unique` in SQL | RLS-9, FORM-2 |
| `grant all` / write grants `to anon`; a table used in `src/` with no `grant … to authenticated` in any migration | RLS-11 |
| Policy using bare `auth.uid()` (not `(select auth.uid())`); policy column with no index; two permissive policies for the same table, role and command | RLS-10 |
| `const { data } = await supabase` / `.then(({ data }) =>` with no `error` read; `functions.invoke` result unchecked | SUPA-1, QRY-2 |
| `.single()` on a lookup that may have no row | SUPA-2 |
| `.select(` on a list with no `.range(`/`.limit(`; `select('*')` | SUPA-3 |
| `service_role` / `SERVICE_ROLE` / `sb_secret_` / `SECRET_KEY` anywhere under `src/` or in a `VITE_` var | SUPA-4 |
| `.or(` / `.filter(` / `.order(` built from a template literal or user value | SUPA-5 |
| Two or more dependent `.insert`/`.update`/`.delete` in one handler | SUPA-6 |
| `createClient(` outside `src/integrations/supabase/` | SUPA-7 |
| `supabase.channel(` in an Effect without `removeChannel` in cleanup; `postgres_changes` without `filter` | SUPA-8 |
| `getPublicUrl(` for user files; upload path from `file.name` | SUPA-9 |
| `supabase as any`; `from('…' as any)`; hand-written row interfaces duplicating `types.ts` | SUPA-10 |
| `role` / `is_admin` column on `profiles`; hardcoded admin email/ID in `src/` | AUTH-1, AUTH-2 |
| `ProtectedRoute` / `AdminRoute` / `isPro` gating with no matching policy or function check | AUTH-2 |
| `onAuthStateChange` subscribed more than once or without unsubscribe; `await supabase…` in the callback on supabase-js < 2.107 | AUTH-3 |
| `signOut(` with no `queryClient.clear`/`removeQueries` nearby; `persist(` stores holding per-user data never cleared on sign-out | AUTH-4 |
| `localStorage.setItem` with `token`/`session`/`access_token` | AUTH-5 |
| `signUp(` / `signInWithOtp(` / `signInWithOAuth(` / `resetPasswordForEmail(` without `emailRedirectTo`/`redirectTo`; `lovable.auth.signInWithOAuth(` without `redirect_uri` or with its result unread | AUTH-6 |
| `searchParams.get('redirect'\|'next'\|'returnTo')` passed to `navigate`/`location` | AUTH-7 |
| `verify_jwt = false` in `supabase/config.toml`; `user_id` read from `req.json()` | EDGE-1 |
| `SUPABASE_SERVICE_ROLE_KEY` / `SUPABASE_SECRET_KEYS` in a function; a service-role `createClient` that also sets `global.headers.Authorization` | EDGE-2 |
| Function calling OpenAI / Lovable AI gateway / Resend / Twilio / another paid API; function minting discount codes, gift cards or price rules (`X-Shopify-Access-Token`, `/admin/api/`) | EDGE-3 |
| `await req.json()` destructured with no schema parse | EDGE-4 |
| Function named or handling `webhook` / `stripe` / `svix` | EDGE-5 |
| `Access-Control-Allow-Origin` reflecting `req.headers.get('origin')`; missing `OPTIONS` branch | EDGE-6 |
| Response body containing `error.message` / upstream text; `fetch(` without `signal`; secret literal in a function | EDGE-7 |
| External call (Shopify Admin, payment, email) before the `.insert(`/`.update(` that records it; a read-then-mint "already claimed?" check with no `unique` constraint or status claim; a retried external create with no idempotency key or deterministic identifier | EDGE-8 |
| `deno.land/std@…/http/server.ts` `serve`; `esm.sh/@supabase/supabase-js@2.<old>`; constants copied across functions | EDGE-9 |
| `queryKey: [` with only string literals while `queryFn` closes over variables; the same literal key in several files with different `queryFn` arguments | QRY-1 |
| `useMutation(` with no `onSuccess`/`onSettled` invalidation; `onMutate` without `onError` rollback | QRY-3 |
| `useEffect` + `useState` + `supabase.from` (or a Shopify fetch) in one component; `useState(query.data)`; query data copied into a Zustand store | QRY-4 |
| `useQuery` with an argument that may be `undefined` and no `enabled`; `new QueryClient()` inside a component | QRY-5 |
| `isLoading`/`isPending` branch with no `isError`/`error` branch; spinner on `isPending` for a query with `enabled` | QRY-6 |
| `persist(` from `zustand/middleware` with no `version`; `partialize` keeping functions or server data; persisted state read before hydration | QRY-7 |
| `useForm(` without `resolver`; per-field `useState` forms with no `safeParse`, or an insert built from raw state instead of `parsed.data` | FORM-1 |
| `type="number"` input with `z.number()` and no coercion; `z.coerce.number()` with no `""` pre-processing; `""` written to nullable columns | FORM-3 |
| Submit button without `disabled={isSubmitting\|isPending}`; mutation error not shown | FORM-4 |
| `register(` inputs outside `FormField` / `Field`; error `<p>` without `aria-describedby` | FORM-5 |
| `bg-(blue\|gray\|slate\|…)-\d+`, `text-white`, `bg-[#…]` in feature components | UI-1 |
| `` `bg-${`` / `` `text-${`` / `` `border-${`` template-literal classes | UI-2 |
| `className` prop merged by `+` or template literal instead of `cn(` | UI-3 |
| Edits under `src/components/ui/` importing app code; `*-2.tsx` / `Custom*.tsx` forks of primitives | UI-4 |
| `DialogContent` / `SheetContent` / `AlertDialogContent` / `DrawerContent` without a `Title` | UI-5 |
| `<Link>` wrapping `<Button>`; `asChild` with more than one child | UI-6 |
| Both `<Toaster />` and `<Sonner />` mounted; both `useToast` and `toast` from `sonner` imported | UI-7 |
| `X-Shopify-Access-Token` / `Shopify-Storefront-Private-Token` / `shpat_` / `shpss_` / `shppa_` under `src/` or in a `VITE_` var (the public `X-Shopify-Storefront-Access-Token` is fine) | SHOP-1 |
| Storefront helper checking only `response.ok` or only `errors`; cart mutation result read without `userErrors`; `return;` / toast in place of a throw | SHOP-2, QRY-2 |
| Price multiplied by a discount constant in `src/`; subscription UI with no `sellingPlanId` on the cart line; `$`/`€` hardcoded beside `amount` | SHOP-3 |
| Persisted `cartId`/`checkoutUrl` never revalidated with the `cart` query; local lines patched instead of rebuilt from the response; `checkoutUrl` host or path rebuilt | SHOP-4 |
| `api/20YY-MM/graphql.json` or `admin/api/20YY-MM` older than 12 months, or differing between `src/` and `supabase/functions/` | SHOP-5 |
| `strict`/`strictNullChecks`/`noImplicitAny` false in `tsconfig.app.json` or root `tsconfig.json`; `no-unused-vars` off; no `typecheck` script | LOV-1 |
| `componentTagger()` not gated on development mode; `lovable-tagger` in `dependencies` | LOV-2 |
| More than one lockfile at the root | LOV-3 |
| Hand edits in `git log -p` of `src/integrations/supabase/{client,types}.ts`, `previewAuthStorage.ts` or `src/integrations/lovable/index.ts` | LOV-4 |
| Pages/components with no importer; `*New.tsx`/`*2.tsx`/`*Old.tsx`; unused `src/components/ui/*` | LOV-5 |
| Submit handlers that only `console.log`/`toast`; `setTimeout` simulating saves; `mock*`/`sample*`/`dummy*` data rendered; `isAuthenticated = true`; features `.lovable/plan.md` says are blocked on setup but the UI presents as live | LOV-6 |
| `index.html` title/description/`og:image` still scaffold defaults; `cdn.gpteng.co/gptengineer.js` script | LOV-7 |

## Sweep — categories with no signal

None. Every category above has a signal row. If a category is added without one, list it here,
or `make validate-rules` reports it unreachable.
