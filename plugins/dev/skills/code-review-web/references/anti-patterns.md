# Cross-Cutting Anti-Patterns

Common React + TypeScript anti-patterns that span multiple rule categories. Use these as scan signals during review.

## React State & Effects

- **Derived state in state**: mirroring props/other state into `useState` then syncing with an Effect — goes stale and adds render passes. Fix: compute during render (REACT-5, REACT-17).
- **Effect for event logic**: doing on-submit/on-click work inside an Effect keyed on a state change instead of in the handler. Fix: move it to the event handler (REACT-6).
- **Disabling exhaustive-deps**: silencing the lint to hide a stale closure. Fix: move the value in, wrap a stable callback, or use `useEffectEvent` (REACT-4).
- **Missing cleanup**: subscriptions/timers/sockets/listeners opened in an Effect with no cleanup → leaks and double-fires. Fix: return a cleanup function (REACT-7).
- **Fetch race in Effect**: a slower earlier request overwrites a newer one. Fix: ignore-stale flag or `AbortController` (REACT-7, ASYNC-3).
- **setState in render**: calling a setter during render → infinite loop or impurity. Fix: move to an event/Effect (REACT-3).
- **Index as key**: array index `key` on a reorderable/editable list → state attaches to the wrong row. Fix: stable ID key (REACT-12).

## Type Safety

- **`any` escape hatch**: `any` (or `as any`) to silence the checker — disables checking transitively. Fix: `unknown` + narrowing (TS-1).
- **Double-cast**: `as unknown as T` to force an invalid value. Fix: validate/narrow, or document a genuine brand cast (TS-2).
- **Boolean flag soup**: `isLoading`/`isError`/`isSuccess` independent booleans allowing impossible combinations. Fix: discriminated union (TS-5).
- **Stringly-typed**: bare `string` for values with a known variant set (event names, statuses). Fix: union literals / `as const` (TS-8).

## Async & Error Handling

- **Floating promise**: an un-awaited async call dropping its rejection. Fix: await, `.catch`, or deliberate `void` (ASYNC-1).
- **Unchecked fetch**: using a response without checking `response.ok` — error bodies treated as data. Fix: check status (ASYNC-4).
- **No abort/timeout**: unbounded fetch hanging the UI and leaking on unmount. Fix: `AbortController` (ASYNC-5).
- **Swallowed error**: `catch {}` discarding the error with no user feedback or log. Fix: surface an error state, log without secrets (ASYNC-7).

## Performance

- **Unstable context value**: a fresh object/array as `<Context value>` each render → all consumers re-render. Fix: memoize the value (PERF-2).
- **Expensive work in render**: sorting/parsing/crypto on every render. Fix: memoize or move out (PERF-3).

## Security

- **Unsanitized HTML**: `dangerouslySetInnerHTML` with untrusted data. Fix: avoid, or sanitize with DOMPurify (SEC-1).
- **IV reuse / `Math.random` crypto**: reused AES-GCM IV or non-CSPRNG randomness for security values. Fix: fresh `crypto.getRandomValues` IV per encryption (SEC-5, SEC-6).
- **Secret in bundle**: hardcoded token, or a real secret behind a `VITE_` var (which is public). Fix: backend proxy; secrets never reach the client (SEC-10, SEC-11).
- **Trusting the wire**: applying fetch/WebSocket payloads without validation. Fix: schema-validate at the boundary (SEC-13, RT-1).

## Structure

- **God component**: one component fetching + holding form state + computing + rendering a large tree. Fix: split, extract hooks (ARCH-1, FN-6).
- **Inline fetch in component**: raw `fetch` + URL building + parsing inside JSX components, duplicated across call sites. Fix: typed API module (ARCH-2, DUP-3).
- **Leftover `console.log`**: debug logging shipped to production. Fix: remove or gate behind `import.meta.env.DEV` (READ-8).
