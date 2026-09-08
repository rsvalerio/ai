# Rust rule index

One line per rule — enough to decide whether a rule is in play. Before filing a finding,
read that rule's full text (rationale, examples, scanning guidance, exceptions) in the
category file linked from its heading. Never file a finding from the index line alone.

## OWN — Ownership & Borrowing (typical severity: Medium--High) · [rules/OWN.md](rules/OWN.md) (4 KB)

- **OWN-1** Prefer `&T` over `&mut T`; smallest scope possible.
- **OWN-2** *Retired.* Do not reuse this ID for new rules; old findings may reference it.
- **OWN-3** Return owned data to avoid lifetime leakage
- **OWN-4** `Cow<T>` for conditional ownership
- **OWN-5** *Retired.* Do not reuse this ID for new rules; old findings may reference it.
- **OWN-6** Prefer `Option<&T>` over `&Option<T>`
- **OWN-7** `AsRef`/`Borrow` to accept owned or borrowed.
- **OWN-8** If you're cloning to satisfy the borrow checker, rethink ownership design — mechanical detection of redundant clones is handled by `clippy::redundant_clone` …
- **OWN-9** `Rc` for single-thread sharing; `Arc` when crossing thread boundaries; `Weak<T>` to break cycles.
- **OWN-10** `RefCell<T>` for single-thread interior mutability only; enforces borrowing rules at runtime (panics on violation).
- **OWN-11** Deref early in chains to reduce `&` noise (e.g., `let val = *wrapper;` before chaining methods instead of `(&wrapper).method()`)
- **OWN-12** Implement `Deref` only for transparent wrappers and smart pointers; never use it to simulate OOP inheritance …
- **OWN-13** When the borrow checker rejects code because the *whole* struct is borrowed to reach one field, split the struct rather than reaching for `.clone()` (OWN-8).

## ERR — Error Handling (typical severity: High) · [rules/ERR.md](rules/ERR.md) (12 KB)

- **ERR-1** Propagate with `?`; handle or propagate, never both; similarly, log at the handling site only — propagating an error and also logging it creates duplicate log entries
- **ERR-2** Define domain error enums; document which variants each public function may return and under what conditions.
- **ERR-3** Choose error crates by caller intent: `thiserror` when callers match on variants, `anyhow` when callers just propagate/log; combine both (thiserror for types, anyhow for context) when needed.
- **ERR-4** Add context with `.with_context()`
- **ERR-5** Detection of `unwrap`/`expect` in production code is handled by `clippy::unwrap_used` (restriction lint).
- **ERR-6** `Result<Option<T>>` over sentinel values
- **ERR-7** Map internal errors to public types at module boundaries; use `map_err()` for simple conversions and `.context()`/`.with_context()` (anyhow) for adding caller-relevant context …
- **ERR-8** `unwrap_or_else` for defaults
- **ERR-9** Implement `Error::source()` for error chains — `thiserror`'s `#[from]` and `#[source]` wire it up for you.
- **ERR-10** Never use `Result<T, String>` — use proper error types
- **ERR-11** Panic for bugs, `Result` for expected failure.
- **ERR-12** Attribute panics and errors to the *caller* with `#[track_caller]` (stable since Rust 1.46) rather than embedding `file!()`/`line!()`/`module_path!()` by hand.
- **ERR-13** Filesystem errors must name the path.
- **ERR-14** Deserialization failures on human-edited input must name the failing field. serde's default message — "invalid type: string, expected u64" …
- **ERR-15** `std::panic::catch_unwind` is a last resort, and continuing after it is a defect on its own.
- **ERR-16** Indexing panics; the fallible accessor does not.

## TRAIT — Traits & Generics (typical severity: Low--Medium) · [rules/TRAIT.md](rules/TRAIT.md) (8 KB)

- **TRAIT-1** `From`/`Into` for conversions
- **TRAIT-2** `impl Trait` in return position for flexibility; in 2024 edition, all lifetimes are captured by default (use `+ use<>` to opt out)
- **TRAIT-3** Complex bounds → `where` clauses
- **TRAIT-4** Derive deliberately, not reflexively.
- **TRAIT-5** Blanket impls sparingly (coherence conflicts)
- **TRAIT-6** Separate read/write traits (ISP)
- **TRAIT-7** `dyn Trait` only when dynamic dispatch needed
- **TRAIT-8** Prefer traits over macros (better errors, IDE support)
- **TRAIT-9** Extract traits when needed for multiple implementations, stable public APIs, or test doubles; start concrete until then.
- **TRAIT-10** Use Generic Associated Types (GATs, stable since Rust 1.65) when an associated type needs to borrow from `&self` or carry a lifetime …
- **TRAIT-11** On traits whose bounds are commonly unsatisfied, attach `#[diagnostic::on_unimplemented(message = "…", note = "…", label = "…")]` (stable since Rust 1.78 …
- **TRAIT-12** Put essential functionality in an **inherent** `impl` and have trait impls forward to it, not the other way round.
- **TRAIT-13** Public types should be `Send`, and so should the futures they produce, unless the crate deliberately targets a single-threaded runtime and says so.
- **TRAIT-14** A bound repeated across a struct, its `impl` blocks, and its signatures should be *named*, not just reformatted.

## CONC — Concurrency (typical severity: High--Critical) · [rules/CONC.md](rules/CONC.md) (24 KB)

- **CONC-1** Choose the right shared ownership primitive: `Arc<T>` for immutable shared state; `Arc<RwLock<T>>` when reads dominate and writes are rare; `Arc<Mutex<T>>` for occasional writes …
- **CONC-2** Hold locks briefly; never across `.await`
- **CONC-3** Prefer channels over shared state; bounded channels provide natural backpressure.
- **CONC-4** `tokio::select!` for cancellation/timeouts; common patterns: (1) shutdown signal: `tokio::select! { _ = shutdown.recv() => break, msg = rx.recv() => handle(msg) }` …
- **CONC-5** Never block in async — common offenders and their async equivalents: `std::thread::sleep` → `tokio::time::sleep` …
- **CONC-6** Structured concurrency: `JoinSet` for task groups — ensures all spawned tasks are tracked, awaited, and cleaned up; prevents orphaned tasks that silently leak resources or panic.
- **CONC-7** Avoid `Mutex` around collections (`HashMap`, `VecDeque`, `Vec`) in hot paths; prefer `DashMap` (sharded `RwLock`s), `crossbeam::queue`, or manual sharding for high-contention scenarios …
- **CONC-8** Channel type selection: `mpsc` / `broadcast` / `watch` / `oneshot` — see the full rule for the selection table and `RecvError::Lagged` handling.
- **CONC-9** Understand lock-free trade-offs: CAS retry loops can spin under high contention (many threads competing on the same atomic variable) …
- **CONC-10** In crates with `std`, for lazily-initialized global/static state, prefer `std::sync::OnceLock<T>` (stable since 1.70) and `std::sync::LazyLock<T>` … (not a finding in `no_std`)
- **CONC-11** `thread_local!` for genuinely per-thread state (scratch buffers, per-thread RNG, sync-code context) — each thread gets an independent instance, so no lock is needed.
- **CONC-12** Pad independently-written shared state to a cache line with `#[repr(align(N))]` (stable since Rust 1.25) to avoid **false sharing** …
- **CONC-13** A spawned task's failure does not reach anyone unless something joins it.
- **CONC-14** Graceful shutdown means the signals the platform actually sends.
- **CONC-15** For parallelism that ends inside the current function, `std::thread::scope` (stable since Rust 1.63) lets the spawned threads borrow local data directly …

## ASYNC — Async (typical severity: Medium--High) · [rules/ASYNC.md](rules/ASYNC.md) (18 KB)

- **ASYNC-1** `spawn_blocking` for CPU-heavy work
- **ASYNC-2** *Retired.* Channel selection is owned by **CONC-8**.
- **ASYNC-3** Bounded channels for backpressure (see also CONC-8 for detailed guidance)
- **ASYNC-4** Batch small, fast-completing tasks (e.g., individual DB row inserts) into fewer spawned futures to reduce scheduler overhead …
- **ASYNC-5** `join_all`/`FuturesUnordered` over serial `.await` in loops.
- **ASYNC-6** Timeouts + retries + exponential backoff for all external calls.
- **ASYNC-7** Use sync code when async adds no value.
- **ASYNC-8** Insert `tokio::task::yield_now().await` in compute loops that run for more than ~1--5ms without an `.await` point, to avoid starving other tasks on the runtime; for longer compute …
- **ASYNC-9** Separate state from task logic; pass only what tasks need; minimal tokio architecture
- **ASYNC-10** Prefer native `async fn` in traits (stable since Rust 1.75) over the `async-trait` crate.
- **ASYNC-11** Use async closures `async || {}` with `AsyncFn`/`AsyncFnMut`/`AsyncFnOnce` traits (stable since Rust 1.85); check project MSRV before adopting.
- **ASYNC-12** Prefer `std::pin::pin!` (stable since Rust 1.68) over `Box::pin` when a future only needs to be pinned for the current scope — it pins to the stack frame with no heap allocation.
- **ASYNC-13** `Stream` is the *asynchronous* `Iterator`, not a push-based inversion of it.
- **ASYNC-14** Async I/O does not turn end-of-file into "wait for more data".
- **ASYNC-15** Declare `async fn foo()` rather than `fn foo() -> impl Future<Output = …>` — it reads normally, needs no wrapping `async {}` block in the body, and is what callers expect.
- **ASYNC-16** Every future in a `tokio::select!` arm must be cancellation-safe, and that is a per-method property you have to look up rather than infer.

## PERF — Performance (typical severity: Medium) · [rules/PERF.md](rules/PERF.md) (16 KB)

- **PERF-1** Avoid premature `.collect()` — keep data as iterators through chains and collect only at the final consumption point; unnecessary intermediate collections waste allocations and defeat lazy evaluation.
- **PERF-2** `Vec::with_capacity()` when size known — eliminates reallocations in hot paths.
- **PERF-3** Avoid `.clone()` in hot paths; use `Option::take()` or `std::mem::replace()` to move instead of copy (see also OWN-8 for general clone guidance).
- **PERF-4** `Option::take()` for safe resource cleanup; prevents double drops when moving out of `Option`
- **PERF-5** `#[inline]` exposes a function's body to cross-crate inlining (non-generic functions are otherwise monomorphized in the defining crate only).
- **PERF-6** Benchmark release builds only — debug builds disable optimizations and produce misleading numbers (5--20x slower).
- **PERF-7** Prefer pass-by-value for small `Copy` types (≤16 bytes, roughly two machine words) in inner loops — indirection through `&T` adds a load per access and inhibits register allocation.
- **PERF-8** Fast hashers (`ahash` via `HashMap` from `hashbrown`, `FxHashMap`, `XxHash64`) for internal maps where keys are trusted (not user-supplied) …
- **PERF-9** `SmallVec` when collections are typically small (stack-allocated up to N, spills to heap); `ArrayVec` for hard upper bounds (compile-time capacity).
- **PERF-10** `rayon::par_iter()` for data parallelism on CPU-bound iterators.
- **PERF-11** Reuse buffers across loop iterations with `.clear()` instead of re-allocating.
- **PERF-12** Replace linear scans with composed maps (`HashMap<K, BTreeMap<...>>`) for O(1)+O(log n) lookup when data has two-level keys; adds memory overhead — profile to confirm benefit
- **PERF-13** Build formatted output with `write!`/`writeln!` directly into the destination instead of `format!` + `push_str`/`write_all` — the intermediate `String` is a wasted allocation per call.
- **PERF-14** Mark rarely-taken paths `#[cold]` so the optimizer keeps them out of the hot path's instruction cache and stops inlining them into it.
- **PERF-15** `String` is the right default; reach for small-string optimization only where the workload is dominated by short, numerous strings …
- **PERF-16** A cache is not a `HashMap` plus a cleanup task.
- **PERF-17** Do not reach for `Arc` (or `Box`) reflexively on nested types — each layer is a pointer to chase …
- **PERF-18** Store immutable owned sequences as `Box<[T]>` / `Box<str>` / `Arc<str>` rather than `Vec<T>` / `String`.
- **PERF-19** Telemetry on a hot path must be cheap enough to leave permanently enabled.
- **PERF-20** Call `shrink_to_fit()` on large, long-lived collections built by growth.
- **PERF-21** Two build-level knobs apply to **applications** (they are ignored for libraries, which do not control the final build) and are worth setting deliberately once rather than chasing in code.

## UNSAFE — Unsafe (typical severity: High--Critical) · [rules/UNSAFE.md](rules/UNSAFE.md) (7 KB)

- **UNSAFE-1** Small `unsafe` blocks; document invariants with `// SAFETY:` comments.
- **UNSAFE-2** `unsafe fn` only if every call requires upholding invariants — and specifically invariants whose violation is **undefined behaviour**.
- **UNSAFE-3** Use `std::ptr` utilities over raw arithmetic
- **UNSAFE-4** Test unsafe code thoroughly
- **UNSAFE-5** Wrap unsafe in safe public APIs, and put the unsafe code in the smallest *module* that can uphold the invariant — not merely the smallest block (UNSAFE-1).
- **UNSAFE-6** *Not a finding rule.* `unsafe extern` blocks are enforced by the Rust 2024 edition and migrated by `cargo fix --edition`; documented here for reviewer awareness only.
- **UNSAFE-7** *Not a finding rule.* `#[unsafe(...)]` attribute syntax is enforced by the Rust 2024 edition and migrated by `cargo fix --edition`; documented here for reviewer awareness only.
- **UNSAFE-8** `std::env::set_var`/`remove_var` are unsafe in 2024 edition; avoid in async contexts
- **UNSAFE-9** Never guard an `unsafe` precondition with `debug_assert!` alone.
- **UNSAFE-10** `unsafe` needs a stated reason from a short list, and evidence.
- **UNSAFE-11** Distinguish *unsafe* from *unsound*, because the review question differs.
- **UNSAFE-12** A crate that does not need `unsafe` should say so mechanically: `unsafe_code = "forbid"` in the crate's `[lints.rust]` table …

## PATTERN — Advanced Patterns (typical severity: Low--Medium) · [rules/PATTERN.md](rules/PATTERN.md) (7 KB)

- **PATTERN-1** Typestate pattern for state machines.
- **PATTERN-2** Phantom types for zero-cost guarantees
- **PATTERN-3** `bytes::Bytes` for zero-copy IO; `&str` slices for parsing — prefer `Vec<&str>` over `Vec<String>` when parsed tokens don't outlive the source
- **PATTERN-4** `MaybeUninit` for uninitialized memory
- **PATTERN-5** Custom allocators for allocation-heavy workloads; arena allocators (`bumpalo`) for batch operations (parsers, AST builders, ECS); pool allocators for fixed-size types.
- **PATTERN-6** Embed static assets that ship with the source using `include_str!` (→ `&'static str`) and `include_bytes!` (→ `&'static [u8]`) instead of reading them at runtime.
- **PATTERN-7** Prefer compile-time constants over runtime environment lookups for values fixed at build time.
- **PATTERN-8** Know when `cfg!(…)` is not a substitute for `#[cfg(…)]`.
- **PATTERN-9** Rust has no `finally`; the equivalent is a value whose `Drop` runs the cleanup, and a *guard* is that value plus mediated access to what it protects …
- **PATTERN-10** A `dyn Trait` value that only has to live for the current scope does not need a `Box`.

## MACRO — Macros (typical severity: Low--Medium) · [rules/MACRO.md](rules/MACRO.md) (4 KB)

- **MACRO-1** A macro is what you write when you have run out of language, and Rust gives you a lot of language — so a macro needs a reason that traits, generics, or a plain function could not satisfy (TRAIT-8).
- **MACRO-2** A macro must not lie about what it expands to.
- **MACRO-3** Structure macro crates so they are testable and so their expansions resolve.

## TIME — Date & Time (typical severity: Medium--High) · [rules/TIME.md](rules/TIME.md) (9 KB)

- **TIME-1** Never hand-roll calendar arithmetic.
- **TIME-2** Compute, store, compare, and log in UTC (`Utc::now()`); convert to `Local` only at the point of display.
- **TIME-3** Distinguish *elapsed-time* arithmetic from *calendar* arithmetic.
- **TIME-4** Measure elapsed time with a monotonic clock — `std::time::Instant` (or `tokio::time::Instant` in async) — never by subtracting two `Utc::now()`/`SystemTime` readings.
- **TIME-5** Keep timestamps unambiguous at every boundary.
- **TIME-6** Do not read the clock in the middle of business logic — `Utc::now()`, `SystemTime::now()`, `Local::now()`, `Zoned::now()`, `Instant::now()` for a decision rather than a measurement …

## EDITION — Rust 2024 Edition Reference · [rules/EDITION.md](rules/EDITION.md) (1 KB)

- **EDITION-1** Reserved keyword: `gen` (for future generators); use raw identifier `r#gen` if needed
- **EDITION-2** In **return position** (`-> impl Trait`), Rust 2024 captures all in-scope lifetimes and type parameters by default; use `+ use<'a, T>` to state the captures explicitly and narrow them.
- **EDITION-3** Match ergonomics restrictions: in Rust 2024, you cannot mix implicit match ergonomics (compiler-inserted `ref`/`ref mut`) with explicit `mut` or `ref` on the same binding — it's a hard error.
- **EDITION-4** Shortened temporary lifetimes: `if let` temporaries drop at branch end, not statement end
- **EDITION-5** Apply edition migration fixes before updating `edition = "2024"` in Cargo.toml

## VER — Version-Specific Features (typical severity: Low) · [rules/VER.md](rules/VER.md) (2 KB)

- **VER-1** `RwLockWriteGuard::downgrade()` (stable since Rust 1.92): converts write lock to read lock atomically; use when you need to modify data then continue reading without releasing the lock …
- **VER-4** `Mutex::clear_poison` and `RwLock::clear_poison` (stable since Rust 1.77): explicitly reset a poisoned lock after recovering from a panic, instead of unwrapping `PoisonError` or recreating the lock.
- **VER-5** Async closures with `AsyncFn`/`AsyncFnMut`/`AsyncFnOnce` traits (stable since Rust 1.85): prefer `async || {}` over `|| async {}` workarounds — the latter captures borrows incorrectly …
- **VER-6** `HashMap`/`HashSet` expose `extract_if` (stable since Rust 1.88): drain entries matching a predicate in-place without collecting; replaces `retain` + side-effect patterns …
- **VER-7** `ptr::fn_addr_eq` (stable since Rust 1.85): compare function pointers for equality by address without `as usize` casts; prefer over manual casting; check project MSRV before adopting
- **VER-8** `NonZero<T>` unified generic (stable since Rust 1.79): replaces individual `NonZeroU8`, `NonZeroU32`, etc. with a single generic.
- **VER-9** `core::range` Copy range types (stable since Rust 1.96): `core::range::Range`, `RangeFrom`, `RangeInclusive` implement `IntoIterator` instead of `Iterator`, so the range value is plain `Copy` data …

## FN — Functions & Structure (typical severity: Medium--High) · [rules/FN.md](rules/FN.md) (3 KB)

- **FN-1** Functions ≤50 lines. Each function should operate at a single abstraction level — extract low-level details into named helpers rather than mixing orchestration with bit manipulation or I/O. Context may justify exceptions (state machines, exhaustive match arms, DSL builders)
- **FN-2** Nesting ≤4 levels; use early returns/guards.
- **FN-3** Parameters ≤5; group into config structs.
- **FN-4** Return structs, not long tuples
- **FN-5** Extract complex booleans (>3 conditions) to named predicates: `is_<state>` for state checks (`is_ready`, `is_valid`), `has_<possession>` for ownership/presence …
- **FN-6** Cyclomatic complexity ≤10 (McCabe's threshold, widely adopted); `clippy::cognitive_complexity` catches the mechanical threshold …
- **FN-7** *Retired* — folded into **READ-1** and **READ-3**.
- **FN-8** DRY: see DUP-1--10 for thresholds and refactoring guidance.
- **FN-9** Explicit dependencies; no implicit state

## READ — Readability · [rules/READ.md](rules/READ.md) (7 KB)

- **READ-1** Prefer clarity over cleverness: explicit > implicit, familiar patterns > obscure features, readability > brevity
- **READ-2** Break dense expressions into named intermediate variables
- **READ-3** Name steps in long iterator chains.
- **READ-4** Document "why", not "what"
- **READ-5** Make invariants explicit (types, asserts, docs)
- **READ-6** Consistent patterns for similar problems
- **READ-7** Prefer pattern matching over nested if/else; compiler enforces exhaustiveness.
- **READ-8** For new service/application code, prefer the `tracing` crate over `log` — structured fields, spans, and per-async-task context are first-class, and most modern observability exporters …
- **READ-9** `dbg!` must not survive into committed code.
- **READ-10** Prefer `#[expect(lint, reason = "…")]` over `#[allow(lint)]` for suppressions that are meant to be temporary or that document a specific known violation …
- **READ-11** A hardcoded value in production code needs a comment saying *why that value*, what breaks if it changes, and which external system it is pinned to …
- **READ-12** Log structured events with named fields and a message *template*, not a preformatted string.
- **READ-13** Documentation describes the end state, not the journey that produced it.

## ARCH — Architecture & Modules · [rules/ARCH.md](rules/ARCH.md) (15 KB)

- **ARCH-1** No god objects or god modules; split by responsibility.
- **ARCH-2** At module boundaries, depend on traits for decoupling and testability; within a module, start concrete until abstraction is justified (see TRAIT-9 for when to extract traits)
- **ARCH-3** Modules by concern (`auth`, `db`, `error`), not layer — anti-pattern: `models/`, `controllers/`, `services/` directories that scatter a single feature across many folders …
- **ARCH-4** Shared code used by multiple concerns should be organized as its own concern-named module (e.g., `crypto`, `field_path`, `json_fields`) rather than generic buckets like `helpers`/`utils`.
- **ARCH-5** High cohesion within modules; no circular dependencies
- **ARCH-6** Match abstraction to problem complexity; YAGNI.
- **ARCH-7** Prefer flat file layout (e.g., `foo.rs` + `foo/bar.rs`) over `mod.rs` for new code; both are idiomatic — follow project convention when one exists
- **ARCH-8** `lib.rs` = thin entry point: module declarations, re-exports, crate-level docs, and small central types only.
- **ARCH-9** Minimal public surface; hide internals behind modules
- **ARCH-10** Snake_case files; singular names (`config.rs` not `configs.rs`)
- **ARCH-11** In Cargo workspaces, centralize shared dependency versions and lints in `[workspace.dependencies]` and `[workspace.lints]` …
- **ARCH-12** Enforce feature-flag invariants with `compile_error!` rather than a runtime check or a silent fallback.
- **ARCH-13** Code ported from C#, Java, C++, or Python must be reshaped, not transliterated.
- **ARCH-14** In an FFI project, business logic lives in the core crate and the FFI crate only translates.
- **ARCH-15** Workspace layout: one `Cargo.toml` at the root, all crates as siblings in a single directory (`crates/`), and a shallow grouping (`common/`, `server/`, `client/`) only past a dozen or two.
- **ARCH-16** A published library must build with nothing but `cargo` and `rustc`.
- **ARCH-17** A **new** crate or workspace should be created on the latest stable edition (2024 at the time of writing); the `resolver` key is implied by the edition and not needed.
- **ARCH-18** Never write `#![deny(warnings)]` in the source.

## API — API Design (typical severity: Medium) · [rules/API.md](rules/API.md) (25 KB)

- **API-1** Expressive type names (`TemperatureCelsius`, not `f64`) — expressive, but **short**: Rust convention is that identifiers compound at most two short words …
- **API-2** Newtype pattern: wrap primitives for type safety (`UserId(u32)`, `Email(String)`) to prevent argument order mistakes; zero-cost abstraction.
- **API-3** Prefer returning `impl Iterator` over collected `Vec` when the caller only needs iteration; return `Vec` when indexing, length, or owned storage is required
- **API-4** Builder pattern for complex construction; initialize all fields.
- **API-5** `#[must_use]` on Results, Futures, builders.
- **API-6** Doc tests with `///`
- **API-7** Prefer returning values over out params (`&mut T`); out params are acceptable for buffer reuse (`Read::read`, `Write::write`) and allocation-sensitive hot paths
- **API-8** Sealed trait pattern: prevent external implementations to reserve right to add methods without breaking changes; use private `Sealed` supertrait
- **API-9** Prevent external construction/exhaustive-match when reserving the right to add fields or variants: use `#[non_exhaustive]` on public structs and enums (stable since Rust 1.40) …
- **API-10** For published libraries, run `cargo semver-checks` in CI on every release: it detects accidental breaking changes …
- **API-11** Retire public API through ``#[deprecated(since = "…", note = "use `X` instead")]`` rather than deleting it.
- **API-12** When UTF-8 paths are already part of the product contract — paths serialized into JSON, compared in config files, stored in a database, printed in diagnostics, or returned through an API …
- **API-13** A public item should be reachable by exactly **one** path.
- **API-14** Public items carry the canonical doc sections, and a module has module docs.
- **API-15** A library sets an MSRV (`rust-version` in `Cargo.toml`) when it is created, keeps it a few releases behind current stable, and raises it in a **minor** version.
- **API-16** These rules complement rather than replace the upstream Rust API Guidelines, Style Guide, and Design Patterns book — consult those for anything not covered here.
- **API-17** Associated functions are for constructing the type, not for hosting general computation.
- **API-18** Prefer **concrete types over generics, and generics over `dyn Trait`**, and do not let any of them show through the public surface as nesting.
- **API-19** Accept the most general parameter type the function can work with.
- **API-20** A custom collection should implement the iterator traits `std` establishes, or it will not compose with anything.
- **API-21** A fallible function that *consumes* an argument must hand it back in the error.
- **API-22** Give the dominant use case a one-call entry point.

## CL — Cognitive Load · [rules/CL.md](rules/CL.md) (4 KB)

- **CL-1** *Retired* — folded into **READ-1** ("prefer clarity over cleverness").
- **CL-2** *Retired* — folded into **READ-2** (named intermediate variables).
- **CL-3** Avoid implicit assumptions — make preconditions explicit via types, asserts, or guard clauses rather than relying on undocumented invariants
- **CL-4** Prefer familiar patterns over obscure language features — use well-known Rust idioms over exotic type-level programming unless it buys a compile-time guarantee …
- **CL-5** Balance structural complexity with cognitive load — when the two conflict, use the decision heuristic below.

## DUP — Code Duplication (typical severity: Medium--High) · [rules/DUP.md](rules/DUP.md) (2 KB)

- **DUP-1** Flag identical code blocks of 5+ lines (direct copy-paste, same match branches); threshold is configurable — lower for critical code, higher for generated or boilerplate-heavy modules
- **DUP-2** Flag 3+ functions with similar structure differing only in types, literals, or field names; threshold is configurable per project
- **DUP-3** Flag 3+ occurrences of repeated patterns: error mapping, `From`/`Into`/`TryFrom` impls, similar trait implementations across different types, struct initialization, builder setup, conversion functions
- **DUP-4** Flag identical or near-identical match arms within the same function
- **DUP-5** Extract shared logic into helper functions or methods
- **DUP-6** Use generics or trait-based dispatch to unify type-varying duplicates
- **DUP-7** Use `Default` + struct update syntax (`..Default::default()`) to reduce initialization duplication
- **DUP-8** Use `From`/`Into` blanket impls or macros to reduce boilerplate conversions
- **DUP-9** Context matters: some duplication is better than the wrong abstraction; don't DRY prematurely
- **DUP-10** Test code has a higher duplication tolerance than production code; prefer clarity over DRY in tests.

## SEC — SEC · [rules/SEC.md](rules/SEC.md) (29 KB)

### Security: Memory Safety (typical severity: Critical)

- **SEC-1** No use-after-free, double-free, or data races (safe Rust prevents these at compile time; verify unsafe blocks and atomic orderings manually)
- **SEC-2** Validate all raw pointer dereferences; document safety invariants
- **SEC-3** No bad `transmute`; prefer safe casts (`as`, `From`/`Into`)
- **SEC-4** Verify `Send`/`Sync` bounds on types shared across threads

### Security: Secrets & Crypto (typical severity: High--Critical)

- **SEC-5** Secret types: disable `Debug`/`Clone`, auto-zeroize on drop.
- **SEC-6** The `secrecy` crate packages redaction and zeroization together and is the default choice over a hand-rolled wrapper (SEC-5).
- **SEC-7** Constant-time comparisons for sensitive data (use `subtle::ConstantTimeEq` from the `subtle` crate)
- **SEC-8** No hardcoded keys, passwords, tokens, or NKey seeds in source or VCS; use environment variables or secret managers
- **SEC-9** No weak algorithms (MD5/SHA1/DES) for cryptographic or security purposes; use modern alternatives (SHA-256+, AES, ChaCha20).
- **SEC-10** Prefer the OS-entropy RNG for key generation, security tokens, and any cryptographic use.

### Security: Input Validation (typical severity: High--Critical)

- **SEC-11** Validate and sanitize all external input at system boundaries using layered validation: (1) type validation — reject wrong types early, (2) range/size …
- **SEC-12** Parameterized queries for SQL; no string concatenation
- **SEC-13** Sanitize command arguments; no shell interpolation (`Command::new` over `sh -c`).
- **SEC-14** Path traversal: canonicalize and validate paths against allowed roots.
- **SEC-15** Integer overflow: use checked/saturating arithmetic for untrusted input; audit `as` casts between integer types for truncation (e.g., `u64 as u32`) …
- **SEC-16** Regex limits — but be precise about which risk applies, because the generic ReDoS advice misdescribes the Rust ecosystem.
- **SEC-33** Bound resource consumption on untrusted input: enforce size limits on buffers, collections, and strings; cap iteration counts; set timeouts on operations processing external data …

### Security: Access Control (typical severity: High--Critical)

- **SEC-17** Encode auth states in enums; compiler enforces all cases
- **SEC-18** Check authorization at every entry point; no implicit trust
- **SEC-19** Prevent IDOR: validate resource ownership before access
- **SEC-20** Tenant isolation: enforce boundaries in multi-tenant systems

### Security: Information Disclosure (typical severity: High)

- **SEC-21** No secrets, stack traces, or internal-path details in log output, error messages returned to users, or error chains (covers both logging and error-type leakage …
- **SEC-22** No fingerprinting surface on user-facing responses: do not expose server versions (`Server:` header, banner), library versions, OS details, build hashes, or feature flags.
- **SEC-23** Disable debug endpoints and verbose logging in production; gate behind explicit `cfg(debug_assertions)` or feature flags, not environment variables that can be toggled by an attacker

### Security: Concurrency (typical severity: High--Critical)

- **SEC-24** In `unsafe impl Sync`/`Send`, verify no `RefCell<T>` is exposed across threads — `RefCell<T>` is `!Sync` by design and safe Rust prevents cross-thread use at compile time …
- **SEC-25** TOCTOU (time-of-check-to-time-of-use) in file/resource operations: any `metadata()`/`exists()`/`access()` check followed by an independent open/read/write is racy …
- **SEC-38** Reentrancy in callbacks, signal handlers, and async state machines: state mutation during a nested/reentrant call can bypass invariants the outer call assumed …
- **SEC-26** Treat deadlock as a DoS vulnerability on request-handling paths: a single attacker-triggered lock-order inversion or await-holding-guard can freeze a worker pool.

### Security: FFI (typical severity: High--Critical)

- **SEC-34** Validate all raw pointers at FFI boundaries before dereferencing; document caller invariants ("caller must ensure buffer is initialized and valid for N bytes")
- **SEC-35** Never use `std::mem::uninitialized()` (deprecated, instant UB); use `MaybeUninit` instead
- **SEC-36** Audit FFI bindings for correct nullability, lifetime, and ownership transfer semantics; verify function signatures match C expectations (ABI, calling convention, signedness)
- **SEC-39** Treat every exported symbol as global namespace.
- **SEC-40** Across a boundary between two Rust dynamic libraries (or between a DLL and its host), only **portable** data may be exchanged …
- **SEC-41** Strings crossing the FFI boundary fail in two distinct ways; check both directions.
- **SEC-42** Do not export a handle whose validity depends on another handle's lifetime.

### Security: Dependencies (typical severity: High)

- **SEC-27** Review unmaintained or abandoned dependencies; check for known vulnerabilities; vet dependency source trustworthiness (unverified registries, unknown maintainers, weak security track record).
- **SEC-28** Pin dependency versions; ensure `Cargo.lock` is committed (missing lockfile allows silent dependency drift); audit lockfile changes in PRs …

### Security: Configuration (typical severity: High)

- **SEC-29** Secure defaults: TLS enabled, auth required, debug disabled; verify configuration file permissions are not world-readable
- **SEC-30** Validate configuration at startup; fail fast on insecure settings; implement secret rotation mechanisms and key expiration where applicable

### Security: Error Handling (typical severity: High)

- **SEC-31** No security bypass on error; fail closed
- **SEC-32** Ensure cleanup of sensitive resources on error paths

### Security: Testing & Verification (typical severity: Medium--High)

- **SEC-37** Fuzz security-critical parsing and deserialization code with fuzzing tools; prioritize code that handles untrusted input, protocol parsing, and format conversion

## TEST — TEST · [rules/TEST.md](rules/TEST.md) (15 KB)

### Test Structure

- **TEST-1** Every test must have meaningful assertions; no empty bodies or assertion-free tests.
- **TEST-2** One concern per test; name encodes both the state/scenario being tested AND the expected outcome — e.g., `test_empty_input_returns_none`, not just `test_parse` or `test_empty`
- **TEST-3** Integration tests in `tests/`; unit tests in `#[cfg(test)]` modules.
- **TEST-4** Shared setup via helper functions when setup is identical across 3+ tests; some duplication in test setup is acceptable for clarity (see DUP-10).

### Test Coverage & Gaps

- **TEST-5** All public API functions must have at least one test
- **TEST-6** Test error paths and edge cases, not just happy paths
- **TEST-7** Complex functions (cyclomatic complexity >10, see FN-6) need at least one test per distinct branch or match arm — this applies even when FN-6 grants a structural complexity exception …
- **TEST-8** Test boundary conditions: empty collections, zero values, max values, None variants

### Test Assertions & Quality

- **TEST-9** Consider property-based tests (`proptest`, `quickcheck`) for: serialization round-trips (`decode(encode(x)) == x`), parser correctness (arbitrary input never panics), numeric invariants …
- **TEST-10** `#[should_panic]` for expected panics; include `expected` message substring
- **TEST-11** Assert specific values, not just `is_ok()` / `is_some()`; verify the actual result
- **TEST-12** No redundant tests: identical logic, same paths, copy-paste with trivial differences.
- **TEST-29** Prefer std `assert_matches!` / `debug_assert_matches!` (stable since Rust 1.96) over hand-rolled `matches!(x, P)` + `assert!` or `if let … else panic!` when asserting a value matches a pattern …
- **TEST-30** Use snapshot testing (`insta`) for output that is verbose, structured, or awkward to assert field by field …
- **TEST-31** A CLI's real interface is the binary: argument and alias parsing, `stdout` vs `stderr` routing, exit codes, environment variables, and behaviour from a different working directory.
- **TEST-32** A test must not assert ground truth back to itself.
- **TEST-33** Anything non-deterministic or environment-dependent must be substitutable at the API boundary: filesystem and network access, clocks (TIME-6), entropy and seeds …
- **TEST-34** A doctest whose body sits inside a helper `fn` that nothing calls is compiled but never run — every assertion in it is dead.

### Test Async & Concurrency

- **TEST-13** `#[tokio::test]` + `tokio::time::pause()` for async/time tests (tokio-specific; other runtimes need different approaches — see [flakiness patterns](flakiness-patterns.md))
- **TEST-14** Use `#[tokio::test(flavor = "multi_thread")]` as a race condition discovery tool — single-threaded flavor serializes tasks and hides data races …
- **TEST-15** Deterministic sync points over `sleep`-based waits

### Test Flakiness Prevention

- **TEST-16** Fixed seed for random-based tests; production code may use `thread_rng` per SEC-10, but tests must inject a seeded RNG for determinism
- **TEST-17** No real network in unit tests; use `wiremock` or test doubles
- **TEST-18** Isolated state per test; avoid `static mut` or shared fixtures that mutate
- **TEST-19** Use `tempfile::tempdir()` for filesystem tests; no hardcoded paths
- **TEST-20** Bind to port `0` instead of hardcoded ports — hardcoded ports cause collisions when CI runs tests in parallel (`cargo test` runs test binaries concurrently by default)
- **TEST-21** Do not rely on thread or task scheduling order; use explicit synchronization (barriers, channels, `Notify`)

### Test Anti-Patterns

- **TEST-22** Avoid excessive `clone()` or `unwrap()` in tests when they mask the intent; prefer `let val = result.expect("setup: reason")` for clarity
- **TEST-23** Ensure shared global state has proper cleanup between test runs (use `Drop` guards, `tempdir`, or per-test isolation)

### Test Organization

- **TEST-24** `#[ignore]` for slow tests; document why and how to run them.
- **TEST-25** No framework-only tests that only exercise external libraries without testing crate logic.
- **TEST-26** Remove or fix `#[ignore]`d tests with no explanation — ignored tests with a tracking issue or clear justification are Low severity; ignored tests without explanation are High severity …

### Test Tooling

- **TEST-27** Coverage measurement: `cargo llvm-cov` is the current default choice — LLVM source-based coverage like `grcov` but driven by one command …
- **TEST-28** Mutation testing: `cargo-mutants` for validating test effectiveness — mutates source code (replaces operators, removes calls, changes returns) and re-runs tests …
- **TEST-35** Concurrent data structures need interleaving coverage, which ordinary tests do not provide: a test that spawns two threads and asserts the result exercises whichever interleaving the scheduler happened to pick, and passing it a thousand times says nothing about the one ordering that breaks.
- **TEST-36** `cargo nextest` runs each test in its own process, which changes what the suite can catch as well as how fast it runs: a test that aborts, segfaults …

## NATS — NATS · [rules/NATS.md](rules/NATS.md) (4 KB)

### NATS Connection (typical severity: High)

- **NATS-1** Use `ConnectOptions::new()` instead of bare `connect()`; bare connect lacks event visibility, reconnect control, and client naming
- **NATS-2** Set `.name()` for server-side debugging and connection identification
- **NATS-3** Configure `.event_callback()` for connection state visibility (connect, disconnect, reconnect, error)
- **NATS-4** Set `.reconnect_delay_callback()` with exponential backoff
- **NATS-5** Use `.retry_on_initial_connect()` for container orchestration environments
- **NATS-6** Configure `.connection_timeout()` and `.ping_interval()` appropriately for the environment
- **NATS-7** Call `client.drain()` on graceful shutdown
- **NATS-8** Clone client (cheap) rather than recreating connections

### NATS Streams (typical severity: High)

- **NATS-9** Set explicit `retention` policy (Limits / Interest / WorkQueue)
- **NATS-10** Configure `max_bytes` and/or `max_msgs` resource limits
- **NATS-11** Set `num_replicas` >= 3 for clustered production deployments with 5+ nodes; for 3-node clusters, replicas=3 means every node stores every stream …
- **NATS-12** Configure `duplicate_window` for idempotency
- **NATS-13** Enable `allow_direct` only when needed for direct-get API access (key-value stores, direct message retrieval)
- **NATS-14** Use explicit `storage` type (File vs Memory)

### NATS Consumers (typical severity: High)

- **NATS-15** Use durable consumers for persistent subscriptions (projections, read models)
- **NATS-16** Configure `ack_wait` based on processing time
- **NATS-17** Set `max_ack_pending` for consumer-level backpressure
- **NATS-18** Use pull consumers for controlled message fetching; set `max_waiting` on pull consumers to limit outstanding pull requests
- **NATS-19** Use `message.ack_with(AckKind::InProgress).await` for long-running handlers
- **NATS-20** Handle `AckKind::Nak(Option<Duration>)` for retriable failures

### NATS Observability (typical severity: Medium)

- **NATS-21** Handle connection events configured via NATS-3 — do not silently ignore; log state changes without credentials (see SEC-21 for secret handling in logs)
- **NATS-22** Track reconnects, publish/subscribe counts, consumer lag; instrument manually or use NATS server monitoring endpoints.
- **NATS-23** Ensure failures are visible (no swallow-and-ignore); propagate or log with context

### NATS Subject Design (typical severity: Low)

- **NATS-24** Use hierarchical subject patterns for filtering efficiency; avoid flat subjects, inconsistent naming, or hardcoded subjects

### NATS Backpressure & Flow Control (typical severity: High)

- **NATS-25** Set bounded capacity on subscription buffers (`ConnectOptions::subscription_capacity()`) to prevent unbounded memory growth
- **NATS-26** Enable server-side flow control on push consumers when message rates may exceed consumer processing speed
- **NATS-27** Use publish acknowledgements in JetStream (`jetstream.publish(subject, payload).await?.await?` — first await sends, second await confirms server ack) to detect backpressure from the server …
