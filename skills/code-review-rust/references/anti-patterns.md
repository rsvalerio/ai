# Cross-Cutting Anti-Patterns

Common Rust anti-patterns that span multiple rule categories. Use these as scan signals during review.

## Ownership & Borrowing

- **Clone to satisfy borrow checker**: Adding `.clone()` instead of restructuring ownership — masks the real issue (lifetime design) and adds unnecessary allocations. Fix: restructure to avoid simultaneous borrows, use scoped borrows, or use `Cow<T>` (OWN-8, PERF-3)
- **Reference cycle with `Rc`/`Arc`**: Creating circular references that leak memory. Fix: use `Weak<T>` for back-references (OWN-9)
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
- **`Stream` treated as push-based**: assuming a stream hands items to the consumer on its own. `poll_next` is a *pull*, identical in shape to `Iterator::next` — nothing advances without a consumer polling. Fix: use `Sink`/`broadcast`/callbacks when the producer must drive (ASYNC-13)

## Date & Time

- **Hand-rolled calendar math**: manual month-length tables, `year % 4` leap-year checks, or `secs / 86_400` date derivation — wrong at century years, month boundaries, and DST. Fix: use `chrono`/`jiff` (TIME-1)
- **Naive or local timestamps crossing a boundary**: `Local::now()` or a `NaiveDateTime` persisted, logged, or serialized — the value means something different on every host. Fix: UTC everywhere, `Local` only at display, RFC 3339 on the wire (TIME-2, TIME-5)
- **Wall clock as a stopwatch**: `Utc::now() - start` or `SystemTime::now().duration_since(start)` to measure elapsed time — NTP adjustments can make it negative or fail the `duration_since`. Fix: `Instant::elapsed()` (TIME-4)

## Macros & Public Surface

- **Macro that rewrites the signature**: an attribute macro that adds a parameter, changes the item's kind, or makes a `fn` `async` — the source no longer describes the program. Fix: emit only what the written signature implies; use a function or trait if the transformation is the point (MACRO-2, TRAIT-8)
- **Item reachable by two public paths**: a compatibility `pub use` left behind by a refactor, so `crate::Connection` and `crate::db::Connection` are the same type with two names in docs, search, and errors. Fix: one public path per item; re-export from a `pub(crate)` module instead (API-13)
- **Glob re-export or crate `prelude`**: `pub use foo::*` exports whatever is added later and is invisible in a diff; two preludes in one file collide (`E0659`). Fix: enumerate re-exports; fix the module layout instead of papering over it (API-13, ARCH-3)
- **Newtype that guards nothing**: `pub struct Month(pub u8)` with an infallible constructor — every caller still re-validates, and the public field bypasses the check anyway. Fix: private field, fallible constructor, no infallible `From` (API-2)

## Ports from Other Languages

- **Interface-per-service `dyn Trait`**: a trait implemented exactly once, passed as `Arc<dyn Service>` because the original had an `IService`. Fix: concrete type; escalate to generics, then `dyn`, only when a second implementation actually exists (API-18, ARCH-13)
- **`Arc` at every level**: reflexively shared nested types, so a hot read chases two or three pointers to reach one field. Fix: embed the data; lift the hot field (PERF-17)
- **Weasel-word types**: `BookingService`, `ConnectionManager`, `WidgetFactory` — a role every type has. Fix: `Bookings`, `BookingDispatcher`, `WidgetBuilder` (API-1)
- **Computation parked in an `impl` block**: `Database::check_parameters(p)` with no receiver, because the source language had no free functions. Fix: a module-level `fn` (API-17)
- **Static as a global singleton in a library**: a registry or counter in a `static`, silently duplicated when two majors of the crate are linked, or per dynamic library. Fix: caller-owned state passed in (CONC-10, SEC-40)

## Testing

- **Tautological test**: `assert_eq!(CONSTANTS, [the same literals])`, or an expected value recomputed with the implementation's own logic — passes by construction and can never fail usefully. Fix: assert a property the value must satisfy (TEST-32)
- **Un-gated test hooks**: `bypass_certificate_checks()` or a secret accessor compiled into release because it sat behind no `#[cfg(feature = "test-util")]`. Fix: gate every testing affordance behind one clearly named feature (TEST-33)

## Type Safety

- **Primitive obsession**: Using bare `u32`, `String`, `f64` where a newtype would prevent misuse (mixing user_id with order_id, Celsius with Fahrenheit). Fix: newtype pattern (API-1, API-2)
- **Stringly-typed APIs**: Using `String` for values with a known set of variants. Fix: use enums

## Security

- **Hardcoded secrets**: API keys, passwords, tokens in source code or VCS. Fix: environment variables or secret managers (SEC-8)
- **Missing input validation**: Trusting external input without size limits, type checks, or sanitization. Fix: validate at system boundaries (SEC-11)
