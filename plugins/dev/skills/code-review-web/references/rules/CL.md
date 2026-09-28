# CL rules

> Thresholds below are industry-common defaults (Clean Code, cognitive-complexity research, Airbnb/typescript-eslint conventions). Adjust per project — the goal is flagging outliers for review, not rigid enforcement.

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
