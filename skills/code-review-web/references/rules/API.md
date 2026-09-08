# API rules

> Thresholds below are industry-common defaults (Clean Code, cognitive-complexity research, Airbnb/typescript-eslint conventions). Adjust per project — the goal is flagging outliers for review, not rigid enforcement.

## Component API Design (typical severity: Medium)

- **API-1.** Design narrow, well-typed component props: required vs optional explicit, no `any`/`object` prop types, discriminated-union props for variant components instead of many optional flags (mirrors TS-5).
- **API-2.** Avoid deep prop drilling (passing a prop through 3+ intermediate components that don't use it) — lift to context or compose with `children`/render props. But don't reach for context when one level of passing suffices (ARCH-6).
- **API-3.** Prefer composition (`children`, slots) over boolean-prop explosions (`showHeader`, `showFooter`, `compact`, `bordered`…). Components that accumulate many boolean toggles should be decomposed.
- **API-4.** Keep prop and callback names predictable and consistent (`onChange`, `onSelect`, `value`, `disabled`); match the conventions of the underlying DOM/library elements the component wraps.
- **API-5.** Type imperative handles and external APIs precisely (e.g. an Excalidraw `ExcalidrawImperativeAPI` stored in a ref/state) rather than `any`; surface only the methods callers need.
