# Web rule index

One line per rule — enough to decide whether a rule is in play. Before filing a finding,
read that rule's full text (rationale, examples, scanning guidance, exceptions) in the
category file linked from its heading. Never file a finding from the index line alone.

## REACT — REACT · [rules/REACT.md](REACT.md) (7 KB)

### React — Hooks & Effects (typical severity: High)

- **REACT-1** Call hooks only at the top level of a component or custom hook — never in conditions, loops, nested functions, or after an early return.
- **REACT-2** Hooks are callable only from React function components and other hooks, not plain functions.
- **REACT-3** Keep render pure: no side effects, mutation of props/state, subscriptions, or I/O during render.
- **REACT-4** Do not silence `react-hooks/exhaustive-deps`.
- **REACT-5** Do not use an Effect to compute derived state.
- **REACT-6** Do not put event-specific logic in an Effect.
- **REACT-7** Every Effect that subscribes, opens a connection, starts a timer, or fetches must return a cleanup function.
- **REACT-8** Custom hooks must be named `use*`, be pure in the same sense as components, and exist to share *stateful logic*, not state itself (each call gets independent state).
- **REACT-9** `useRef` is for values that persist across renders without triggering re-render (DOM nodes, timer IDs, mutable instances).

### React — Memoization & Compiler (typical severity: Low--Medium)

- **REACT-10** With **React Compiler v1.0** (stable, Oct 2025) enabled, drop reflexive `useMemo`/`useCallback`/`React.memo` in new code …
- **REACT-11** The Compiler only optimizes code that follows the Rules of React (pure render, no prop/state mutation).

### React — Components, Keys & State (typical severity: Medium--High)

- **REACT-12** Give list items a stable, unique `key` derived from data identity (an ID), never the array index for lists that can reorder, insert, or delete …
- **REACT-13** In React 19, pass `ref` as a normal prop to function components; `forwardRef` is deprecated.
- **REACT-14** In React 19, render the context object directly as a provider: `<MyContext value={...}>` instead of `<MyContext.Provider value={...}>`.
- **REACT-15** Controlled inputs must pair `value`/`checked` with an `onChange` handler; an input with `value` and no handler is read-only and a bug.
- **REACT-16** Colocate state with the component that uses it; lift state only to the closest common ancestor that actually needs it.
- **REACT-17** Prefer deriving rendered output from a single source of truth over mirroring props into state (`useState(props.x)`); copied props go stale.

### React — React 19 Forms, Actions & `use()` (typical severity: Medium)

- **REACT-18** Prefer React 19 Actions (`<form action={fn}>`, `useActionState`, `useFormStatus`, `useOptimistic`) over hand-rolled `isLoading`/`error`/pending plumbing for form submission and async transitions …
- **REACT-19** `use()` reads a resource (promise or context) during render but **does not support a promise created inline in render** — the promise must be cached/stable …
- **REACT-20** React 19 supports rendering `<title>`, `<meta>`, and `<link>` from any component (hoisted to `<head>`); prefer this over manual `document.title` mutation in an Effect for document metadata.

## TS — TS · [rules/TS.md](TS.md) (4 KB)

### TypeScript — Type Safety (typical severity: Medium--High)

- **TS-1** Avoid `any`; use `unknown` for values of unknown shape and narrow before use.
- **TS-2** Avoid type assertions (`as T`) and especially the double-cast `as unknown as T`; they silence the checker and let invalid values masquerade as valid.
- **TS-3** Avoid the non-null assertion `!`; it asserts non-null without proof and crashes at runtime if wrong.
- **TS-4** Prefer the `satisfies` operator to validate a value against a type while keeping its narrow inferred type, rather than a widening `: T` annotation that erases literal/narrow information.
- **TS-5** Model mutually-exclusive states as a **discriminated union** (`{ status: "loading" } | { status: "error"; error: E } | { status: "success" …`

### TypeScript — Modeling & Strictness (typical severity: Low--Medium)

- **TS-6** Mark data that should not mutate as `readonly` / `ReadonlyArray<T>` and lock literal config with `as const`; immutability documents intent and prevents accidental mutation …
- **TS-7** Use branded/nominal types (`type UserId = string & { readonly __brand: "UserId" }`) for IDs and validated values so structurally-identical-but-semantically-different values cannot be swapped …
- **TS-8** Prefer union string literals (or `as const` objects) over `enum` in new code; unions avoid `enum` runtime artifacts and `const enum` cross-module pitfalls.
- **TS-9** Use `import type` for type-only imports so bundlers/transpilers erase them, avoiding accidental runtime side-effects and easing circular-import issues.
- **TS-10** Constrain generics with `extends` rather than leaving them open, and return the narrowest accurate type from functions — broad returns push the checking burden onto every caller.
- **TS-11** Add a `default` branch that assigns the value to `never` when switching over a discriminated union …
- **TS-12** Enable strict typing in `tsconfig`: `"strict": true` at minimum, and prefer also enabling `noUncheckedIndexedAccess` (array/index access returns `T | undefined`) and `exactOptionalPropertyTypes` …

## ASYNC — Async & Error Handling (typical severity: High) · [rules/ASYNC.md](ASYNC.md) (3 KB)

- **ASYNC-1** No floating promises — every promise in statement position must be awaited, `.catch()`-ed, or explicitly `void`-ed; a dropped promise swallows rejections silently.
- **ASYNC-2** Do not misuse promises where a non-promise is expected — a promise in an `if`/`&&`/ternary condition is always truthy …
- **ASYNC-3** Guard async state updates against races and unmount: when an `await` resolves, verify the result is still the latest request (sequence/abort/`cancelled` flag) before calling `setState` …
- **ASYNC-4** Check `response.ok` (or status) after every `fetch` — `fetch` does **not** reject on HTTP 4xx/5xx, so unchecked code treats an error body as success data.
- **ASYNC-5** Attach a timeout/cancellation (`AbortController`, `AbortSignal.timeout()`) to network requests; an unbounded request hangs the UI and leaks when the component unmounts.
- **ASYNC-6** Wrap subtrees that can throw during render (lazy components, `use()` of a rejected promise, third-party widgets) in an error boundary so one failure doesn't blank the whole app …
- **ASYNC-7** Render explicit loading and error states for every async operation; don't leave the UI blank or stuck on the previous value while a request is in flight or after it fails.

## PERF — Performance (typical severity: Low--Medium) · [rules/PERF.md](PERF.md) (2 KB)

- **PERF-1** Avoid needless re-renders: hoist expensive computation out of the render path or `useMemo` it; don't recreate large objects/handlers passed to memoized children every render …
- **PERF-2** Keep context provider `value` referentially stable — pass a memoized object/array, not a fresh literal each render — or every consumer re-renders on every provider render.
- **PERF-3** Don't run expensive work (sorting/filtering large arrays, parsing, crypto) directly in the render body on every render — memoize keyed on its inputs or move it to an event/Effect.
- **PERF-4** Virtualize long lists (windowing) rather than rendering thousands of DOM nodes; large unvirtualized lists tank scroll performance and memory.
- **PERF-5** Code-split heavy or route-level components with `React.lazy()` + dynamic `import()` and a `<Suspense>` fallback so the initial bundle stays small …

## A11Y — Accessibility (typical severity: Medium) · [rules/A11Y.md](A11Y.md) (2 KB)

- **A11Y-1** Use semantic elements (`<button>`, `<a>`, `<nav>`, `<label>`) over `<div>`/`<span>` with click handlers; a clickable `<div>` is not focusable or keyboard-operable by default.
- **A11Y-2** Provide text alternatives and labels: `alt` on `<img>` (empty `alt=""` for decorative), an associated `<label>` or `aria-label` for every form control, and accessible names for icon-only buttons.
- **A11Y-3** Pair pointer interactions with keyboard support: an element with `onClick` that isn't a native button/link needs `onKeyDown` (Enter/Space) and focus management …
- **A11Y-4** Use ARIA only to fill gaps native HTML can't, and use it correctly — invalid/contradictory ARIA is worse than none.

## FN — Functions & Structure (typical severity: Medium--High) · [rules/FN.md](FN.md) (2 KB)

- **FN-1** Functions/components ≤50 lines of logic, operating at a single abstraction level — extract low-level details …
- **FN-2** Nesting ≤4 levels; use early returns/guard clauses.
- **FN-3** Parameters ≤5; group related arguments into a props/options object.
- **FN-4** Extract complex boolean expressions (>3 conditions) into named predicates: `isReady`, `hasPermission`, `shouldRetry`, `canEdit`.
- **FN-5** Keep cyclomatic complexity ≤10 (McCabe).
- **FN-6** Components should do one thing.

## READ — Readability (typical severity: Low--Medium) · [rules/READ.md](READ.md) (2 KB)

- **READ-1** Prefer clarity over cleverness: explicit > implicit, familiar React/TS patterns > obscure type-level gymnastics, readability > brevity.
- **READ-2** Break dense expressions into named intermediate variables; name the steps of long array-method chains …
- **READ-3** Use descriptive, consistent names.
- **READ-4** No magic numbers or magic strings — extract to named constants (`const CURSOR_THROTTLE_MS = 33;`), especially for timing, sizes, status codes, storage keys, and protocol event names.
- **READ-5** Remove dead code: unused imports, variables, params, components, commented-out blocks, and unreachable branches.
- **READ-6** Document "why", not "what".
- **READ-7** Use consistent patterns for similar problems across the codebase (one fetch/error pattern, one way to read config, one toast/notification path).
- **READ-8** No `console.log`/`console.debug`/`console.info` in production (non-test) code — leftover logs leak data and clutter the console.

## ARCH — Architecture & Modules (typical severity: Medium) · [rules/ARCH.md](ARCH.md) (2 KB)

- **ARCH-1** No god components or god modules.
- **ARCH-2** Separate concerns: keep data fetching (API clients), business logic (pure functions / hooks), and presentation (components) distinct.
- **ARCH-3** Organize by feature/domain (`library/`, `collab/`, `share`), not by technical layer (`components/`, `services/`, `hooks/` split across a feature).
- **ARCH-4** Put genuinely shared utilities in a clearly named module (`crypto.ts`, `config.ts`), not a grab-bag `utils.ts`.
- **ARCH-5** No circular dependencies between modules; high cohesion within a module.
- **ARCH-6** Match abstraction to complexity (YAGNI) — don't introduce a context, generic wrapper, or abstraction layer before there are multiple real consumers.
- **ARCH-7** Be deliberate with barrel files (`index.ts` re-exports): they ease imports but can create cycles and defeat tree-shaking when overused.
- **ARCH-8** Keep `tsconfig` project references and `include`/`exclude` honest — app code, node/config code, and tests should resolve to the right config …

## API — Component API Design (typical severity: Medium) · [rules/API.md](API.md) (1 KB)

- **API-1** Design narrow, well-typed component props: required vs optional explicit, no `any`/`object` prop types, discriminated-union props for variant components instead of many optional flags (mirrors TS-5).
- **API-2** Avoid deep prop drilling (passing a prop through 3+ intermediate components that don't use it) — lift to context or compose with `children`/render props.
- **API-3** Prefer composition (`children`, slots) over boolean-prop explosions (`showHeader`, `showFooter`, `compact`, `bordered`…).
- **API-4** Keep prop and callback names predictable and consistent (`onChange`, `onSelect`, `value`, `disabled`); match the conventions of the underlying DOM/library elements the component wraps.
- **API-5** Type imperative handles and external APIs precisely (e.g. an Excalidraw `ExcalidrawImperativeAPI` stored in a ref/state) rather than `any`; surface only the methods callers need.

## CL — Cognitive Load · [rules/CL.md](CL.md) (1 KB)

- **CL-1** Default to reducing cognitive load, especially in high-churn application code and mixed-experience teams.

## DUP — Code Duplication (typical severity: Medium--High) · [rules/DUP.md](DUP.md) (2 KB)

- **DUP-1** Flag identical or near-identical code blocks of 5+ lines (copy-pasted logic, repeated JSX subtrees).
- **DUP-2** Flag 3+ functions/components with the same structure differing only in literals, field names, or types — candidates for a generic helper, a shared component with props, or a custom hook.
- **DUP-3** Flag copy-pasted network code: repeated `fetch` + URL building + `response.ok` check + JSON parse + error handling across call sites.
- **DUP-4** Flag duplicated type definitions: the same shape declared independently in multiple files (request/response bodies, props).
- **DUP-5** Flag repeated stateful logic across components (the same `useState`/`useEffect` choreography) — extract a custom hook (REACT-8).
- **DUP-6** Extract shared JSX into a reusable component; pass variation as props/children.
- **DUP-7** Extract shared stateful logic into a custom `use*` hook.
- **DUP-8** Extract shared async/network logic into a typed API module; centralize base URL, headers, error mapping, and 401 handling.
- **DUP-9** Context matters: a little duplication is better than a premature or wrong abstraction.
- **DUP-10** Test code has higher duplication tolerance than production code (see TEST-12); prefer clarity over DRY in tests.

## SEC — SEC · [rules/SEC.md](SEC.md) (7 KB)

### Security: XSS & DOM Injection (typical severity: Critical)

- **SEC-1** Do not pass unsanitized data to `dangerouslySetInnerHTML` (React) or `.innerHTML`/`.outerHTML` — it executes attacker script.
- **SEC-2** Prefer safe DOM sinks for untrusted data — render via React children / JSX text or `textContent`, never `innerHTML`/`document.write`/`eval`/`new Function` …
- **SEC-3** Validate user-supplied URLs against an `http(s)` allowlist before using them in `href`/`src`/`window.open`; `javascript:` and untrusted `data:` URLs execute script on interaction.
- **SEC-4** Never build framework templates or markup by string-concatenating untrusted input; bind data through React's escaping so data cannot become code.

### Security: Web Crypto (SubtleCrypto) (typical severity: High--Critical)

- **SEC-5** Generate a fresh, random 96-bit (12-byte) IV for **every** AES-GCM encryption with a given key.
- **SEC-6** Generate IVs, salts, and keys with `crypto.getRandomValues()` or `crypto.subtle.generateKey()`, never `Math.random()` — only the Web Crypto RNG is cryptographically strong.
- **SEC-7** Create `CryptoKey`s with `extractable: false` unless export is genuinely required; an extractable key can be read back out of the object and leaked.
- **SEC-8** Never log, serialize to telemetry, or send to analytics any raw key, IV, or plaintext; logged secrets propagate into aggregation systems and crash reports.
- **SEC-9** Use authenticated encryption (AES-GCM) — do not pair unauthenticated modes without a MAC.

### Security: Secrets in the Frontend (typical severity: Critical)

- **SEC-10** Never hardcode API keys, tokens, or credentials in frontend source — everything shipped to the browser is fully readable in the bundle and devtools.
- **SEC-11** Treat every `VITE_`-prefixed env var as **public** — Vite inlines it into the client bundle at build time.
- **SEC-12** Carry capability/secret tokens in the URL **fragment** (`#…`), which browsers do not send to the server, rather than the query string (which is logged by servers/proxies and sent in `Referer`).

### Security: Network & Data Handling (typical severity: High)

- **SEC-13** Validate and schema-check untrusted responses (fetch, WebSocket, `postMessage`, `localStorage`) before use — never trust the shape of data crossing a boundary …
- **SEC-14** Do not log tokens, PII, or full request/response bodies to the console or telemetry; client logs are user-accessible and frequently shipped to third parties (mirrors SEC-8, READ-8).
- **SEC-15** Send credentials (`credentials: "include"`, cookies, auth headers) only to trusted origins; do not broaden CORS or attach auth to third-party requests.

### Security: Build & Dependencies (typical severity: High)

- **SEC-16** Do not ship readable source maps to production (or restrict their access); `build.sourcemap` true on a public deploy exposes full source and embedded constants.
- **SEC-17** Audit and pin dependencies: run `npm audit`/SCA in CI, commit the lockfile, and review new/transitive packages — a frontend bundle inherits its whole supply chain, a primary attack vector.

## TEST — TEST · [rules/TEST.md](TEST.md) (5 KB)

### Test Structure & Behavior

- **TEST-1** Every test must have a meaningful assertion; no assertion-free tests that only render or call a function.
- **TEST-2** Test behavior, not implementation details.
- **TEST-3** Use the React Testing Library query priority: `getByRole` (with name) > `getByLabelText` > `getByPlaceholderText` > `getByText` > `getByDisplayValue`, and `getByTestId` only as a last resort.
- **TEST-4** Use `@testing-library/user-event` over `fireEvent` for user interactions — `userEvent` simulates real event sequences (focus, keydown, input) that `fireEvent` skips.
- **TEST-5** Cover every security-critical and logic-critical unit with at least one test: crypto round-trips (`decrypt(encrypt(x)) === x`), parsers/validators …
- **TEST-6** Test error and edge paths, not just the happy path: 4xx/5xx responses, empty/zero/max inputs, malformed data, aborted requests, and the loading/error UI states (ASYNC-7).

### Test Async & Determinism

- **TEST-7** For async UI use `findBy*` / `await waitFor(...)` to await appearance; do not wrap interactions in manual `act()` …
- **TEST-8** `waitFor` callbacks must contain a single assertion and **no side effects** (don't fire events or call APIs inside `waitFor`); side effects run repeatedly until timeout and cause flakiness.
- **TEST-9** Make tests deterministic: fake timers (`vi.useFakeTimers()`) for throttle/debounce/`setTimeout` logic, fixed seeds/inputs …
- **TEST-10** Mock network with MSW (Mock Service Worker) at the network boundary rather than monkey-patching `fetch`/modules ad hoc; MSW tests the real request path and survives refactors.

### Test Hygiene

- **TEST-11** Assert specific values, not just truthiness — verify the actual rendered text/value/call arguments, not merely that an element exists or a function "was called".
- **TEST-12** No redundant tests (identical logic with trivial differences).
- **TEST-13** Ensure isolation and cleanup between tests: rely on RTL auto-cleanup, reset module/handler/mocks state …
- **TEST-14** Avoid snapshot overuse — large/auto-updated snapshots assert nothing meaningful and get blindly re-recorded.
- **TEST-15** No skipped/`.skip`/`.todo`/`.only` tests left in the suite without explanation; a bare skip is silent coverage loss, and a stray `.only` disables the rest of the file.

### Test Tooling

- **TEST-16** Track coverage of critical paths (Vitest `--coverage` via v8/istanbul) but treat coverage as a gap-finder, not a quality proof — combine with meaningful assertions (TEST-1, TEST-11).

## RT — RT · [rules/RT.md](RT.md) (3 KB)

### Real-Time: Inbound Message Safety (typical severity: High--Critical)

- **RT-1** Validate every inbound message before use: check the event shape, wrap parsing/decryption in try/catch, and reject malformed payloads instead of applying them.
- **RT-2** Do not treat a live connection as authorization for every operation.
- **RT-3** Bound resource consumption: cap/validate inbound payload size and guard against floods (the server should enforce `maxPayload` and rate limits …

### Real-Time: Traffic Control & Correctness (typical severity: Medium--High)

- **RT-4** Throttle high-frequency *volatile* signals (cursor/pointer position) and debounce *persisted* broadcasts (full scene snapshots) so the socket isn't flooded — e.g. cursor updates throttled to ~30 fps …
- **RT-5** Watermark/deduplicate echoed updates: track the last broadcast version/sequence so the client doesn't re-apply or re-broadcast its own change (feedback loop).
- **RT-6** Manage socket lifecycle deterministically: create the connection on join, remove **all** listeners and disconnect on `stop()`/unmount …

### Real-Time: Encryption & Secrets (typical severity: High)

- **RT-7** Encrypt broadcast payloads end-to-end when the relay is untrusted, with a fresh IV per message (SEC-5) and a CSPRNG-generated room key (SEC-6) …
