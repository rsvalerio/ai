# CL rules

## Cognitive Load

- **CL-1.** *Retired* — folded into **READ-1** ("prefer clarity over cleverness").
- **CL-2.** *Retired* — folded into **READ-2** (named intermediate variables).
- **CL-3.** Avoid implicit assumptions — make preconditions explicit via types, asserts, or guard clauses rather than relying on undocumented invariants
- **CL-4.** Prefer familiar patterns over obscure language features — use well-known Rust idioms (`if let`, `match`, `?`) over exotic type-level programming unless the type-level approach provides compile-time safety guarantees that runtime checks cannot
- **CL-5.** Balance structural complexity with cognitive load — when the two conflict, use the decision heuristic below. Key distinction: **library code consumed by experts** can tolerate higher cognitive load; **application code with mixed-experience teams** should minimize it; **frequently modified code** should always minimize cognitive load regardless of audience

### Cognitive Load Decision Heuristic

Weigh these five factors:

1. **Change frequency**: high-churn code → lower cognitive load (more readers over time)
2. **Audience expertise**: mixed team → explicit patterns; experts-only library → idiomatic/terse acceptable
3. **Correctness criticality**: safety-critical → prefer explicit for clarity even at higher structural cost
4. **Team familiarity**: well-established team idioms (iterator chains, phantom types) can have higher cognitive load
5. **Domain complexity**: complex domains → reduce incidental complexity to preserve capacity for essential complexity

Default: prefer reducing cognitive load. Accept higher cognitive load for library code consumed by experts or correctness-critical paths where explicitness would obscure invariants. Application code should almost always minimize cognitive load.

| Accept higher *structural* complexity for lower cognitive load | Accept higher *cognitive* load for lower structural complexity |
|---|---|
| Intermediate variables for clarity (even if +5 lines) | Familiar iterator chains (idiomatic Rust) |
| Explicit loops over clever combinators (when >3 steps) | Type-level programming (encodes invariants) |
| Early returns / guard clauses (even if +branches) | Combinator patterns (`and_then`, `map_or_else` — safer than explicit control flow) |
| Type states (even if +types/traits) | Phantom types (compile-time guarantees) |

### Refactoring Patterns

When flagging complexity or readability issues, suggest concrete refactoring:

- **Deep nesting** → early returns + guard clauses + extract to named functions; flatten `if let Some(x) = ... { if let Some(y) = ... { } }` chains into sequential let-else guards
- **Complex boolean logic** → extract named predicates: `let is_eligible = has_permission && !is_expired && meets_threshold;`
- **Long parameter lists** → group into config/options struct or builder pattern; `fn connect(opts: ConnectionOpts)` instead of 6 positional args
- **Nested matches** → simplify with combinators: `opt.as_ref().map(|v| v.field)` instead of `match opt { Some(v) => Some(v.field), None => None }`
- **Macro overuse** → prefer traits over macros for better error messages, IDE support, and type checking; macros are justified for boilerplate reduction when trait-based approaches would require significantly more code (e.g., derive macros, declarative test generators) — see also TRAIT-8
- Long functions → extract helpers; split by responsibility; one abstraction level per function
- Tight coupling → introduce traits or interfaces; push logic behind abstractions
- Large module → split by responsibility; keep public API in one place
