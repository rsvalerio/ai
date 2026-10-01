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
  or filter's results to another from cache. *(Enforced by
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
  fetching from Supabase in an app that already has a `QueryClientProvider`, and do not copy
  `query.data` into `useState`. Both reintroduce the races and staleness the library removes
  (see `code-review-web` REACT-7 / REACT-17).
- **QRY-5.** Dependent queries use `enabled: !!userId` rather than running with an `undefined`
  argument and filtering the error away. The `QueryClient` is created once, at module scope or in
  `useState(() => new QueryClient())`, never in a component body.
- **QRY-6.** Components render all three states: pending, **error**, and empty. In v5, branch on
  `isPending` / `status === 'pending'`, not `isLoading`. v5 renamed the old `isLoading` to
  `isPending`, and the new `isLoading` (`isPending && isFetching`) is false for a disabled query. A screen that
  branches only on `isLoading` shows a blank or "no items" view on failure, which hides the bug
  that SUPA-1 / QRY-2 just surfaced.
