# ARCH rules

> Thresholds below are industry-common defaults (Clean Code, cognitive-complexity research, Airbnb/typescript-eslint conventions). Adjust per project — the goal is flagging outliers for review, not rigid enforcement.

## Architecture & Modules (typical severity: Medium)

- **ARCH-1.** No god components or god modules. Red flags: a component file >250--300 lines, a module mixing unrelated concerns, a component with >10 distinct responsibilities or pieces of state. Split by responsibility (e.g. `LibraryPanel` → sidebar / item list / auth flow).
- **ARCH-2.** Separate concerns: keep data fetching (API clients), business logic (pure functions / hooks), and presentation (components) distinct. A component should call a typed API module or hook, not inline raw `fetch` + URL building + response parsing.
- **ARCH-3.** Organize by feature/domain (`library/`, `collab/`, `share`), not by technical layer (`components/`, `services/`, `hooks/` split across a feature). Co-locate a feature's component, hook, types, and tests.
- **ARCH-4.** Put genuinely shared utilities in a clearly named module (`crypto.ts`, `config.ts`), not a grab-bag `utils.ts`. Keep cross-module dependencies explicit and one-directional.
- **ARCH-5.** No circular dependencies between modules; high cohesion within a module. Circular imports cause initialization-order bugs and break tree-shaking. *(Detectable with `eslint-plugin-import` `no-cycle` or `madge`.)*
- **ARCH-6.** Match abstraction to complexity (YAGNI) — don't introduce a context, generic wrapper, or abstraction layer before there are multiple real consumers.
- **ARCH-7.** Be deliberate with barrel files (`index.ts` re-exports): they ease imports but can create cycles and defeat tree-shaking when overused. Don't add a barrel that re-exports an entire feature's internals.
- **ARCH-8.** Keep `tsconfig` project references and `include`/`exclude` honest — app code, node/config code, and tests should resolve to the right config; don't let test or config files leak into the app build graph.
