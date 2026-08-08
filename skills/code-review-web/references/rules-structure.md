# Structure and Readability Rules — FN, READ, ARCH, API

> Thresholds below are industry-common defaults (Clean Code, cognitive-complexity research, Airbnb/typescript-eslint conventions). Adjust per project — the goal is flagging outliers for review, not rigid enforcement.

## Functions & Structure (typical severity: Medium--High)

- **FN-1.** Functions/components ≤50 lines of logic, operating at a single abstraction level — extract low-level details (data shaping, DOM math, formatting) into named helpers or hooks rather than mixing orchestration with detail. Exceptions: large but flat JSX returns, exhaustive `switch` arms.
- **FN-2.** Nesting ≤4 levels; use early returns/guard clauses. Flatten conditional pyramids with `if (!precondition) return null;`, optional chaining, and extracted predicates instead of deep `if`/ternary nesting. Avoid deeply nested ternaries in JSX — extract to a variable or helper component.
- **FN-3.** Parameters ≤5; group related arguments into a props/options object. React components should take a single typed `props` object, not many positional args.
- **FN-4.** Extract complex boolean expressions (>3 conditions) into named predicates: `isReady`, `hasPermission`, `shouldRetry`, `canEdit`. Improves readability and testability.
- **FN-5.** Keep cyclomatic complexity ≤10 (McCabe). High-branch render logic is a smell — extract sub-components or a reducer. Exhaustive discriminated-union `switch` may exceed the threshold legitimately; judge by cognitive load, not the raw number.
- **FN-6.** Components should do one thing. A component that fetches data, holds form state, computes derived values, *and* renders a complex tree is doing too much — split presentational and container concerns or extract custom hooks.

## Readability (typical severity: Low--Medium)

- **READ-1.** Prefer clarity over cleverness: explicit > implicit, familiar React/TS patterns > obscure type-level gymnastics, readability > brevity.
- **READ-2.** Break dense expressions into named intermediate variables; name the steps of long array-method chains (`const visible = items.filter(...).map(...)`) or use an explicit loop when a chain exceeds ~3--4 operations or mixes control flow with transformation.
- **READ-3.** Use descriptive, consistent names. Components `PascalCase`; hooks `useCamelCase`; event handlers `handleX`/`onX`; booleans `is/has/should/can`. Avoid abbreviations and single-letter names outside trivial scopes.
- **READ-4.** No magic numbers or magic strings — extract to named constants (`const CURSOR_THROTTLE_MS = 33;`), especially for timing, sizes, status codes, storage keys, and protocol event names. Repeated string literals used as keys/discriminants should be a `const`/union.
- **READ-5.** Remove dead code: unused imports, variables, params, components, commented-out blocks, and unreachable branches. *(Partly enforced by `noUnusedLocals`/`noUnusedParameters` and ESLint.)*
- **READ-6.** Document "why", not "what". Comment non-obvious decisions (why a throttle interval, why a cast is safe, why an Effect dependency is intentionally omitted) — not restatements of the code.
- **READ-7.** Use consistent patterns for similar problems across the codebase (one fetch/error pattern, one way to read config, one toast/notification path).
- **READ-8.** No `console.log`/`console.debug`/`console.info` in production (non-test) code — leftover logs leak data and clutter the console. Use a real logger or remove them. `console.error`/`console.warn` in genuine error paths are acceptable but should not include secrets/PII (see SEC-13).
  **Scanning guidance:** exclude test files, dev-only debug utilities gated behind `import.meta.env.DEV`, and config/build scripts before counting.

## Architecture & Modules (typical severity: Medium)

- **ARCH-1.** No god components or god modules. Red flags: a component file >250--300 lines, a module mixing unrelated concerns, a component with >10 distinct responsibilities or pieces of state. Split by responsibility (e.g. `LibraryPanel` → sidebar / item list / auth flow).
- **ARCH-2.** Separate concerns: keep data fetching (API clients), business logic (pure functions / hooks), and presentation (components) distinct. A component should call a typed API module or hook, not inline raw `fetch` + URL building + response parsing.
- **ARCH-3.** Organize by feature/domain (`library/`, `collab/`, `share`), not by technical layer (`components/`, `services/`, `hooks/` split across a feature). Co-locate a feature's component, hook, types, and tests.
- **ARCH-4.** Put genuinely shared utilities in a clearly named module (`crypto.ts`, `config.ts`), not a grab-bag `utils.ts`. Keep cross-module dependencies explicit and one-directional.
- **ARCH-5.** No circular dependencies between modules; high cohesion within a module. Circular imports cause initialization-order bugs and break tree-shaking. *(Detectable with `eslint-plugin-import` `no-cycle` or `madge`.)*
- **ARCH-6.** Match abstraction to complexity (YAGNI) — don't introduce a context, generic wrapper, or abstraction layer before there are multiple real consumers.
- **ARCH-7.** Be deliberate with barrel files (`index.ts` re-exports): they ease imports but can create cycles and defeat tree-shaking when overused. Don't add a barrel that re-exports an entire feature's internals.
- **ARCH-8.** Keep `tsconfig` project references and `include`/`exclude` honest — app code, node/config code, and tests should resolve to the right config; don't let test or config files leak into the app build graph.

## Component API Design (typical severity: Medium)

- **API-1.** Design narrow, well-typed component props: required vs optional explicit, no `any`/`object` prop types, discriminated-union props for variant components instead of many optional flags (mirrors TS-5).
- **API-2.** Avoid deep prop drilling (passing a prop through 3+ intermediate components that don't use it) — lift to context or compose with `children`/render props. But don't reach for context when one level of passing suffices (ARCH-6).
- **API-3.** Prefer composition (`children`, slots) over boolean-prop explosions (`showHeader`, `showFooter`, `compact`, `bordered`…). Components that accumulate many boolean toggles should be decomposed.
- **API-4.** Keep prop and callback names predictable and consistent (`onChange`, `onSelect`, `value`, `disabled`); match the conventions of the underlying DOM/library elements the component wraps.
- **API-5.** Type imperative handles and external APIs precisely (e.g. an Excalidraw `ExcalidrawImperativeAPI` stored in a ref/state) rather than `any`; surface only the methods callers need.

## Cognitive Load

- **CL-1.** Default to reducing cognitive load, especially in high-churn application code and mixed-experience teams. Accept higher structural complexity (extra variables, early returns, small components) to lower cognitive load. Reserve terse, idiomatic density for stable, expert-facing utility code.

### Refactoring Patterns

When flagging complexity or readability, suggest concrete refactoring:

- **Deep nesting** → early returns + guard clauses + extract sub-components; flatten nested ternaries in JSX into variables or small components.
- **Complex boolean logic** → named predicates: `const canShare = isSignedIn && !isBusy && hasScene;`
- **Long parameter lists** → a single typed options/props object.
- **God component** → split presentational vs container; extract custom hooks for stateful logic; extract repeated JSX into child components.
- **Inline fetch in component** → move to a typed API module + a data hook (see ARCH-2, DUP-3).
- **Mixed concerns** → separate data, logic, and presentation layers.
