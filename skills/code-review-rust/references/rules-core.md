# Core Rust Rules

## Ownership & Borrowing (typical severity: Medium--High)

- **OWN-1.** Prefer `&T` over `&mut T`; smallest scope possible
- **OWN-2.** *Retired.* Do not reuse this ID for new rules; old findings may reference it.
- **OWN-3.** Return owned data to avoid lifetime leakage
- **OWN-4.** `Cow<T>` for conditional ownership
- **OWN-5.** *Retired.* Do not reuse this ID for new rules; old findings may reference it.
- **OWN-6.** Prefer `Option<&T>` over `&Option<T>`
- **OWN-7.** `AsRef`/`Borrow` to accept owned or borrowed
- **OWN-8.** If you're cloning to satisfy the borrow checker, rethink ownership design — mechanical detection of redundant clones is handled by `clippy::redundant_clone`; this rule covers the design smell of cloning as a workaround for lifetime issues
- **OWN-9.** `Rc` for single-thread sharing; `Arc` when crossing thread boundaries; `Weak<T>` to break cycles. For shared-state primitive selection (`Arc<Mutex<T>>` vs `Arc<RwLock<T>>` etc.), see CONC-1
- **OWN-10.** `RefCell<T>` for single-thread interior mutability only; enforces borrowing rules at runtime (panics on violation). For cross-thread sharing, see CONC-1; for the security angle of `unsafe impl Sync` with `RefCell`, see SEC-24
- **OWN-11.** Deref early in chains to reduce `&` noise (e.g., `let val = *wrapper;` before chaining methods instead of `(&wrapper).method()`)
- **OWN-12.** Implement `Deref` only for transparent wrappers and smart pointers; never use it to simulate OOP inheritance — implicit method resolution through deref coercion creates confusing APIs and hides ownership semantics

## Error Handling (typical severity: High)

- **ERR-1.** Propagate with `?`; handle or propagate, never both; similarly, log at the handling site only — propagating an error and also logging it creates duplicate log entries
- **ERR-2.** Define domain error enums; document which variants each public function may return and under what conditions. For organizing error types (inline vs. `error.rs`), see ARCH-8
- **ERR-3.** Choose error crates by caller intent: `thiserror` when callers match on variants, `anyhow` when callers just propagate/log; combine both (thiserror for types, anyhow for context) when needed
- **ERR-4.** Add context with `.with_context()`
- **ERR-5.** Detection of `unwrap`/`expect` in production code is handled by `clippy::unwrap_used` (restriction lint). This rule's unique value is severity nuance: downgrade to Low on provably infallible paths (constant `Regex::new`, known-literal parse, `Result<T, Infallible>`). Prefer `expect("reason")` even then. Note: `if x.is_some() { x.unwrap() }` is not valid — use `if let`.
  **Scanning guidance:** `unwrap()` / `expect()` inside `#[cfg(test)]` modules, `#[test]`-attributed functions, `tests/` directories, `#[cfg(any(test, ...))]` blocks, or `test-support`-feature-gated code is **not** a finding — test panics are the explicit failure mechanism. Only count occurrences in production code paths. Before filing an ERR-5 finding, confirm the callsite is reachable outside `#[cfg(test)]`. Absolute counts that ignore this filter are meaningless (in this workspace a naive scan found 371 unwraps, all in tests; the real production count was zero).
- **ERR-6.** `Result<Option<T>>` over sentinel values
- **ERR-7.** Map internal errors to public types at module boundaries; use `map_err()` for simple conversions and `.context()`/`.with_context()` (anyhow) for adding caller-relevant context — this hides implementation details and keeps internal error types private
- **ERR-8.** `unwrap_or_else` for defaults
- **ERR-9.** Implement `Error::source()` for error chains
- **ERR-10.** Never use `Result<T, String>` — use proper error types

## Traits & Generics (typical severity: Low--Medium)

- **TRAIT-1.** `From`/`Into` for conversions
- **TRAIT-2.** `impl Trait` in return position for flexibility; in 2024 edition, all lifetimes are captured by default (use `+ use<>` to opt out)
- **TRAIT-3.** Complex bounds → `where` clauses
- **TRAIT-4.** Derive deliberately, not reflexively. `Debug` is usually safe and helpful (except on secret-bearing types — see SEC-5); `Clone`, `Copy`, `Hash`, `PartialEq`/`Eq` are semantic commitments and part of your public API — once derived, removing is a breaking change. Derive only when the type semantically supports the trait and callers need it. `clippy::missing_debug_implementations` partially covers `Debug`; this rule's unique value is the "derive with intent" philosophy (see OWN-8, PERF-3 for clone-usage guidance and SEC-5 for secret types)
- **TRAIT-5.** Blanket impls sparingly (coherence conflicts)
- **TRAIT-6.** Separate read/write traits (ISP)
- **TRAIT-7.** `dyn Trait` only when dynamic dispatch needed
- **TRAIT-8.** Prefer traits over macros (better errors, IDE support)
- **TRAIT-9.** Extract traits when needed for multiple implementations, stable public APIs, or test doubles; start concrete until then. For module boundary design, see ARCH-2
- **TRAIT-10.** Use Generic Associated Types (GATs, stable since Rust 1.65) when an associated type needs to borrow from `&self` or carry a lifetime — e.g., a streaming-iterator-style `trait LendingIterator { type Item<'a> where Self: 'a; }`. Do not adopt GATs pre-emptively; they are a powerful tool for lending-iterator and allocator-like APIs but carry steeper error messages and inference costs than plain associated types

## Concurrency (typical severity: High--Critical)

- **CONC-1.** Choose the right shared ownership primitive: `Arc<T>` for immutable shared state; `Arc<RwLock<T>>` when reads dominate and writes are rare; `Arc<Mutex<T>>` for occasional writes; almost never `Mutex<Arc<T>>` (rare exception: atomically swapping the inner `Arc`)
- **CONC-2.** Hold locks briefly; never across `.await`
- **CONC-3.** Prefer channels over shared state; bounded channels provide natural backpressure. Capacity sizing has no universal constant — it is a function of the producer/consumer rate gap and the acceptable queueing latency. Default to a small capacity (4--32) and tune from telemetry (observed queue depth, producer wait time, end-to-end latency). Red flag: unbounded channels in production — they defer OOM to runtime instead of surfacing backpressure
- **CONC-4.** `tokio::select!` for cancellation/timeouts; common patterns: (1) shutdown signal: `tokio::select! { _ = shutdown.recv() => break, msg = rx.recv() => handle(msg) }`, (2) timeout: `tokio::select! { result = work() => result, _ = tokio::time::sleep(dur) => Err(Timeout) }`
- **CONC-5.** Never block in async — common offenders and their async equivalents: `std::thread::sleep` → `tokio::time::sleep`, `std::fs::{read,write,rename,remove_file,create_dir_all,File::create,metadata,exists}` → `tokio::fs::*`, `std::net::TcpStream` → `tokio::net::TcpStream`, synchronous `reqwest::blocking` → `reqwest` async client; for unavoidable blocking (e.g., CPU-heavy compute, blocking C library, sync sqlite/rusqlite calls), use `spawn_blocking` (ASYNC-1). **Checklist for `cli::commands::bench` and `bench::runner`: any `std::fs::*` or sync store call inside an `async fn` is a defect** — either swap to `tokio::fs` or move the block under `tokio::task::spawn_blocking`
- **CONC-6.** Structured concurrency: `JoinSet` for task groups — ensures all spawned tasks are tracked, awaited, and cleaned up; prevents orphaned tasks that silently leak resources or panic. Drop a `JoinSet` to cancel all tasks in the group. Prefer `JoinSet` over ad-hoc `Vec<JoinHandle>` + `join_all` for dynamic task groups
- **CONC-7.** Avoid `Mutex` around collections (`HashMap`, `VecDeque`, `Vec`) in hot paths; prefer `DashMap` (sharded `RwLock`s), `crossbeam::queue`, or manual sharding for high-contention scenarios; for simple patterns, evaluate `std::sync::mpsc` (reworked in Rust 1.67 to be crossbeam-based) before pulling in external crates
- **CONC-8.** Channel type selection:

  | Channel | Context | Use case |
  |---|---|---|
  | `crossbeam::channel` | Sync | Select, bounded with backpressure, multi-producer |
  | `tokio::sync::mpsc` | Async | Point-to-point message passing |
  | `tokio::sync::broadcast` | Async | Fan-out / pub-sub (multiple receivers) |
  | `tokio::sync::oneshot` | Async | Single request-response or completion signal |
  | `tokio::sync::watch` | Async | Latest-value broadcast (config updates, state) |

  Rule of thumb: `crossbeam` for sync code needing `select!` or bounded backpressure; `tokio::sync` for async code — they integrate with the runtime and handle backpressure natively
- **CONC-9.** Understand lock-free trade-offs: CAS retry loops can spin under high contention (many threads competing on the same atomic variable), wasting CPU cycles and potentially performing worse than a `Mutex` under sustained contention; profile with realistic concurrency levels before assuming lock-free is faster — measure both throughput and tail latency
- **CONC-10.** For lazily-initialized global/static state, prefer `std::sync::OnceLock<T>` (stable since 1.70) and `std::sync::LazyLock<T>` (stable since 1.80) over the `once_cell` crate and the legacy `lazy_static!` macro. `OnceLock` for manual initialization, `LazyLock` for closure-based initialization. `once_cell`/`lazy_static` remain acceptable for MSRV <1.80 only — for new code at modern MSRVs, flag as an EFF finding

## Async (typical severity: Medium--High)

> ASYNC rules assume **tokio** as the async runtime. If the project uses a different runtime (e.g., `async-std`, `smol`), adapt API references accordingly.

- **ASYNC-1.** `spawn_blocking` for CPU-heavy work
- **ASYNC-2.** *Retired.* Channel selection is owned by **CONC-8**. For async-vs-sync `Mutex` choice, use `parking_lot::Mutex` / `std::sync::Mutex` when the critical section is short and never crosses `.await`; reach for `tokio::sync::Mutex` only when you must hold the guard across `.await` (see CONC-2)
- **ASYNC-3.** Bounded channels for backpressure (see also CONC-8 for detailed guidance)
- **ASYNC-4.** Batch small, fast-completing tasks (e.g., individual DB row inserts) into fewer spawned futures to reduce scheduler overhead; do NOT batch operations that should run independently or have different cancellation requirements — batching unrelated work couples their failure modes
- **ASYNC-5.** `join_all`/`FuturesUnordered` over serial `.await` in loops
- **ASYNC-6.** Timeouts + retries + exponential backoff for all external calls. Pattern: wrap with `tokio::time::timeout(dur, fut).await` → on timeout, retry with exponential backoff (`delay * 2^attempt`, cap at max). Use `tokio-retry` crate for production retry logic; hand-roll only for simple cases. Always set a max retry count to avoid infinite loops
- **ASYNC-7.** Use sync code when async adds no value. Async has overhead (future state machines, polling, context switching). Decision: use async for network I/O, concurrent operations, and event-driven flows; use sync for CPU-bound work (via `spawn_blocking`), simple sequential I/O, and operations that don't benefit from concurrency. An `async fn` that never yields is just overhead
- **ASYNC-8.** Insert `tokio::task::yield_now().await` in compute loops that run for more than ~1--5ms without an `.await` point, to avoid starving other tasks on the runtime; for longer compute (>5ms), prefer `spawn_blocking` (ASYNC-1)
- **ASYNC-9.** Separate state from task logic; pass only what tasks need; minimal tokio architecture
- **ASYNC-10.** Prefer native `async fn` in traits (stable since Rust 1.75) over the `async-trait` crate. When callers need `Send`-bounded futures (common in multi-threaded tokio runtimes), use `#[trait_variant::make(Send)]` from the `trait-variant` crate to generate a `Send`-bounded variant — this preserves static dispatch and avoids the `Box<dyn Future>` allocation that `async-trait` introduces. Reach for `async-trait` only when you genuinely need `dyn Trait` object-safety that `trait-variant` can't yet provide (deeply heterogeneous collections of erased async trait objects)
- **ASYNC-11.** Use async closures `async || {}` with `AsyncFn`/`AsyncFnMut`/`AsyncFnOnce` traits (stable since Rust 1.85); check project MSRV before adopting. The hierarchy mirrors `Fn`/`FnMut`/`FnOnce` (`AsyncFn` ⊃ `AsyncFnMut` ⊃ `AsyncFnOnce`), so accept the least-restrictive bound a callee needs. **`Send` caveat:** the `AsyncFn`-family `Send`-bound story is still incomplete — when the returned future must be `Send` (e.g. `tokio::spawn` on a multi-threaded runtime), prefer an explicit `F: Fn(T) -> Fut, Fut: Future<Output = …> + Send + 'static` signature, or move owned captures into an `async move` block, rather than relying on `AsyncFn` to infer the `Send` bound. `AsyncFn` is the right default for single-threaded use and `Arc`-protected shared state (see also ASYNC-10 for the trait-method `Send` story via `trait_variant`)

## Performance (typical severity: Medium)

- **PERF-1.** Avoid premature `.collect()` — keep data as iterators through chains and collect only at the final consumption point; unnecessary intermediate collections waste allocations and defeat lazy evaluation. Note: basic indexed-loop-to-iterator conversion is handled by `clippy::needless_range_loop`
- **PERF-2.** `Vec::with_capacity()` when size known — eliminates reallocations in hot paths
- **PERF-3.** Avoid `.clone()` in hot paths; use `Option::take()` or `std::mem::replace()` to move instead of copy (see also OWN-8 for general clone guidance)
- **PERF-4.** `Option::take()` for safe resource cleanup; prevents double drops when moving out of `Option`
- **PERF-5.** `#[inline]` exposes a function's body to cross-crate inlining (non-generic functions are otherwise monomorphized in the defining crate only). Within a crate, LLVM inlines across codegen units only with LTO or `codegen-units = 1`; otherwise cross-CGU calls are opaque. Use `#[inline]` on small, hot, cross-crate functions; use `#[inline(always)]` sparingly and only when profiling confirms it. Generic functions and `#[inline]` functions are inlined at the call site by default
- **PERF-6.** Benchmark release builds only — debug builds disable optimizations and produce misleading numbers (5--20x slower). Tools: `cargo criterion` for benchmarks, `cargo flamegraph` for CPU profiling, `tokio-console` for async task diagnostics. Workflow: profile → identify 1--2 dominant hotspots (typically 80% of cycles) → optimize those → measure again; never optimize without profiling first
- **PERF-7.** Prefer pass-by-value for small `Copy` types (≤16 bytes, roughly two machine words) in inner loops — indirection through `&T` adds a load per access and inhibits register allocation. `clippy::trivially_copy_pass_by_ref` and `large_types_passed_by_value` flag the obvious cases; this rule's unique value is the hot-loop judgment: profile before restructuring wide signatures
- **PERF-8.** Fast hashers (`ahash` via `HashMap` from `hashbrown`, `FxHashMap`, `XxHash64`) for internal maps where keys are trusted (not user-supplied); default `SipHash` is collision-resistant and needed for untrusted keys to prevent HashDoS; `ahash` is the most common ecosystem choice (used by `DashMap` and `hashbrown` by default)
- **PERF-9.** `SmallVec` when collections are typically small (stack-allocated up to N, spills to heap); `ArrayVec` for hard upper bounds (compile-time capacity). Sweet spot: 1--4 elements typical; beyond ~8, heap `Vec` is usually better
- **PERF-10.** `rayon::par_iter()` for data parallelism on CPU-bound iterators. Sync code only; for async, use `spawn_blocking` + rayon. Not beneficial for I/O-bound or small workloads
- **PERF-11.** Reuse buffers across loop iterations with `.clear()` instead of re-allocating
- **PERF-12.** Replace linear scans with composed maps (`HashMap<K, BTreeMap<...>>`) for O(1)+O(log n) lookup when data has two-level keys; adds memory overhead — profile to confirm benefit

## Unsafe (typical severity: High--Critical)

- **UNSAFE-1.** Small `unsafe` blocks; document invariants with `// SAFETY:` comments. For performance micro-optimization (e.g., `get_unchecked`), only apply after profiling confirms the bottleneck
- **UNSAFE-2.** `unsafe fn` only if every call requires upholding invariants
- **UNSAFE-3.** Use `std::ptr` utilities over raw arithmetic
- **UNSAFE-4.** Test unsafe code thoroughly
- **UNSAFE-5.** Wrap unsafe in safe public APIs
- **UNSAFE-6.** *Not a finding rule.* `unsafe extern` blocks are enforced by the Rust 2024 edition and migrated by `cargo fix --edition`; documented here for reviewer awareness only.
- **UNSAFE-7.** *Not a finding rule.* `#[unsafe(...)]` attribute syntax is enforced by the Rust 2024 edition and migrated by `cargo fix --edition`; documented here for reviewer awareness only.
- **UNSAFE-8.** `std::env::set_var`/`remove_var` are unsafe in 2024 edition; avoid in async contexts

## Advanced Patterns (typical severity: Low--Medium)

- **PATTERN-1.** Typestate pattern for state machines
- **PATTERN-2.** Phantom types for zero-cost guarantees
- **PATTERN-3.** `bytes::Bytes` for zero-copy IO; `&str` slices for parsing — prefer `Vec<&str>` over `Vec<String>` when parsed tokens don't outlive the source
- **PATTERN-4.** `MaybeUninit` for uninitialized memory
- **PATTERN-5.** Custom allocators for allocation-heavy workloads; arena allocators (`bumpalo`) for batch operations (parsers, AST builders, ECS); pool allocators for fixed-size types. Requires nightly `allocator_api` or stable crate wrappers

## Rust 2024 Edition Reference

> These are **not finding-generating rules** — they document edition behavior changes for context. The compiler and `cargo fix --edition` enforce edition migration. Reviewers should understand these changes but should not flag them as findings.

- **EDITION-1.** Reserved keyword: `gen` (for future generators); use raw identifier `r#gen` if needed
- **EDITION-2.** `impl Trait` captures all lifetimes by default; use `+ use<'a, T>` syntax to explicitly specify captures
- **EDITION-3.** Match ergonomics restrictions: in Rust 2024, you cannot mix implicit match ergonomics (compiler-inserted `ref`/`ref mut`) with explicit `mut` or `ref` on the same binding — it's a hard error. Fix: either let the compiler handle binding modes entirely, or write fully explicit patterns. Patterns that already specify all binding modes are unaffected
- **EDITION-4.** Shortened temporary lifetimes: `if let` temporaries drop at branch end, not statement end
- **EDITION-5.** Apply edition migration fixes before updating `edition = "2024"` in Cargo.toml

## Version-Specific Features (typical severity: Low)

> **Maintenance note**: Verify version-specific claims against [Rust release notes](https://releases.rs/) before adopting. Incorrect version tags mislead MSRV decisions. Features listed below were verified against release announcements; re-check if your toolchain differs.

- **VER-1.** `RwLockWriteGuard::downgrade()` (stable since Rust 1.81): converts write lock to read lock atomically; use when you need to modify data then continue reading without releasing the lock — prevents other writers from jumping in; check project MSRV before adopting
- **VER-4.** `Mutex::clear_poison` and `RwLock::clear_poison` (stable since Rust 1.84): explicitly reset a poisoned lock after recovering from a panic, instead of unwrapping `PoisonError` or recreating the lock. Use when a lock's invariant is re-established by a recovery path; check project MSRV before adopting
- **VER-5.** Async closures with `AsyncFn`/`AsyncFnMut`/`AsyncFnOnce` traits (stable since Rust 1.85): prefer `async || {}` over `|| async {}` workarounds — the latter captures borrows incorrectly; see also ASYNC-11; check project MSRV before adopting
- **VER-6.** `HashMap`/`HashSet` expose `extract_if` (stable since Rust 1.87): drain entries matching a predicate in-place without collecting; replaces `retain` + side-effect patterns; check project MSRV before adopting
- **VER-7.** `ptr::fn_addr_eq` (stable since Rust 1.85): compare function pointers for equality by address without `as usize` casts; prefer over manual casting; check project MSRV before adopting
- **VER-8.** `NonZero<T>` unified generic (stable since Rust 1.79): replaces individual `NonZeroU8`, `NonZeroU32`, etc. with a single generic. The individual aliases remain but `NonZero<u32>` is preferred in new code; check project MSRV before adopting
- **VER-9.** `core::range` Copy range types (stable since Rust 1.96): `core::range::Range`, `RangeFrom`, `RangeInclusive` implement `IntoIterator` instead of `Iterator`, so the range value is plain `Copy` data — store it in a struct or capture it by value without splitting into `start`/`end` or cloning. Use when a range needs to live in `Copy`/`#[derive(Clone, Copy)]` state. **Caveat:** range *literal* syntax (`0..5`) still produces the legacy `std::ops::Range` (which is not `Copy`) in the 2024 edition — you must construct `core::range::Range { start, end }` explicitly to get the `Copy` type; literal migration is deferred to a future edition. Check project MSRV before adopting
