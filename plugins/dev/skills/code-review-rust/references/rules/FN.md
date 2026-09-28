# FN rules

## Functions & Structure (typical severity: Medium--High)

> Thresholds below are industry-common defaults (Clean Code, cognitive complexity research). Adjust per project — the goal is flagging outliers for review, not rigid enforcement.

- **FN-1.** Functions ≤50 lines. Each function should operate at a single abstraction level — extract low-level details into named helpers rather than mixing orchestration with bit manipulation or I/O. Context may justify exceptions (state machines, exhaustive match arms, DSL builders)
- **FN-2.** Nesting ≤4 levels; use early returns/guards. Transform nested conditionals: `let Some(x) = input else { return Err(...) };` (let-else, stable since 1.65), `if !precondition { return early; }` (guard clause), or let-chains (`if let Some(x) = opt && x.is_valid() { ... }`, stable in Rust 2024) instead of nested `if let` pyramids
- **FN-3.** Parameters ≤5; group into config structs. Beyond ~4 parameters the failure mode is not length but **mix-ups** — `new(bank: &str, customer: &str, currency: &str, amount: u64)` accepts any permutation of the three `&str`s and compiles. Two fixes compose: newtype the primitives so the compiler rejects the swap (API-2), and *cascade* the construction, grouping parameters into the intermediate types the domain already has (`Deposit::new(account: Account, amount: Currency)`, with `Account::new(bank, customer)` one level down). Beyond 4 optional parameters, a builder is the answer instead (API-4).
  **Ordering is part of the signature.** When the same conceptual parameters recur across functions — in a crate or across a family of crates — they must appear in the same order every time: call-specific parameters first, ubiquitous ones (`&logger`, `&ctx`) last, closures always last, and no more than one closure. A `tenant_id, user_id` here and `user_id, tenant_id` there is a bug waiting for two same-typed arguments to meet
- **FN-4.** Return structs, not long tuples
- **FN-5.** Extract complex booleans (>3 conditions) to named predicates: `is_<state>` for state checks (`is_ready`, `is_valid`), `has_<possession>` for ownership/presence (`has_data`, `has_permission`), `should_<action>` for conditional actions (`should_retry`, `should_log`), `can_<capability>` for ability checks (`can_read`, `can_connect`)
- **FN-6.** Cyclomatic complexity ≤10 (McCabe's threshold, widely adopted); `clippy::cognitive_complexity` catches the mechanical threshold — this rule's unique value is the Rust-specific nuance: exhaustive pattern matching naturally inflates cyclomatic complexity, so parsers, state machines, and exhaustive matches may exceed this; evaluate cognitive load (READ-1) rather than forcing extraction
- **FN-7.** *Retired* — folded into **READ-1** and **READ-3**. Iterator-chain length is a readability concern, not a structural one; Clippy handles the mechanical cases (`manual_map`, `manual_flatten`, `manual_filter_map`).
- **FN-8.** DRY: see DUP-1--10 for thresholds and refactoring guidance. Clone abuse: see OWN-8 and PERF-3
- **FN-9.** Explicit dependencies; no implicit state
