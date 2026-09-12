# Web Scan Checklist

Observable signal → rules to check. Grep for the signal; when it hits, go straight to the
full rule in `rules/<CATEGORY>.md` and confirm there before filing. The rule IDs below are
the lookup — `rules/index.md` is not a scan step. A signal with no hits costs nothing
further.

| Signal | Rules to check |
|--------|----------------|
| `useEffect` doing data fetching without cleanup / abort | REACT-7, ASYNC-3 |
| `useEffect` computing derived state, or doing work that belongs in an event handler | REACT-5, REACT-6 |
| `// eslint-disable*next*line react-hooks/exhaustive-deps` | REACT-4 |
| Reflexive `useMemo`/`useCallback`/`memo` (React Compiler era) *(see REACT-10 scanning guidance)* | REACT-10 |
| Array index as `key` in a reorderable/editable list | REACT-12 |
| `forwardRef` in new code; `<Context.Provider>` instead of `<Context value>` | REACT-13, REACT-14 |
| `any` / `as unknown as` double-cast / non-null `!` in non-test code *(exclude `.d.ts`, mocks, documented brand casts — see TS-1/TS-2 scanning guidance)* | TS-1, TS-2, TS-3 |
| Boolean/optional flag soup for mutually-exclusive states | TS-5 |
| Type-only imports without `import type` | TS-9 |
| `switch` over a union without a `never` exhaustiveness default | TS-11 |
| Floating promise; promise passed to `if`/`&&`/void callback | ASYNC-1, ASYNC-2 |
| `fetch` without `response.ok` check, or without timeout/`AbortController` | ASYNC-4, ASYNC-5 |
| Async state set after await with no race/stale guard | ASYNC-3 |
| No error boundary around a subtree that can throw | ASYNC-6 |
| Context provider value rebuilt every render (new object/array/fn) | PERF-2 |
| Expensive compute in render body; missing list virtualization; no route/code splitting | PERF-3, PERF-4, PERF-5 |
| `div`/`span` with `onClick` and no keyboard handling; missing `alt`/label | A11Y-1, A11Y-2, A11Y-3 |
| `dangerouslySetInnerHTML` / `innerHTML` with untrusted data | SEC-1, SEC-2 |
| User-controlled URL in `href`/`src` without scheme allowlist (`javascript:`/`data:`) | SEC-3 |
| AES-GCM IV reuse; `Math.random` for security values; extractable keys; key/plaintext in logs | SEC-5, SEC-6, SEC-7, SEC-8 |
| Hardcoded secret/token in source; secret assumed safe behind `VITE_`; capability token in query string | SEC-10, SEC-11, SEC-12 |
| Unvalidated fetch/WebSocket response shape; sensitive data in `console`/telemetry | SEC-13, SEC-14 |
| Credentials (`credentials: "include"`, cookies, auth headers) sent to a third-party or untrusted origin | SEC-15 |
| Production source maps; unaudited/unpinned dependencies | SEC-16, SEC-17 |
| socket.io inbound message used without validation; authz only at connect; no message/rate bound | RT-1, RT-2, RT-3 |
| Volatile events not throttled; persisted broadcasts not debounced; no echo dedup | RT-4, RT-5 |
| Component file >250 lines; fn >50 lines; nesting >4; params >5 | ARCH-1, FN-1, FN-2, FN-3 |
| `console.log`/`console.debug` left in production code | READ-8 |
| Mixed concerns (fetch + UI + business logic) in one component; circular imports | ARCH-2, ARCH-5 |
| Duplicated JSX/logic/fetch/type blocks (3+) | DUP-1, DUP-2, DUP-3, DUP-4, DUP-6, DUP-8 |
| Test without assertion; `getByTestId` where a role query fits; `fireEvent` over `userEvent` | TEST-1, TEST-3, TEST-4 |
| Security-critical unit (crypto, parsing, auth) with no test | TEST-5, TEST-6 |
