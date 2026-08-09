# Structure and Readability Rules

## Functions & Structure (typical severity: Medium--High)

> Thresholds below are industry-common defaults (Clean Code, cognitive complexity research). Adjust per project — the goal is flagging outliers for review, not rigid enforcement.

- **FN-1.** Functions ≤50 lines. Each function should operate at a single abstraction level — extract low-level details into named helpers rather than mixing orchestration with bit manipulation or I/O. Context may justify exceptions (state machines, exhaustive match arms, DSL builders)
- **FN-2.** Nesting ≤4 levels; use early returns/guards. Transform nested conditionals: `let Some(x) = input else { return Err(...) };` (let-else, stable since 1.65), `if !precondition { return early; }` (guard clause), or let-chains (`if let Some(x) = opt && x.is_valid() { ... }`, stable in Rust 2024) instead of nested `if let` pyramids
- **FN-3.** Parameters ≤5; group into config structs
- **FN-4.** Return structs, not long tuples
- **FN-5.** Extract complex booleans (>3 conditions) to named predicates: `is_<state>` for state checks (`is_ready`, `is_valid`), `has_<possession>` for ownership/presence (`has_data`, `has_permission`), `should_<action>` for conditional actions (`should_retry`, `should_log`), `can_<capability>` for ability checks (`can_read`, `can_connect`)
- **FN-6.** Cyclomatic complexity ≤10 (McCabe's threshold, widely adopted); `clippy::cognitive_complexity` catches the mechanical threshold — this rule's unique value is the Rust-specific nuance: exhaustive pattern matching naturally inflates cyclomatic complexity, so parsers, state machines, and exhaustive matches may exceed this; evaluate cognitive load (READ-1) rather than forcing extraction
- **FN-7.** *Retired* — folded into **READ-1** and **READ-3**. Iterator-chain length is a readability concern, not a structural one; Clippy handles the mechanical cases (`manual_map`, `manual_flatten`, `manual_filter_map`).
- **FN-8.** DRY: see DUP-1--10 for thresholds and refactoring guidance. Clone abuse: see OWN-8 and PERF-3
- **FN-9.** Explicit dependencies; no implicit state

## Readability

- **READ-1.** Prefer clarity over cleverness: explicit > implicit, familiar patterns > obscure features, readability > brevity
- **READ-2.** Break dense expressions into named intermediate variables
- **READ-3.** Name steps in long iterator chains. When a chain exceeds ~3--4 combinators or mixes control flow with data transformation, either break it into named intermediates (`let parsed = items.iter().map(...).collect::<Result<Vec<_>, _>>()?;`) or switch to an explicit `for` loop. Clippy handles the mechanical cases (`manual_map`, `manual_flatten`, `manual_filter_map`); this rule covers the structural upper bound
- **READ-4.** Document "why", not "what"
- **READ-5.** Make invariants explicit (types, asserts, docs)
- **READ-6.** Consistent patterns for similar problems
- **READ-7.** Prefer pattern matching over nested if/else; compiler enforces exhaustiveness. Note: clippy catches narrow cases (`match_like_matches_macro`); this rule covers the broader stylistic preference
- **READ-8.** For new service/application code, prefer the `tracing` crate over `log` — structured fields, spans, and per-async-task context are first-class, and most modern observability exporters (OpenTelemetry, Honeycomb, Datadog) target `tracing::Subscriber`. The `log` crate is still appropriate for libraries that want a minimal dependency footprint; bridge library logs into `tracing` with `tracing-log`. Flag `println!`/`eprintln!` in non-binary, non-test code as a finding. **In CLI binaries**, where direct printing is correct, honour the stream contract: `stdout` carries the program's *result* (the part a caller may pipe or parse), `stderr` carries diagnostics, progress, warnings, and errors. Any `println!` used for a diagnostic breaks downstream pipelines and must be `eprintln!`
- **READ-9.** `dbg!` must not survive into committed code. It writes the expression source and value to stderr *unconditionally* — it is not stripped in release builds, unlike `debug_assert!` — so a leftover call becomes permanent noise on the diagnostic stream and can leak internal state (SEC-21). It also takes ownership of its argument, so inserting or removing it can change move semantics. Enable `clippy::dbg_macro` (restriction lint) at deny level in CI to catch it mechanically; use `tracing::debug!` for logging that is meant to stay
- **READ-10.** Prefer `#[expect(lint, reason = "…")]` over `#[allow(lint)]` for suppressions that are meant to be temporary or that document a specific known violation (both `expect` and the `reason` field are stable since Rust 1.81). `#[expect]` suppresses the lint exactly like `#[allow]`, but additionally warns (`unfulfilled_lint_expectations`) once the lint stops firing — so the suppression deletes itself from the codebase instead of outliving the problem it was hiding. `#[allow]` remains correct for permanent, intentional policy exceptions. **Footgun:** an `#[expect]` on a lint that fires only under some cfg/feature combinations produces `unfulfilled` warnings in every other configuration, so use `#[allow]` for cfg-dependent suppressions or scope the expectation to the same `#[cfg]`. Per rules-classification, a suppression carrying a specific, accurate `reason` earns the one-level severity reduction; a bare `#[allow]` with no rationale does not

## Architecture & Modules

- **ARCH-1.** No god objects or god modules; split by responsibility. Module-level red flags: >500 lines, mixed unrelated concerns (e.g., parsing + networking + serialization in one file), >10 public items with no cohesive theme
- **ARCH-2.** At module boundaries, depend on traits for decoupling and testability; within a module, start concrete until abstraction is justified (see TRAIT-9 for when to extract traits)
- **ARCH-3.** Modules by concern (`auth`, `db`, `error`), not layer — anti-pattern: `models/`, `controllers/`, `services/` directories that scatter a single feature across many folders; instead, group by domain so related types, logic, and tests live together
- **ARCH-4.** Shared code used by multiple concerns should be organized as its own concern-named module (e.g., `crypto`, `field_path`, `json_fields`) rather than generic buckets like `helpers`/`utils`. Cross-module dependencies are normal; keep them explicit, one-directional, and keep public API re-exports curated in `lib.rs`. If the code is purely implementation detail, prefer an `internal` module with descriptive submodules over a grab-bag utility module.
- **ARCH-5.** High cohesion within modules; no circular dependencies
- **ARCH-6.** Match abstraction to problem complexity; YAGNI
- **ARCH-7.** Prefer flat file layout (e.g., `foo.rs` + `foo/bar.rs`) over `mod.rs` for new code; both are idiomatic — follow project convention when one exists
- **ARCH-8.** `lib.rs` = thin entry point: module declarations, re-exports, crate-level docs, and small central types only. Move out: error types (→ `error.rs` when >50 lines or shared across modules), implementation logic, private helpers, domain logic. Organization heuristic: inline error types for ≤2 types in ≤50 lines; when types exceed ~50 lines or you have 3+ helper functions, extract to a dedicated module
- **ARCH-9.** Minimal public surface; hide internals behind modules
- **ARCH-10.** Snake_case files; singular names (`config.rs` not `configs.rs`)
- **ARCH-11.** In Cargo workspaces, centralize shared dependency versions and lints in `[workspace.dependencies]` and `[workspace.lints]`, then inherit with `dep = { workspace = true }` and `[lints] workspace = true`. Prevents version drift across member crates and makes CVE upgrades a single-point change. Flag workspaces where sibling crates pin different versions of the same transitive dep or duplicate lint configuration
- **ARCH-12.** Enforce feature-flag invariants with `compile_error!` rather than a runtime check or a silent fallback. Cargo features are *additive* — any consumer in the dependency graph can turn one on, and `--all-features` turns on every one — so a crate whose backends are mutually exclusive, or that requires at least one of a set, must say so at compile time:

  ```rust
  #[cfg(not(any(feature = "sqlite", feature = "postgres")))]
  compile_error!("enable exactly one backend: `sqlite` or `postgres`");
  #[cfg(all(feature = "sqlite", feature = "postgres"))]
  compile_error!("`sqlite` and `postgres` are mutually exclusive");
  ```

  Cover both directions (none-selected *and* over-selected); a single `not(any(...))` guard still lets `--all-features` produce a nonsense build. Prefer restructuring so features are genuinely additive (e.g. select the backend at runtime from a trait object) — mutually exclusive features are a design smell that breaks feature unification for downstream crates. `compile_error!` is the right tool where that restructuring is not possible, and inside declarative/procedural macros to reject invalid invocations with a readable message

## API Design (typical severity: Medium)

- **API-1.** Expressive type names (`TemperatureCelsius`, not `f64`)
- **API-2.** Newtype pattern: wrap primitives for type safety (`UserId(u32)`, `Email(String)`) to prevent argument order mistakes; zero-cost abstraction. "Zero-cost" is a statement about performance, not about layout: a plain `struct UserId(u32)` has *no guaranteed* ABI or memory layout, so passing it across FFI, `transmute`-ing it, or casting `&[UserId]` to `&[u32]` is unsound. Add `#[repr(transparent)]` when any of those matter — it guarantees the type has exactly the layout and ABI of its single non-zero-sized field (other fields must be zero-sized, e.g. `PhantomData`). Required on newtypes crossing an FFI boundary (SEC-36) and on wrappers the caller may reinterpret; unnecessary noise on ordinary domain newtypes that never leave Rust
- **API-3.** Prefer returning `impl Iterator` over collected `Vec` when the caller only needs iteration; return `Vec` when indexing, length, or owned storage is required
- **API-4.** Builder pattern for complex construction; initialize all fields
- **API-5.** `#[must_use]` on Results, Futures, builders. Note that `Result`, `Option`, and futures are *already* `#[must_use]` in std, so annotating a function returning one adds nothing — the value is in annotating (a) **your own types** whose construction is pointless if discarded (`#[must_use = "remember to execute the query"] struct Query(…)`, guards, builders mid-chain), and (b) functions returning a plain type where discarding signals a bug (`Vec::is_empty`, a pure transform mistaken for an in-place mutation). Always use the message form `#[must_use = "…"]`: the bare attribute produces "unused return value that must be used", which tells the reader nothing they could not see. Write the message as the action the caller forgot, not as a restatement of the warning
- **API-6.** Doc tests with `///`
- **API-7.** Prefer returning values over out params (`&mut T`); out params are acceptable for buffer reuse (`Read::read`, `Write::write`) and allocation-sensitive hot paths
- **API-8.** Sealed trait pattern: prevent external implementations to reserve right to add methods without breaking changes; use private `Sealed` supertrait
- **API-9.** Prevent external construction/exhaustive-match when reserving the right to add fields or variants: use `#[non_exhaustive]` on public structs and enums (stable since Rust 1.40) — it is the idiomatic and tool-aware mechanism (`cargo semver-checks` understands it). Reach for the `_private: ()` field pattern only when you need to forbid construction *and* still allow pattern matching on all other public fields, which `#[non_exhaustive]` cannot express on its own
- **API-10.** For published libraries, run `cargo semver-checks` in CI on every release: it detects accidental breaking changes (removed items, changed signatures, added required trait bounds, changed MSRV) that pure version bumps won't catch. Pair with `cargo public-api --diff-git-checkouts` for a human-readable diff of the public surface
- **API-11.** Retire public API through `#[deprecated(since = "…", note = "use `X` instead")]` rather than deleting it. Deprecating is a non-breaking, minor-version change; removal is a major-version break, so the attribute buys a migration window in which callers get a compiler warning naming the replacement. Applies to functions, types, traits, modules, constants, and type aliases — but **not** trait impls, where it is silently useless (`useless_deprecated` lint). Two review checks: (1) `since` must be the version the deprecation *ships in*, not the version it will be removed in — a wrong `since` breaks `#[deprecated]`'s interaction with `cargo semver-checks` (API-10) and misleads readers; (2) `note` must name the concrete replacement, since a note saying only "deprecated" leaves the caller no path forward. Deprecated items still warn at internal call sites — migrate those in the same change rather than papering over them with `#[allow(deprecated)]`, and when a genuine internal use must remain (e.g. implementing the deprecated item in terms of the new one), scope the allow to that item with a reason (READ-10)

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
