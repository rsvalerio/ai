# FN rules

> Thresholds below are industry-common defaults (Clean Code, cognitive-complexity research, Airbnb/typescript-eslint conventions). Adjust per project — the goal is flagging outliers for review, not rigid enforcement.

## Functions & Structure (typical severity: Medium--High)

- **FN-1.** Functions/components ≤50 lines of logic, operating at a single abstraction level — extract low-level details (data shaping, DOM math, formatting) into named helpers or hooks rather than mixing orchestration with detail. Exceptions: large but flat JSX returns, exhaustive `switch` arms.
- **FN-2.** Nesting ≤4 levels; use early returns/guard clauses. Flatten conditional pyramids with `if (!precondition) return null;`, optional chaining, and extracted predicates instead of deep `if`/ternary nesting. Avoid deeply nested ternaries in JSX — extract to a variable or helper component.
- **FN-3.** Parameters ≤5; group related arguments into a props/options object. React components should take a single typed `props` object, not many positional args.
- **FN-4.** Extract complex boolean expressions (>3 conditions) into named predicates: `isReady`, `hasPermission`, `shouldRetry`, `canEdit`. Improves readability and testability.
- **FN-5.** Keep cyclomatic complexity ≤10 (McCabe). High-branch render logic is a smell — extract sub-components or a reducer. Exhaustive discriminated-union `switch` may exceed the threshold legitimately; judge by cognitive load, not the raw number.
- **FN-6.** Components should do one thing. A component that fetches data, holds form state, computes derived values, *and* renders a complex tree is doing too much — split presentational and container concerns or extract custom hooks.
