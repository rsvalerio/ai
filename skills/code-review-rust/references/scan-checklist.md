# Rust Scan Checklist

Observable signal → rules to check. Grep for the signal; when it hits, read that rule's
one-liner in [rules-index.md](rules-index.md), then the full rule in `rules/<CATEGORY>.md`
before filing. A signal with no hits costs nothing further.

| Signal | Rules to check |
|--------|----------------|
| `unwrap` / `expect` in non-test code *(exclude `#[cfg(test)]` / `tests/` / `test-support` feature gates before counting — see ERR-5 scanning guidance)* | ERR-5, ERR-8 |
| `.clone()` in hot path or to appease borrow checker | OWN-8, PERF-3 |
| `RefCell<T>` | OWN-10, SEC-24 |
| `Arc<Mutex<T>>` around collections | CONC-1--3, CONC-7--9 |
| `Result<T, String>` or `Box<dyn Error>` in library API | ERR-1, ERR-2, ERR-10 |
| Missing `.with_context()` on `?` propagation | ERR-4 |
| `std::fs` error propagated with no path in the message | ERR-13 |
| `serde_*::from_str` on human-edited config with no field path in the error | ERR-14, SEC-11 |
| Repeated `to_str().unwrap()` / `to_string_lossy()` on the same path values | API-12 |
| `HashMap` used as a cache with no size cap, TTL, or eviction | PERF-16, SEC-33 |
| `Arc<RwLock<T>>` read on every request, replaced wholesale and rarely | CONC-1, CONC-8 |
| CLI binary with no test that runs it as a command (flags, exit codes, stderr) | TEST-31 |
| `unsafe` blocks | UNSAFE-1--5, UNSAFE-8, SEC-1--4, SEC-34--36 |
| `lazy_static!` / `once_cell::sync::Lazy` in new code | CONC-10 |
| `async-trait` macro on types that could use native async fn | ASYNC-10 |
| Log/event "follow" loop relying on async alone to block at EOF | ASYNC-14 |
| `while let Some(x) = stream.next().await { … .await }` — serial per-item async work | ASYNC-5, ASYNC-13 |
| `futures::StreamExt` and `tokio_stream::StreamExt` imported in the same module | ASYNC-13 |
| `tokio::spawn(...)` whose `JoinHandle` is discarded, or `join`ed with `JoinError` logged as "panicked" | CONC-13, CONC-6 |
| Shutdown path built on `signal::ctrl_c()` with no `SignalKind::terminate()` arm | CONC-14 |
| `broadcast` consumer that does not branch on `RecvError::Lagged` | CONC-8 |
| `timeout(...)` result collapsed with `??` / `.flatten()`, or a bare `Elapsed` propagated to callers | ASYNC-6 |
| `#[error("...: {0}")]` on a variant whose field is `#[from]` / `#[source]` | ERR-9 |
| `println!` / `eprintln!` in library or service code | READ-8 |
| Workspace crates with diverging dep versions or per-crate lint config | ARCH-11 |
| Hand-rolled date math (`is_leap_year`, month-length tables, `secs / 86_400`) | TIME-1 |
| `Local::now()` or `NaiveDateTime` persisted, logged, or serialized | TIME-2, TIME-5 |
| Datetime `+`/`-` with a fixed-length duration (`TimeDelta::days`, `chrono::Duration::days`, `time::Duration::days`, `jiff::SignedDuration`) where a calendar unit was meant (`Days`/`Months`, `jiff::Span`) | TIME-3 |
| Unchecked datetime `+` or `-` on an untrusted or unbounded operand instead of the `checked_add_*` / `checked_sub_*` forms | TIME-3, SEC-33 |
| `Utc::now()` / `SystemTime::now()` subtracted or `duration_since`d to time an operation | TIME-4 |
| `Utc::now()` / `SystemTime::now()` called inside business logic instead of injected | TIME-6, TEST-16 |
| `std::thread::sleep` in async | CONC-5 |
| Missing `tokio::time::timeout` on I/O | ASYNC-6 |
| Hardcoded secrets, weak crypto | SEC-5--10 |
| Secret-bearing type with a derived `Serialize`, or a hand-written `Debug` that reads `self.field` instead of destructuring | SEC-5, SEC-21 |
| `Path::join` / `PathBuf::push` with an externally-supplied segment | SEC-14 |
| `metadata()` / `exists()` / `is_dir()` on a path followed by an independent open, write, or delete of the same path | SEC-25 |
| `v[i]`, `&s[a..b]`, or `split_at(n)` where the index comes from parsed, deserialized, or network input | ERR-16, SEC-33 |
| `as` cast narrowing an integer, or arithmetic on untrusted operands with no `checked_*` / `saturating_*` | SEC-15 |
| Validated newtype deriving `Deserialize` with no `#[serde(try_from = "…")]` | API-2, SEC-11 |
| `#[derive(Default)]` on a type whose zero value is not a valid state (ports, capacities, timeouts) | TRAIT-4, API-2 |
| `bool` field beside an `Option` field it gates (`ssl` / `ssl_cert`) | PATTERN-1 |
| String concatenation in SQL/commands | SEC-12, SEC-13 |
| Functions >50 lines, nesting >4, params >5 | FN-1--3 |
| Identical code blocks 5+ lines | DUP-1--4 |
| Tests without assertions *(see TEST-1 scanning guidance — recognize `assert_*` helpers, `#[should_panic]`, and `Result<...>` tests before filing)* | TEST-1, TEST-11 |
| `#[ignore]` without explanation | TEST-24, TEST-26 |
| NATS `connect()` without options | NATS-1--8 |
| `pub use` duplicating a still-public path, `pub use foo::*`, or a crate `prelude` module | API-13 |
| Public item or module with no doc summary, or a `Result`/panicking/`unsafe` fn with no `# Errors`/`# Panics`/`# Safety` section | API-14 |
| Newtype over a narrower domain with a public field or an infallible constructor | API-2 |
| Builder with fallible setters, `set_x()` naming, or a public `FooBuilder::new()` | API-4 |
| Trait implemented exactly once and passed as `dyn`, or `Arc`/`Box`/`RefCell` in a public signature | API-18 |
| Associated function with no receiver doing general computation (`Type::helper(x)`) | API-17, ARCH-13 |
| `Service`/`Manager`/`Factory` type names, or names repeating their module (`foo::FooId`) | API-1 |
| `static` / `thread_local!` holding correctness-relevant state in a library | CONC-10, SEC-40 |
| `String`, `Vec`, `Box<T>`, or non-`#[repr(C)]` types passed between Rust dynamic libraries | SEC-40 |
| `catch_unwind` used to turn a panic into a `Result` or to continue in-process | ERR-15 |
| `assert!`/`panic!`/`unreachable!` with no message or with no offending value in it | ERR-11 |
| `unsafe` marked on a merely dangerous (non-UB) function, or `unsafe impl Send/Sync` to silence a bound | UNSAFE-2, UNSAFE-10 |
| `unsafe` code with no Miri run in CI | UNSAFE-10, ARCH-11 |
| Attribute macro that changes an item's kind, signature, or `async`-ness, or emits extra named types | MACRO-2 |
| Proc macro with no separate `_impl` crate, or expansion emitting `::third_party::` paths directly | MACRO-3 |
| `Vec<String>` / `String` field that is never resized after construction, in a type with many instances | PERF-18 |
| Long-lived collection built by `push` with no `with_capacity` and no `shrink_to_fit` | PERF-2, PERF-20 |
| `Arc<Config>` chains dereferenced on a hot path to read one small field | PERF-17 |
| `format!` inside a log/metric call in an inner loop | PERF-19, READ-12 |
| `tracing`/`log` call with positional `{}` formatting instead of named structured fields | READ-12 |
| Magic literal (timeout, capacity, retry count) with no named `const` and no rationale | READ-11 |
| Docs narrating design decisions, migrations, or "why we picked X over Y" | READ-13 |
| Test asserting a constant equals its own literal, or recomputing the expected value with the implementation's logic | TEST-32 |
| Mock constructor, secret accessor, or safety-check bypass not behind `#[cfg(feature = "test-util")]` | TEST-33 |
| Library performing ad-hoc I/O, clock, or entropy calls with no injection point | TEST-33, API-19, TIME-6 |
| New crate on an edition older than 2024, or a library with no `rust-version` | ARCH-17, API-15 |
| Business logic or `#[repr(C)]` types in the core crate of an FFI pair | ARCH-14 |
| Crate nested inside another crate's directory, or deps declared per-crate instead of in `[workspace.dependencies]` | ARCH-15, ARCH-11 |
| Hot `async fn` holding large values across `.await`, with no future-size test | ASYNC-15 |
| CPU-bound loop inside an `async fn` that can run past the yield threshold with no `.await` on the path, or one calling `yield_now().await` every iteration | ASYNC-8 |
| `&String`, `&Vec<T>`, `&PathBuf`, or `&Box<T>` in a function parameter | OWN-7 |
| `.clone()` or a restructured signature introduced to get past a whole-struct borrow | OWN-13, OWN-8 |
| The same `Fn`/`FnMut` bound repeated on a struct and each of its `impl` blocks | TRAIT-14, TRAIT-3 |
| `let _ = <guard-returning call>;`, or `Drop` relied on for durable cleanup | PATTERN-9 |
| `select!` arm calling `read_exact`/`read_to_end`/`read_to_string`/`write_all`/a multi-step local `async fn`, or one of those constructed inside the arm of a loop rather than pinned outside it | ASYNC-16, ASYNC-12 |
| Threads spawned with `'static` clones for a fan-out that joins before the function returns | CONC-15, PERF-10 |
| Crate with no `unsafe` and no `unsafe_code = "forbid"` in its lints table | UNSAFE-12, ARCH-11 |
| User-controlled value reaching `Command::arg` with no leading-dash rejection or `--` separator | SEC-13 |
| `with_capacity`/`read_to_end` sized from a parsed length, or a size limit applied only before decompression | SEC-33 |
| `canonicalize` used to validate a path that does not exist yet | SEC-14 |
| `Regex::new` on a user-supplied pattern (no `RegexBuilder` size limits), or inside a loop | SEC-16, CONC-10 |
| New `build.rs` or proc-macro crate in a lockfile diff, or CI building without `--locked` | SEC-27, SEC-28 |
| Concurrency primitive implemented by hand (custom lock, lock-free queue, explicit `Ordering`) with no `loom` test | TEST-35, CONC-9 |
| `Box<dyn Trait>` built only to unify two branches of an `if`/`match` in a `let` | PATTERN-10 |
| Field or getter returning `Option<T>` that some call sites know is always `Some` | PATTERN-1, API-2 |
| Fallible function consuming an argument whose error carries no way to get it back | API-21 |
| Generic parameter or `Send`/`Sync`/`Clone`/`'static` bound the body never needs, or a signature that grew `&str` → `impl AsRef<str>` → multi-bound generic | API-18, ARCH-6 |
| Trait, enum, or type parameter added for a second implementation that does not exist yet | ARCH-6, TRAIT-9, API-18 |
| Crate whose standard use requires a builder or option selection first, with no one-call convenience entry point | API-22, API-4 |
| Lifetime parameter, `Cow`, arena, or `unsafe` introduced to remove an allocation on a startup, config, or error path | PERF-3, PERF-6 |
| `#![deny(warnings)]` in a crate root | ARCH-18, ARCH-11 |
| `.as_ptr()` on a `CString` temporary whose pointer the callee retains or writes through, or hand-rolled `strlen`/`copy_nonoverlapping` string conversion | SEC-41 |
| Exported `*mut` handle borrowed from another handle, or `transmute` to `'static` at an FFI boundary | SEC-42, SEC-24 |
| `///` example that defines a helper `fn` and asserts inside it | TEST-34, TEST-1 |
| JetStream without resource limits | NATS-9--14 |
