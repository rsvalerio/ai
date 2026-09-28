# ASYNC rules

Rules are grounded in the official React docs (react.dev), the React 19 / 19.2 release posts, the React Compiler v1.0 docs (stable Oct 2025), `eslint-plugin-react-hooks` v7, the TypeScript handbook, `typescript-eslint`, and MDN. Where a rule is fully enforced by configured tooling, file only for the unenforced nuance (see [rules.md](../rules.md)).

## Async & Error Handling (typical severity: High)

- **ASYNC-1.** No floating promises — every promise in statement position must be awaited, `.catch()`-ed, or explicitly `void`-ed; a dropped promise swallows rejections silently. *(Enforced by `@typescript-eslint/no-floating-promises`.)* — typescript-eslint.io/rules/no-floating-promises
- **ASYNC-2.** Do not misuse promises where a non-promise is expected — a promise in an `if`/`&&`/ternary condition is always truthy, and an async function passed where a `void` callback is expected has its rejection ignored. *(Enforced by `@typescript-eslint/no-misused-promises`.)* — typescript-eslint.io/rules/no-misused-promises
- **ASYNC-3.** Guard async state updates against races and unmount: when an `await` resolves, verify the result is still the latest request (sequence/abort/`cancelled` flag) before calling `setState`; out-of-order responses otherwise clobber newer data, and setting state after unmount leaks. — react.dev/reference/react/useEffect#fetching-data-with-effects
- **ASYNC-4.** Check `response.ok` (or status) after every `fetch` — `fetch` does **not** reject on HTTP 4xx/5xx, so unchecked code treats an error body as success data. — developer.mozilla.org/en-US/docs/Web/API/Window/fetch
- **ASYNC-5.** Attach a timeout/cancellation (`AbortController`, `AbortSignal.timeout()`) to network requests; an unbounded request hangs the UI and leaks when the component unmounts. — developer.mozilla.org/en-US/docs/Web/API/AbortController
- **ASYNC-6.** Wrap subtrees that can throw during render (lazy components, `use()` of a rejected promise, third-party widgets) in an error boundary so one failure doesn't blank the whole app; pair with a user-visible fallback. — react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary
- **ASYNC-7.** Render explicit loading and error states for every async operation; don't leave the UI blank or stuck on the previous value while a request is in flight or after it fails.
  **Scanning guidance:** `void someAsyncFn()` is acceptable for *deliberate* fire-and-forget (e.g. best-effort telemetry, an explicitly non-awaited broadcast) — only flag `void` that drops an error the user needs to know about.
