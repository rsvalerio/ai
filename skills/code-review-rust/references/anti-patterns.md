# Cross-Cutting Anti-Patterns

Common Rust anti-patterns that span multiple rule categories. Use these as scan signals during review.

## Ownership & Borrowing

- **Clone to satisfy borrow checker**: Adding `.clone()` instead of restructuring ownership — masks the real issue (lifetime design) and adds unnecessary allocations. Fix: restructure to avoid simultaneous borrows, use scoped borrows, or use `Cow<T>` (OWN-8, PERF-3)
- **Reference cycle with `Rc`/`Arc`**: Creating circular references that leak memory. Fix: use `Weak<T>` for back-references (OWN-9)
- **Whole-struct borrow to reach one field**: `print_database(&db)` while `&mut db.connection_string` is live — fields borrow disjointly, functions taking `&Struct` do not. Fix: pass the fields the callee needs, or decompose into sub-structs composed back into the parent (OWN-13)
- **Deref polymorphism**: Using `Deref` to simulate OOP inheritance — implicit method resolution through deref coercion creates confusing APIs. Fix: use traits for shared behavior (OWN-12)

## Error Handling

- **String-based errors**: `Result<T, String>` or `Box<dyn Error>` in library APIs — callers cannot match on variants. Fix: define domain error enums with `thiserror` (ERR-2, ERR-10)
- **Unwrap in production**: `unwrap()`/`expect()` outside tests and provably infallible paths — panics in production. Fix: use `?`, `unwrap_or_else`, or `if let` (ERR-5)
- **Swallowed errors**: Catching `Result` and discarding the `Err` silently — hides failures. Fix: propagate, log with context, or explicitly document why the error is safe to ignore
- **Source duplicated into the error message**: `#[error("failed: {0}")]` on a variant that also carries `#[from]` — every chain printer says the cause twice. Fix: the message describes this layer; the chain supplies the cause (ERR-9)

## Async & Concurrency

- **Blocking in async**: `std::thread::sleep`, synchronous I/O, or CPU-heavy work on the async executor — starves other tasks. Fix: `tokio::time::sleep`, `tokio::fs`, `spawn_blocking` (CONC-5)
- **Lock held across `.await`**: Holding `Mutex`/`RwLock` guard across an await point — can cause deadlock or long lock hold times. Fix: drop the guard before `.await`, or restructure to separate the locked section (CONC-2)
- **Unbounded channels/queues**: Producer fills memory when consumer is slow. Fix: use bounded channels with backpressure (ASYNC-3, CONC-3)
- **Async mistaken for "waits at EOF"**: a `tokio::fs` line reader used to tail a growing log — it hits EOF and exits just like `std::fs`, so the follower silently stops on the first quiet moment. Fix: offset-tracking re-poll, `notify`, or the log transport (ASYNC-14)
- **Serial work inside a stream loop**: `while let Some(x) = s.next().await { work(x).await }` processes one item at a time no matter how many are ready. Fix, *only where the per-item work is independent*: `futures::StreamExt`'s `buffer_unordered` (after a `.map(work)`) or `for_each_concurrent`, with an explicit concurrency limit. Order-sensitive side effects or item-to-item dependencies keep the serial loop — and `buffered` is not the escape hatch, it orders results while still running items concurrently (ASYNC-5, ASYNC-13)
- **Fire-and-forget `tokio::spawn`**: the `JoinHandle` is dropped, so a panicking background task takes its work down while the process keeps reporting healthy and still exits 0. Fix: `JoinSet` and drain `join_next()`, or await the handle and split `JoinError` into `is_panic()` vs `is_cancelled()` (CONC-13, CONC-6)
- **Shutdown path that only hears Ctrl-C**: `signal::ctrl_c().await` as the whole shutdown story — SIGTERM, which is what containers and systemd send, kills the process before any cleanup runs. Fix: `select!` over `ctrl_c()` and `SignalKind::terminate()`, propagate via `CancellationToken`/`watch`, bound the drain with a timeout (CONC-14)
- **`Lagged` swallowed on a broadcast receiver**: `RecvError::Lagged(n)` is `n` messages permanently lost, and `recv()` keeps working afterwards — `?`-ing or log-and-continue reports healthy while dropping data. Fix: handle it distinctly from `Closed` — resync, resize, or fail loudly (CONC-8)
- **Non-cancellation-safe future in a `select!` arm**: `read_exact` (or any multi-step `async fn` of your own) as one branch — losing the race *drops* the future, so the bytes already read are gone and the stream is left mid-message, with every later read misaligned. Fix: pin the future outside the loop and poll `&mut fut`, or move the work into its own task and select over a channel (ASYNC-16, ASYNC-12)
- **`Arc<Mutex<T>>` for a fan-out that ends in this function**: threads given `'static` clones of everything because `thread::spawn` demands it, when `std::thread::scope` would let them borrow the caller's data directly and joins them all on the way out. Fix: `thread::scope`, or `rayon` where it is a plain data-parallel iterator (CONC-15, PERF-10)
- **`Stream` treated as push-based**: assuming a stream hands items to the consumer on its own. `poll_next` is a *pull*, identical in shape to `Iterator::next` — nothing advances without a consumer polling. Fix: use `Sink`/`broadcast`/callbacks when the producer must drive (ASYNC-13)

## Resources & Cleanup

- **Guard bound to `_`**: `let _ = lock.acquire();` drops the guard *immediately* and protects nothing, while `let _guard = …` holds it to the end of the scope — one character apart, both compile (PATTERN-9)
- **`Drop` treated as a durability guarantee**: cleanup that must happen is skipped by `mem::forget`, `abort`, a panic during unwind, and `SIGKILL`. Fix: keep the guard, and add a reconciliation path for the cleanup that actually matters (PATTERN-9, CONC-14)

## Date & Time

- **Hand-rolled calendar math**: manual month-length tables, `year % 4` leap-year checks, or `secs / 86_400` date derivation — wrong at century years, month boundaries, and DST. Fix: use `chrono`/`jiff` (TIME-1)
- **Naive or local timestamps crossing a boundary**: `Local::now()` or a `NaiveDateTime` persisted, logged, or serialized — the value means something different on every host. Fix: UTC everywhere, `Local` only at display, RFC 3339 on the wire (TIME-2, TIME-5)
- **Wall clock as a stopwatch**: `Utc::now() - start` or `SystemTime::now().duration_since(start)` to measure elapsed time — NTP adjustments can make it negative or fail the `duration_since`. Fix: `Instant::elapsed()` (TIME-4)

## Macros & Public Surface

- **Macro that rewrites the signature**: an attribute macro that adds a parameter, changes the item's kind, or makes a `fn` `async` — the source no longer describes the program. Fix: emit only what the written signature implies; use a function or trait if the transformation is the point (MACRO-2, TRAIT-8)
- **Item reachable by two public paths**: a compatibility `pub use` left behind by a refactor, so `crate::Connection` and `crate::db::Connection` are the same type with two names in docs, search, and errors. Fix: one public path per item; re-export from a `pub(crate)` module instead (API-13)
- **Glob re-export or crate `prelude`**: `pub use foo::*` exports whatever is added later and is invisible in a diff; two preludes in one file collide (`E0659`). Fix: enumerate re-exports; fix the module layout instead of papering over it (API-13, ARCH-3)
- **Newtype that guards nothing**: `pub struct Month(pub u8)` with an infallible constructor — every caller still re-validates, and the public field bypasses the check anyway. Fix: private field, fallible constructor, no infallible `From` (API-2)

## Abstraction & Generics

- **Bound creep**: a signature generalized one reasonable step at a time — `&str` → `impl AsRef<str>` → `<'a, S: AsRef<str> + Send + Sync + ?Sized>` — where every step served a caller that does not exist. Fix: write the concrete signature the callers actually have; generalize when a second one arrives (API-18, ARCH-6)
- **Over-constrained bounds**: `Send`, `Sync`, `Clone`, or `'static` on a parameter the body never sends, clones, or stores — a requirement imposed on every caller for nothing. Removing it later is a compatible relaxation, but only after callers have already been turned away or worked around it — and adding one is the breaking direction, so the set cannot be widened defensively either. Fix: the minimum bound set the body needs (API-18)
- **Speculative trait for a second impl that never comes**: a `Format`/`Storage`/`Backend` trait introduced because a second implementation was anticipated, which then hides the decomposition that would have helped. Fix: stay concrete; let repetition, not prediction, trigger the abstraction (ARCH-6, TRAIT-9)
- **General form as the only form**: a crate where the standard use requires selecting every option first, so the docs open with four lines of configuration and every call site restates the same defaults. Fix: a convenience entry point named for the default it picks, delegating to the general form (API-22, API-4)
- **Allocation avoided at the cost of clarity in cold code**: a lifetime parameter, `Cow`, or unsafe block introduced to remove a clone on a startup, config, or error path nobody profiled. Fix: keep the clone; profile before trading readability for allocations (PERF-3, PERF-6)

## Ports from Other Languages

- **Interface-per-service `dyn Trait`**: a trait implemented exactly once, passed as `Arc<dyn Service>` because the original had an `IService`. Fix: concrete type; escalate to generics, then `dyn`, only when a second implementation actually exists (API-18, ARCH-13)
- **`Arc` at every level**: reflexively shared nested types, so a hot read chases two or three pointers to reach one field. Fix: embed the data; lift the hot field (PERF-17)
- **Weasel-word types**: `BookingService`, `ConnectionManager`, `WidgetFactory` — a role every type has. Fix: `Bookings`, `BookingDispatcher`, `WidgetBuilder` (API-1)
- **Computation parked in an `impl` block**: `Database::check_parameters(p)` with no receiver, because the source language had no free functions. Fix: a module-level `fn` (API-17)
- **Static as a global singleton in a library**: a registry or counter in a `static`, silently duplicated when two majors of the crate are linked, or per dynamic library. Fix: caller-owned state passed in (CONC-10, SEC-40)

## Testing

- **Tautological test**: `assert_eq!(CONSTANTS, [the same literals])`, or an expected value recomputed with the implementation's own logic — passes by construction and can never fail usefully. Fix: assert a property the value must satisfy (TEST-32)
- **Doctest that never runs**: an example whose body sits inside a hidden helper `fn` nothing calls — it type-checks, and its assertions can never fail. Fix: reserve the wrapper for setup-only examples; give asserting examples a real fixture (TEST-34)
- **Un-gated test hooks**: `bypass_certificate_checks()` or a secret accessor compiled into release because it sat behind no `#[cfg(feature = "test-util")]`. Fix: gate every testing affordance behind one clearly named feature (TEST-33)

## Type Safety

- **Primitive obsession**: Using bare `u32`, `String`, `f64` where a newtype would prevent misuse (mixing user_id with order_id, Celsius with Fahrenheit). Fix: newtype pattern (API-1, API-2)
- **Stringly-typed APIs**: Using `String` for values with a known set of variants. Fix: use enums
- **Correlated flag beside its payload**: `ssl: bool` next to `ssl_cert: Option<PathBuf>` — `(true, None)` is representable and meaningless, and every use site unwraps. Fix: one enum carrying the payload on the arm that has it (PATTERN-1)
- **Derived `Default` that produces an invalid value**: `#[derive(Default)]` on a config struct yields port 0, zero connections, a zero timeout — states the type should never hold, now reachable from `unwrap_or_default()`. Fix: omit `Default`, or use field types with no `Default` so the derive fails to compile (TRAIT-4, API-2)
- **Derived `Deserialize` bypassing the validating constructor**: a newtype with a fallible `new` and a derived `Deserialize` is unvalidated for exactly the input that arrives over the wire. Fix: `#[serde(try_from = "…")]` routing through `TryFrom` (API-2, SEC-11)

## Security

- **Hardcoded secrets**: API keys, passwords, tokens in source code or VCS. Fix: environment variables or secret managers (SEC-8)
- **User-controlled value that starts with `-` passed to `Command::arg`**: `.arg()` blocks *command* injection and not *argument* injection — a "filename" of `--output=…` or `-o` re-tasks the child program with no shell involved. Fix: reject a leading dash outright, or use the child program's own safe encoding; `--` before user operands only helps when that program honours it, and `./` still disambiguates relative paths (SEC-13)
- **Buffer pre-allocated from a wire-supplied length**: `Vec::with_capacity(hdr.count)` allocates before a byte of payload is read or validated, so a four-byte field is a remote memory-exhaustion request. Fix: check the length against a `MAX_*` constant first, and read through an explicit bound — `reader.take(MAX_BYTES)` — so the buffer is capped by what may arrive, not only by what the header claimed (SEC-33)
- **Size limit applied before decompression only**: a bounded gzip/zstd/zip body is unbounded after inflation, so the request cap bounds nothing about memory. Fix: decompress through a `take`-limited reader and fail at the limit (SEC-33)
- **`canonicalize` on a path that does not exist yet**: the traversal check returns `NotFound` for any file about to be *created*, so it gets dropped or turned into a fail-open. Fix: canonicalize the parent directory, confirm the root, then join one validated component (SEC-14)
- **"Fixing" ReDoS in the `regex` crate**: `regex` is automata-based and linear-time by construction — a rewrite to avoid catastrophic backtracking there is a false finding. The real risks are compiling an *untrusted pattern* without `size_limit`, recompiling in a loop, and `fancy-regex`/PCRE bindings, which do backtrack (SEC-16)
- **Missing input validation**: Trusting external input without size limits, type checks, or sanitization. Fix: validate at system boundaries (SEC-11)
- **Index computed from untrusted input**: `buf[header.len as usize]`, `split_at(n)` on a parsed length, `&s[..n]` on a wire value — a remote panic, i.e. a DoS. Fix: `get`, `get(a..b)`, `split_at_checked` (ERR-16, SEC-33)
- **`Path::join` with a user-supplied segment**: an absolute segment silently *replaces* the base, so `uploads.join(name)` evaluates to `/etc/shadow`. Fix: walk the segment's `Components` and reject `Prefix` (a Windows drive), `RootDir`, and `ParentDir` before joining, then canonicalize the result and confirm it is still under the root (SEC-14)
- **Secret redacted in `Debug` but not in `Serialize`**: the derived `Serialize` puts the value into every JSON response, cache entry, and audit record. Fix: treat both derives alike, or wrap in `secrecy` (SEC-5, SEC-6)
- **Path re-resolved between check and use**: `p.is_dir()` then a recursive delete on `p` — an attacker swaps in a symlink in between (CVE-2022-21658 in `std::fs`). Fix: open a handle with `O_NOFOLLOW | O_DIRECTORY` and operate through the descriptor (SEC-25)
- **Retained pointer into a temporary `CString`**: `seterr(CString::new(s)?.as_ptr())` — the temporary lives to the end of the statement, so a callee that reads the bytes *during* the call is fine; the bug is a `seterr` that stores the pointer or reads it later, which is then dangling. Fix: where the callee retains, bind the `CString` to something that outlives the retention (SEC-41)
- **Exported handle borrowed from another handle**: `dbm_iter_new(db) -> *mut KeysIter` — the lifetime tying iterator to parent does not cross the FFI boundary, and the resulting use-after-free usually works. Fix: fold the cursor into the owner (SEC-42)

## Build Configuration

- **`#![deny(warnings)]` in the crate root**: turns every future rustc release into a possible build break and blocks anyone from building with an extra lint set. Fix: `RUSTFLAGS="-D warnings"` in CI, plus a named lint list in `[workspace.lints]` (ARCH-18)
- **Dependency judged only by what it runs at runtime**: a `build.rs` or proc macro executes with full privileges at *compile* time — `cargo check` and a rust-analyzer save are enough — so "only a dev-dependency" and "we never call it" mitigate nothing. Fix: review new build scripts and proc-macro crates in lockfile diffs; `cargo vet` to record that a human read a given version (SEC-27)
- **Committed lockfile that CI silently re-resolves**: without `--locked`, a build quietly picks versions nobody reviewed and the committed `Cargo.lock` is decoration. Fix: `cargo build --locked` in CI (SEC-28)
- **Crate with no `unsafe` that does not say so**: nothing stops the next PR from adding a block for a micro-optimization. Fix: `unsafe_code = "forbid"` in `[lints.rust]`, inherited from `[workspace.lints]` (UNSAFE-12, ARCH-11)
