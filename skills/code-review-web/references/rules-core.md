# Core Web Rules — React, TypeScript, Async, Performance, Accessibility

Rules are grounded in the official React docs (react.dev), the React 19 / 19.2 release posts, the React Compiler v1.0 docs (stable Oct 2025), `eslint-plugin-react-hooks` v7, the TypeScript handbook, `typescript-eslint`, and MDN. Where a rule is fully enforced by configured tooling, file only for the unenforced nuance (see [rules.md](rules.md)).

## React — Hooks & Effects (typical severity: High)

- **REACT-1.** Call hooks only at the top level of a component or custom hook — never in conditions, loops, nested functions, or after an early return. The order of hook calls must be stable across renders. *(Enforced by `react-hooks/rules-of-hooks`; file only when the lint is disabled or absent.)* — react.dev/reference/rules/rules-of-hooks
- **REACT-2.** Hooks are callable only from React function components and other hooks, not plain functions. — react.dev/reference/rules/rules-of-hooks
- **REACT-3.** Keep render pure: no side effects, mutation of props/state, subscriptions, or I/O during render. Side effects belong in event handlers or Effects. — react.dev/learn/keeping-components-pure
- **REACT-4.** Do not silence `react-hooks/exhaustive-deps`. A missing dependency is a stale-closure bug. The correct fixes, in order: (1) move the value into the Effect, (2) wrap a stable callback, (3) extract non-reactive logic into `useEffectEvent` (React 19.2), (4) restructure so the value isn't needed. Disabling the lint with a comment is itself a finding unless the comment proves the dependency is intentionally frozen. — react.dev/learn/removing-effect-dependencies, react.dev/reference/react/useEffectEvent
- **REACT-5.** Do not use an Effect to compute derived state. If a value can be calculated from existing props/state, compute it during render (optionally `useMemo`) — an Effect that calls `setState` from other state causes an extra render pass and desync. — react.dev/learn/you-might-not-need-an-effect
- **REACT-6.** Do not put event-specific logic in an Effect. Logic that should run in response to a user action (POST on submit, showing a toast on click) belongs in the event handler, not an Effect keyed on a state change. — react.dev/learn/you-might-not-need-an-effect
- **REACT-7.** Every Effect that subscribes, opens a connection, starts a timer, or fetches must return a cleanup function. Fetch-in-Effect must guard against races (ignore-stale-result flag or `AbortController`) so a slower earlier request can't overwrite a newer one. Prefer a data library or framework loader over hand-rolled fetch Effects. — react.dev/reference/react/useEffect#fetching-data-with-effects
  **Scanning guidance:** an Effect with no subscription/timer/listener/fetch needs no cleanup — only flag Effects that acquire something. A fetch Effect that already sets a `cancelled`/`ignore` flag or passes `signal` is compliant; do not file.
- **REACT-8.** Custom hooks must be named `use*`, be pure in the same sense as components, and exist to share *stateful logic*, not state itself (each call gets independent state). Extract a custom hook when the same effect/state choreography repeats. — react.dev/learn/reusing-logic-with-custom-hooks
- **REACT-9.** `useRef` is for values that persist across renders without triggering re-render (DOM nodes, timer IDs, mutable instances). Do not read/write `ref.current` during render, and do not use a ref where state is needed (changes won't re-render). — react.dev/reference/react/useRef

## React — Memoization & Compiler (typical severity: Low--Medium)

- **REACT-10.** With **React Compiler v1.0** (stable, Oct 2025) enabled, drop reflexive `useMemo`/`useCallback`/`React.memo` in new code — the compiler memoizes automatically for components that obey the Rules of React. Keep manual memoization only where it still matters: a value used as a **dependency of another hook/Effect**, or one crossing a **strict-equality boundary** (a third-party `memo`'d child, a context value — see PERF-2). When migrating existing code, leave memoization in place until verified. — react.dev/learn/react-compiler, react.dev/reference/react-compiler
  **Scanning guidance:** only flag *new* reflexive memoization when the Compiler is enabled in the project's build/ESLint config. If the Compiler is not enabled, manual memoization is still the correct tool — do not file REACT-10; evaluate under PERF-1/PERF-2 instead.
- **REACT-11.** The Compiler only optimizes code that follows the Rules of React (pure render, no prop/state mutation). Code that breaks those rules is silently skipped by the Compiler and is a latent bug — fix the impurity (REACT-3) rather than relying on memoization to paper over it. — react.dev/reference/react-compiler

## React — Components, Keys & State (typical severity: Medium--High)

- **REACT-12.** Give list items a stable, unique `key` derived from data identity (an ID), never the array index for lists that can reorder, insert, or delete — index keys cause state to attach to the wrong row and subtle render bugs. A `key` is acceptable as the array index only for static, append-only lists. — react.dev/learn/rendering-lists#keeping-list-items-in-order-with-key
- **REACT-13.** In React 19, pass `ref` as a normal prop to function components; `forwardRef` is deprecated. New components should not introduce `forwardRef`. — react.dev/blog (React 19), react.dev/reference/react/forwardRef
- **REACT-14.** In React 19, render the context object directly as a provider: `<MyContext value={...}>` instead of `<MyContext.Provider value={...}>`. — react.dev/blog (React 19)
- **REACT-15.** Controlled inputs must pair `value`/`checked` with an `onChange` handler; an input with `value` and no handler is read-only and a bug. Don't switch an input between controlled and uncontrolled across renders (no `value={x ?? undefined}` flip-flop). — react.dev/reference/react-dom/components/input
- **REACT-16.** Colocate state with the component that uses it; lift state only to the closest common ancestor that actually needs it. Avoid hoisting everything to a top-level "god" component or global store when local state suffices. — react.dev/learn/sharing-state-between-components
- **REACT-17.** Prefer deriving rendered output from a single source of truth over mirroring props into state (`useState(props.x)`); copied props go stale. If you must seed state from a prop, treat it as initial-only and document it. — react.dev/learn/choosing-the-state-structure

## React — React 19 Forms, Actions & `use()` (typical severity: Medium)

- **REACT-18.** Prefer React 19 Actions (`<form action={fn}>`, `useActionState`, `useFormStatus`, `useOptimistic`) over hand-rolled `isLoading`/`error`/pending plumbing for form submission and async transitions — they handle pending state, errors, and optimistic UI consistently. — react.dev/blog (React 19), react.dev/reference/react/useActionState
- **REACT-19.** `use()` reads a resource (promise or context) during render but **does not support a promise created inline in render** — the promise must be cached/stable (from a Suspense-enabled data source or hoisted), or it re-fires every render. `use()` may be called conditionally, unlike other hooks. Suspense does not catch data fetched in a `useEffect`. — react.dev/reference/react/use
- **REACT-20.** React 19 supports rendering `<title>`, `<meta>`, and `<link>` from any component (hoisted to `<head>`); prefer this over manual `document.title` mutation in an Effect for document metadata. — react.dev/blog (React 19)

## TypeScript — Type Safety (typical severity: Medium--High)

- **TS-1.** Avoid `any`; use `unknown` for values of unknown shape and narrow before use. Every `any` is a hole that disables checking transitively. *(Enforced by `@typescript-eslint/no-explicit-any` when configured.)*
  **Scanning guidance:** exclude `.d.ts` shims, generated types, and test mocks. A single documented `any` at a typed third-party boundary with a narrowing guard immediately after is lower severity than `any` that flows through business logic. — typescript-eslint.io/rules/no-explicit-any
- **TS-2.** Avoid type assertions (`as T`) and especially the double-cast `as unknown as T`; they silence the checker and let invalid values masquerade as valid. Prefer narrowing, type guards, or `satisfies`.
  **Scanning guidance:** a cast with an adjacent comment documenting a missing upstream brand or nominal marker (e.g. `as unknown as readonly RemoteExcalidrawElement[]`) is a justified compile-time-only marker, not a finding (see [classification notes](rules-classification.md)). `as const` is not a type assertion in this sense — never flag it. — typescript-eslint.io/rules/no-unnecessary-type-assertion
- **TS-3.** Avoid the non-null assertion `!`; it asserts non-null without proof and crashes at runtime if wrong. Narrow with a guard, optional chaining, or an early return instead. — typescript-eslint.io/rules/no-non-null-assertion
- **TS-4.** Prefer the `satisfies` operator to validate a value against a type while keeping its narrow inferred type, rather than a widening `: T` annotation that erases literal/narrow information. — typescriptlang.org/docs/handbook/release-notes/typescript-4-9.html
- **TS-5.** Model mutually-exclusive states as a **discriminated union** (`{ status: "loading" } | { status: "error"; error: E } | { status: "success"; data: D }`) instead of several independent boolean/optional flags — invalid combinations (loading *and* error) become unrepresentable. — typescriptlang.org/docs/handbook/2/narrowing.html#discriminated-unions

## TypeScript — Modeling & Strictness (typical severity: Low--Medium)

- **TS-6.** Mark data that should not mutate as `readonly` / `ReadonlyArray<T>` and lock literal config with `as const`; immutability documents intent and prevents accidental mutation (and feeds discriminated-union/literal derivation). — typescriptlang.org/docs/handbook/2/objects.html#readonly-properties
- **TS-7.** Use branded/nominal types (`type UserId = string & { readonly __brand: "UserId" }`) for IDs and validated values so structurally-identical-but-semantically-different values cannot be swapped (room IDs vs scene IDs, raw vs sanitized strings). — community pattern; see effectivetypescript.com
- **TS-8.** Prefer union string literals (or `as const` objects) over `enum` in new code; unions avoid `enum` runtime artifacts and `const enum` cross-module pitfalls. — typescriptlang.org/docs/handbook/enums.html
- **TS-9.** Use `import type` for type-only imports so bundlers/transpilers erase them, avoiding accidental runtime side-effects and easing circular-import issues. *(Enforced by `@typescript-eslint/consistent-type-imports`.)* — typescript-eslint.io/rules/consistent-type-imports
- **TS-10.** Constrain generics with `extends` rather than leaving them open, and return the narrowest accurate type from functions — broad returns push the checking burden onto every caller. — typescriptlang.org/docs/handbook/2/generics.html#generic-constraints
- **TS-11.** Add a `default` branch that assigns the value to `never` when switching over a discriminated union (`const _exhaustive: never = x;`) so adding a variant later becomes a compile error instead of a silent fall-through. — typescriptlang.org/docs/handbook/2/narrowing.html#exhaustiveness-checking
- **TS-12.** Enable strict typing in `tsconfig`: `"strict": true` at minimum, and prefer also enabling `noUncheckedIndexedAccess` (array/index access returns `T | undefined`) and `exactOptionalPropertyTypes` (distinguishes missing key from `undefined`) — both are *outside* the `strict` preset and catch real bugs. Flag a `tsconfig` missing `strict`. — typescriptlang.org/tsconfig#strict

## Async & Error Handling (typical severity: High)

- **ASYNC-1.** No floating promises — every promise in statement position must be awaited, `.catch()`-ed, or explicitly `void`-ed; a dropped promise swallows rejections silently. *(Enforced by `@typescript-eslint/no-floating-promises`.)* — typescript-eslint.io/rules/no-floating-promises
- **ASYNC-2.** Do not misuse promises where a non-promise is expected — a promise in an `if`/`&&`/ternary condition is always truthy, and an async function passed where a `void` callback is expected has its rejection ignored. *(Enforced by `@typescript-eslint/no-misused-promises`.)* — typescript-eslint.io/rules/no-misused-promises
- **ASYNC-3.** Guard async state updates against races and unmount: when an `await` resolves, verify the result is still the latest request (sequence/abort/`cancelled` flag) before calling `setState`; out-of-order responses otherwise clobber newer data, and setting state after unmount leaks. — react.dev/reference/react/useEffect#fetching-data-with-effects
- **ASYNC-4.** Check `response.ok` (or status) after every `fetch` — `fetch` does **not** reject on HTTP 4xx/5xx, so unchecked code treats an error body as success data. — developer.mozilla.org/en-US/docs/Web/API/Window/fetch
- **ASYNC-5.** Attach a timeout/cancellation (`AbortController`, `AbortSignal.timeout()`) to network requests; an unbounded request hangs the UI and leaks when the component unmounts. — developer.mozilla.org/en-US/docs/Web/API/AbortController
- **ASYNC-6.** Wrap subtrees that can throw during render (lazy components, `use()` of a rejected promise, third-party widgets) in an error boundary so one failure doesn't blank the whole app; pair with a user-visible fallback. — react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary
- **ASYNC-7.** Render explicit loading and error states for every async operation; don't leave the UI blank or stuck on the previous value while a request is in flight or after it fails.
  **Scanning guidance:** `void someAsyncFn()` is acceptable for *deliberate* fire-and-forget (e.g. best-effort telemetry, an explicitly non-awaited broadcast) — only flag `void` that drops an error the user needs to know about.

## Performance (typical severity: Low--Medium)

- **PERF-1.** Avoid needless re-renders: hoist expensive computation out of the render path or `useMemo` it; don't recreate large objects/handlers passed to memoized children every render (or rely on the React Compiler — see REACT-10). — react.dev/reference/react/useMemo
- **PERF-2.** Keep context provider `value` referentially stable — pass a memoized object/array, not a fresh literal each render — or every consumer re-renders on every provider render. This is a strict-equality boundary the Compiler does not fully remove. — react.dev/reference/react/useContext, react.dev/reference/react/createContext
- **PERF-3.** Don't run expensive work (sorting/filtering large arrays, parsing, crypto) directly in the render body on every render — memoize keyed on its inputs or move it to an event/Effect. — react.dev/reference/react/useMemo
- **PERF-4.** Virtualize long lists (windowing) rather than rendering thousands of DOM nodes; large unvirtualized lists tank scroll performance and memory. — react.dev/learn/render-and-commit (perf guidance)
- **PERF-5.** Code-split heavy or route-level components with `React.lazy()` + dynamic `import()` and a `<Suspense>` fallback so the initial bundle stays small; Vite splits dynamic imports into separate chunks automatically. — react.dev/reference/react/lazy, vite.dev/guide/features#dynamic-import

## Accessibility (typical severity: Medium)

- **A11Y-1.** Use semantic elements (`<button>`, `<a>`, `<nav>`, `<label>`) over `<div>`/`<span>` with click handlers; a clickable `<div>` is not focusable or keyboard-operable by default. If a non-semantic element must be interactive, add `role`, `tabIndex`, and keyboard handlers. — developer.mozilla.org/en-US/docs/Web/Accessibility, react.dev/reference/react-dom/components/common
- **A11Y-2.** Provide text alternatives and labels: `alt` on `<img>` (empty `alt=""` for decorative), an associated `<label>` or `aria-label` for every form control, and accessible names for icon-only buttons. — developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA
- **A11Y-3.** Pair pointer interactions with keyboard support: an element with `onClick` that isn't a native button/link needs `onKeyDown` (Enter/Space) and focus management; modals need focus trapping and an Escape handler. — developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA
- **A11Y-4.** Use ARIA only to fill gaps native HTML can't, and use it correctly — invalid/contradictory ARIA is worse than none. Prefer a native element over `role` reinvention. — developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA
