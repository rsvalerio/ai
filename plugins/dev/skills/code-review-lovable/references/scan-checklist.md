# Lovable Stack Scan Checklist

Observable signal → rules to check. Grep for the signal. When it hits, go straight to the full
rule in `rules/<CATEGORY>.md` and confirm there before filing. `rules/index.md` is not a scan
step. Work the SQL rows against the **final** migration state, not a single file.

| Signal | Rules to check |
|--------|----------------|
| `create table` in `public` with no later `enable row level security` for it | RLS-1 |
| `using (true)` / `with check (true)`; policy `to public` / `to anon` on a write; write policy with no `auth.uid()` | RLS-2, RLS-3 |
| `security definer` without `set search_path`; no `revoke execute … from anon` on a non-RPC helper | RLS-4 |
| `create view` in `public` without `security_invoker` | RLS-5 |
| `storage.buckets` row with `public` true for user content; `storage.objects` policy not keyed on `foldername` | RLS-6, SUPA-9 |
| A policy on table T whose expression selects from T; `infinite recursion` in issues/logs | RLS-7, AUTH-1 |
| Same migration file modified after a later one exists (`git log`); schema objects used in `src/` with no migration | RLS-8, SUPA-10 |
| Columns with zod `.min`/`.max`/`.email`/enum in a form but no `check`/`not null`/`unique` in SQL | RLS-9, FORM-2 |
| `grant all` / write grants `to anon`; a table used in `src/` with no `grant … to authenticated` in any migration | RLS-11 |
| Policy using bare `auth.uid()` (not `(select auth.uid())`); policy column with no index | RLS-10 |
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
| `signOut(` with no `queryClient.clear`/`removeQueries` nearby | AUTH-4 |
| `localStorage.setItem` with `token`/`session`/`access_token` | AUTH-5 |
| `signUp(` / `signInWithOtp(` / `signInWithOAuth(` / `resetPasswordForEmail(` without `emailRedirectTo`/`redirectTo` | AUTH-6 |
| `searchParams.get('redirect'\|'next'\|'returnTo')` passed to `navigate`/`location` | AUTH-7 |
| `verify_jwt = false` in `supabase/config.toml`; `user_id` read from `req.json()` | EDGE-1 |
| `SUPABASE_SERVICE_ROLE_KEY` / `SUPABASE_SECRET_KEYS` in a function | EDGE-2 |
| Function calling OpenAI / Lovable AI gateway / Resend / Twilio / another paid API | EDGE-3 |
| `await req.json()` destructured with no schema parse | EDGE-4 |
| Function named or handling `webhook` / `stripe` / `svix` | EDGE-5 |
| `Access-Control-Allow-Origin` reflecting `req.headers.get('origin')`; missing `OPTIONS` branch | EDGE-6 |
| Response body containing `error.message` / upstream text; `fetch(` without `signal`; secret literal in a function | EDGE-7 |
| `queryKey: [` with only string literals while `queryFn` closes over variables | QRY-1 |
| `useMutation(` with no `onSuccess`/`onSettled` invalidation; `onMutate` without `onError` rollback | QRY-3 |
| `useEffect` + `useState` + `supabase.from` in one component; `useState(query.data)` | QRY-4 |
| `useQuery` with an argument that may be `undefined` and no `enabled`; `new QueryClient()` inside a component | QRY-5 |
| `isLoading` branch with no `isError`/`error` branch | QRY-6 |
| `useForm(` without `resolver`; per-field `useState` forms | FORM-1 |
| `type="number"` input with `z.number()` and no coercion; `""` written to nullable columns | FORM-3 |
| Submit button without `disabled={isSubmitting\|isPending}`; mutation error not shown | FORM-4 |
| `register(` inputs outside `FormField`; error `<p>` without `aria-describedby` | FORM-5 |
| `bg-(blue\|gray\|slate\|…)-\d+`, `text-white`, `bg-[#…]` in feature components | UI-1 |
| `` `bg-${`` / `` `text-${`` / `` `border-${`` template-literal classes | UI-2 |
| `className` prop merged by `+` or template literal instead of `cn(` | UI-3 |
| Edits under `src/components/ui/` importing app code; `*-2.tsx` / `Custom*.tsx` forks of primitives | UI-4 |
| `DialogContent` / `SheetContent` / `AlertDialogContent` / `DrawerContent` without a `Title` | UI-5 |
| `<Link>` wrapping `<Button>`; `asChild` with more than one child | UI-6 |
| Both `<Toaster />` and `<Sonner />` mounted; both `useToast` and `toast` from `sonner` imported | UI-7 |
| `strict`/`strictNullChecks`/`noImplicitAny` false; `no-unused-vars` off | LOV-1 |
| `componentTagger()` not gated on development mode; `lovable-tagger` in `dependencies` | LOV-2 |
| More than one lockfile at the root | LOV-3 |
| Hand edits in `git log -p` of `src/integrations/supabase/{client,types}.ts` | LOV-4 |
| Pages/components with no importer; `*New.tsx`/`*2.tsx`/`*Old.tsx`; unused `src/components/ui/*` | LOV-5 |
| Submit handlers that only `console.log`/`toast`; `setTimeout` simulating saves; `mock*`/`sample*`/`dummy*` data rendered; `isAuthenticated = true` | LOV-6 |
| `index.html` title/description/`og:image` still scaffold defaults | LOV-7 |

## Sweep — categories with no signal

None. Every category above has a signal row. If a category is added without one, list it here,
or `make validate-rules` reports it unreachable.
