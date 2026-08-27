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

## Async & Concurrency

- **Blocking in async**: `std::thread::sleep`, synchronous I/O, or CPU-heavy work on the async executor — starves other tasks. Fix: `tokio::time::sleep`, `tokio::fs`, `spawn_blocking` (CONC-5)
- **Lock held across `.await`**: Holding `Mutex`/`RwLock` guard across an await point — can cause deadlock or long lock hold times. Fix: drop the guard before `.await`, or restructure to separate the locked section (CONC-2)
- **Unbounded channels/queues**: Producer fills memory when consumer is slow. Fix: use bounded channels with backpressure (ASYNC-3, CONC-3)
- **Async mistaken for "waits at EOF"**: a `tokio::fs` line reader used to tail a growing log — it hits EOF and exits just like `std::fs`, so the follower silently stops on the first quiet moment. Fix: offset-tracking re-poll, `notify`, or the log transport (ASYNC-14)
- **Serial work inside a stream loop**: `while let Some(x) = s.next().await { work(x).await }` processes one item at a time no matter how many are ready. Fix: `buffer_unordered` / `for_each_concurrent` with an explicit concurrency limit (ASYNC-5, ASYNC-13)
- **Fire-and-forget `tokio::spawn`**: the `JoinHandle` is dropped, so a panicking background task takes its work down while the process keeps reporting healthy and still exits 0. Fix: `JoinSet` and drain `join_next()`, or await the handle and split `JoinError` into `is_panic()` vs `is_cancelled()` (CONC-13, CONC-6)
- **Shutdown path that only hears Ctrl-C**: `signal::ctrl_c().await` as the whole shutdown story — SIGTERM, which is what containers and systemd send, kills the process before any cleanup runs. Fix: `select!` over `ctrl_c()` and `SignalKind::terminate()`, propagate via `CancellationToken`/`watch`, bound the drain with a timeout (CONC-14)
- **`Lagged` swallowed on a broadcast receiver**: `RecvError::Lagged(n)` is `n` messages permanently lost, and `recv()` keeps working afterwards — `?`-ing or log-and-continue reports healthy while dropping data. Fix: handle it distinctly from `Closed` — resync, resize, or fail loudly (CONC-8)
- **Source duplicated into the error message**: `#[error("failed: {0}")]` on a variant that also carries `#[from]` — every chain printer says the cause twice. Fix: the message describes this layer; the chain supplies the cause (ERR-9)
- **`Stream` treated as push-based**: assuming a stream hands items to the consumer on its own. `poll_next` is a *pull*, identical in shape to `Iterator::next` — nothing advances without a consumer polling. Fix: use `Sink`/`broadcast`/callbacks when the producer must drive (ASYNC-13)

## Date & Time

- **Hand-rolled calendar math**: manual month-length tables, `year % 4` leap-year checks, or `secs / 86_400` date derivation — wrong at century years, month boundaries, and DST. Fix: use `chrono`/`jiff` (TIME-1)
- **Naive or local timestamps crossing a boundary**: `Local::now()` or a `NaiveDateTime` persisted, logged, or serialized — the value means something different on every host. Fix: UTC everywhere, `Local` only at display, RFC 3339 on the wire (TIME-2, TIME-5)
- **Wall clock as a stopwatch**: `Utc::now() - start` or `SystemTime::now().duration_since(start)` to measure elapsed time — NTP adjustments can make it negative or fail the `duration_since`. Fix: `Instant::elapsed()` (TIME-4)

## Type Safety

- **Primitive obsession**: Using bare `u32`, `String`, `f64` where a newtype would prevent misuse (mixing user_id with order_id, Celsius with Fahrenheit). Fix: newtype pattern (API-1, API-2)
- **Stringly-typed APIs**: Using `String` for values with a known set of variants. Fix: use enums

## Security

- **Hardcoded secrets**: API keys, passwords, tokens in source code or VCS. Fix: environment variables or secret managers (SEC-8)
- **Missing input validation**: Trusting external input without size limits, type checks, or sanitization. Fix: validate at system boundaries (SEC-11)
