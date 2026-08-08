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

## Type Safety

- **Primitive obsession**: Using bare `u32`, `String`, `f64` where a newtype would prevent misuse (mixing user_id with order_id, Celsius with Fahrenheit). Fix: newtype pattern (API-1, API-2)
- **Stringly-typed APIs**: Using `String` for values with a known set of variants. Fix: use enums

## Security

- **Hardcoded secrets**: API keys, passwords, tokens in source code or VCS. Fix: environment variables or secret managers (SEC-8)
- **Missing input validation**: Trusting external input without size limits, type checks, or sanitization. Fix: validate at system boundaries (SEC-11)
