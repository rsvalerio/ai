# QRY rules

TanStack Query v5 as the server-state layer. Grounded in the TanStack Query docs (Query Keys,
Query Functions, Invalidation, Dependent Queries, Optimistic Updates) and
`@tanstack/eslint-plugin-query`.

## Keys & errors (typical severity: High)

**Detection heuristics** — search for: `queryKey: ['…']` literals with no variables;
`queryFn` bodies that return `data` without checking `error`; `useMutation` without
`onSuccess` / `onSettled`; `useEffect` + `useState` + `supabase.from` in the same component.

- **QRY-1.** A query key includes every value its `queryFn` reads: the user ID, filters, page
  and search term. `['tasks']` for "tasks of the current user with filter X" serves one user's
  or filter's results to another from cache. The same holds **across files**. One literal key
  (`['products']`) used by several components whose `queryFn`s pass different arguments
  (`first: 48` here, `first: 60` there, a different query document) is a single cache entry.
  Whichever component mounts first decides what the others render, and `exhaustive-deps` cannot
  see it. Either share one query-options factory (`productsQuery(first)`) or put the arguments in
  the key. File it once, listing every site. *(Enforced by
  `@tanstack/query/exhaustive-deps` when configured. The scaffold does not install
  `@tanstack/eslint-plugin-query`, so the finding usually also recommends adding it.)* — tanstack.com/query/v5/docs/framework/react/guides/query-keys
- **QRY-2.** A `queryFn` / `mutationFn` **throws** on failure: `if (error) throw error`. Because
  supabase-js does not throw (SUPA-1), a function that returns `data` regardless puts failures
  into the success state with `null` data. Error boundaries, `isError` and retries then
  never fire. — tanstack.com/query/v5/docs/framework/react/guides/query-functions
- **QRY-3.** Every mutation invalidates or updates the queries it changes, in `onSuccess` or
  `onSettled` via `queryClient.invalidateQueries({ queryKey })` or `setQueryData`. Without it,
  the list shows stale data until a refocus refetch. Optimistic updates snapshot the previous
  value in `onMutate` and restore it in `onError`.
  — tanstack.com/query/v5/docs/framework/react/guides/invalidations-from-mutations

## Structure (typical severity: Medium)

- **QRY-4.** Server state lives in the query cache. Do not hand-roll `useEffect` + `useState`
  fetching from Supabase (or Shopify) in an app that already has a `QueryClientProvider`, and do
  not copy `query.data` into `useState` or a Zustand store. All of these reintroduce the races and
  staleness the library removes (see `code-review-web` REACT-7 / REACT-17). Zustand is for client
  state: the cart's local mirror (SHOP-4), UI trays, preferences.
- **QRY-5.** Dependent queries use `enabled: !!userId` rather than running with an `undefined`
  argument and filtering the error away. The `QueryClient` is created once, at module scope or in
  `useState(() => new QueryClient())`, never in a component body.
- **QRY-6.** Components render every state: loading, **error**, empty, and, for a query gated by
  `enabled` (QRY-5), not-yet-enabled. In v5 the old `isLoading` was renamed `isPending`, which
  means "no data yet", and a disabled query stays `isPending` indefinitely. The new `isLoading`
  (`isPending && isFetching`) means "first fetch in flight". So branch on `isPending` for an
  always-enabled query. For a gated query, show the spinner on `isLoading` and handle the disabled
  case (`isPending && fetchStatus === 'idle'`, or the gating condition itself) separately.
  Spinning on `isPending` there never ends. A screen that branches only on the loading flag shows
  a blank or "no items" view on failure, which hides the bug that SUPA-1 / QRY-2 just surfaced.
  — tanstack.com/query/v5/docs/framework/react/guides/disabling-queries

## Persisted client state (typical severity: Medium)

**Detection heuristics** — search for: `persist(` from `zustand/middleware`; `name:` storage keys;
`partialize`; persisted objects with no `version`.

- **QRY-7.** Zustand `persist` stores are a schema stored in every visitor's browser, so treat
  them as one. A store whose state shape has changed since release declares `version` and a
  `migrate` function, or a returning visitor's old state is merged into the new shape and breaks
  it. That shows up as missing fields, a renamed key read as `undefined`, or a cart line from the
  old format. `partialize` persists only what must survive a reload, never functions, derived
  values or server data the next fetch will replace (QRY-4). A store that holds per-user data is
  cleared on sign-out (AUTH-4). Reading a persisted store during render before rehydration
  finishes shows the default state for a frame. Where that matters (a cart badge count, a gated
  redirect), wait on `persist.hasHydrated()` / `onFinishHydration`.
  — zustand.docs.pmnd.rs/integrations/persisting-store-data
