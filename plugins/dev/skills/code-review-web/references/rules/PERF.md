# PERF rules

Rules are grounded in the official React docs (react.dev), the React 19 / 19.2 release posts, the React Compiler v1.0 docs (stable Oct 2025), `eslint-plugin-react-hooks` v7, the TypeScript handbook, `typescript-eslint`, and MDN. Where a rule is fully enforced by configured tooling, file only for the unenforced nuance (see [rules.md](../rules.md)).

## Performance (typical severity: Low--Medium)

- **PERF-1.** Avoid needless re-renders: hoist expensive computation out of the render path or `useMemo` it; don't recreate large objects/handlers passed to memoized children every render (or rely on the React Compiler — see REACT-10). — react.dev/reference/react/useMemo
- **PERF-2.** Keep context provider `value` referentially stable — pass a memoized object/array, not a fresh literal each render — or every consumer re-renders on every provider render. This is a strict-equality boundary the Compiler does not fully remove. — react.dev/reference/react/useContext, react.dev/reference/react/createContext
- **PERF-3.** Don't run expensive work (sorting/filtering large arrays, parsing, crypto) directly in the render body on every render — memoize keyed on its inputs or move it to an event/Effect. — react.dev/reference/react/useMemo
- **PERF-4.** Virtualize long lists (windowing) rather than rendering thousands of DOM nodes; large unvirtualized lists tank scroll performance and memory. — react.dev/learn/render-and-commit (perf guidance)
- **PERF-5.** Code-split heavy or route-level components with `React.lazy()` + dynamic `import()` and a `<Suspense>` fallback so the initial bundle stays small; Vite splits dynamic imports into separate chunks automatically. — react.dev/reference/react/lazy, vite.dev/guide/features#dynamic-import
