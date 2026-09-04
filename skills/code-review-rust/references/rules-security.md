# Security Rules

## Security: Memory Safety (typical severity: Critical)

- **SEC-1.** No use-after-free, double-free, or data races (safe Rust prevents these at compile time; verify unsafe blocks and atomic orderings manually)
- **SEC-2.** Validate all raw pointer dereferences; document safety invariants
- **SEC-3.** No bad `transmute`; prefer safe casts (`as`, `From`/`Into`)
- **SEC-4.** Verify `Send`/`Sync` bounds on types shared across threads

**Detection heuristics** — search for: raw pointer dereferences without bounds checking or null validation, `std::mem::uninitialized()` (deprecated, use `MaybeUninit`), use-after-free patterns and double-free risks, missing `Send`/`Sync` bounds on types crossing thread boundaries, `transmute` between incompatible types without validation, dangling references in unsafe blocks.

> SEC-1--4 own the **security** angle of unsafe code. UNSAFE-1--8 cover the **idiomatic** angle. When both apply, use a single finding under the SEC prefix and note idiomatic concerns in the Notes section.

## Security: Secrets & Crypto (typical severity: High--Critical)

**Detection heuristics** — search for: hardcoded strings matching key/password/token patterns, `Debug` derive on types containing secrets, missing `zeroize`/`secrecy` crate usage for sensitive data, weak algorithms (MD5, SHA1, DES, RC4) in crypto contexts, IV/nonce reuse patterns, non-CSPRNG sources for security values.

- **SEC-5.** Secret types: disable `Debug`/`Clone`, auto-zeroize on drop
- **SEC-6.** `secrecy::Secret<T>` prevents logging/copying secrets
- **SEC-7.** Constant-time comparisons for sensitive data (use `subtle::ConstantTimeEq` from the `subtle` crate)
- **SEC-8.** No hardcoded keys, passwords, tokens, or NKey seeds in source or VCS; use environment variables or secret managers
- **SEC-9.** No weak algorithms (MD5/SHA1/DES) for cryptographic or security purposes; use modern alternatives (SHA-256+, AES, ChaCha20). Use AEAD modes (AES-GCM, ChaCha20-Poly1305) for authenticated encryption — unauthenticated encryption without HMAC is a finding. For password hashing/key derivation, use Argon2, scrypt, or PBKDF2. Non-security uses of SHA1 (e.g., content-addressable storage, git interop) are acceptable when clearly documented. **Common crypto antipatterns**: (1) IV/nonce reuse across encryptions (breaks CBC, CTR, GCM security), (2) weak password hashing (bcrypt with cost <10, plain SHA-256), (3) unauthenticated encryption (AES-ECB, CBC without HMAC), (4) non-CSPRNG for secrets (see SEC-10)
- **SEC-10.** Prefer the OS-entropy RNG for key generation, security tokens, and any cryptographic use. **Name by `rand` version**: on `rand` ≤ 0.9 this is `OsRng` (`rand::rngs::OsRng`); on `rand` 0.10+ `OsRng` was **renamed to `SysRng`** (`rand::rngs::SysRng`, re-exported from `getrandom`) — fill via `rand::TryRng::try_fill_bytes(&mut SysRng, &mut buf)` (fallible: OS entropy can fail), or call `getrandom::fill(&mut buf)` directly. A 0.10+ codebase referencing `OsRng` will not compile. For non-cryptographic unpredictable randomness (shuffling, jitter), use `rand::rng()` on `rand` 0.9+ (current default) or the legacy `thread_rng()` on 0.8 — both are CSPRNG-backed. Never use `SmallRng` or other non-CSPRNG sources for security-sensitive values. In tests, use fixed-seed RNGs for determinism (TEST-16). **Maintenance**: the `rand` API surface changes across major versions — verify names against current crate docs when auditing

## Security: Input Validation (typical severity: High--Critical)

**Detection heuristics** — search for: string concatenation in SQL/command construction, `format!` with user input in shell commands, missing size/depth limits on deserialization, unchecked `as` casts between integer types, user-controlled regex without size bounds, path operations without canonicalization or root validation.

- **SEC-11.** Validate and sanitize all external input at system boundaries using layered validation: (1) type validation — reject wrong types early, (2) range/size — enforce bounds on numeric values and collection sizes, (3) format — validate patterns, encoding, and structure, (4) business rules — domain-specific constraints (e.g., age ≥ 0, email format). When deserializing untrusted data (serde, protobuf), enforce size limits and max nesting depth, validate schema, and reject unknown fields in security-critical contexts
- **SEC-12.** Parameterized queries for SQL; no string concatenation
- **SEC-13.** Sanitize command arguments; no shell interpolation (`Command::new` over `sh -c`)
- **SEC-14.** Path traversal: canonicalize and validate paths against allowed roots
- **SEC-15.** Integer overflow: use checked/saturating arithmetic for untrusted input; audit `as` casts between integer types for truncation (e.g., `u64 as u32`); prefer `try_from`/`try_into` which return `Result` on overflow. **Critical audit detail**: Rust checks for overflow in debug mode (panics) but wraps silently in release mode by default — code that "works" in dev can overflow in production; use `checked_*`/`saturating_*`/`wrapping_*` methods to make overflow behavior explicit regardless of build profile
- **SEC-16.** ReDoS: avoid unbounded regex on user input; set size limits
- **SEC-33.** Bound resource consumption on untrusted input: enforce size limits on buffers, collections, and strings; cap iteration counts; set timeouts on operations processing external data — prevents DoS via unbounded allocations or infinite loops

## Security: Access Control (typical severity: High--Critical)

- **SEC-17.** Encode auth states in enums; compiler enforces all cases
- **SEC-18.** Check authorization at every entry point; no implicit trust
- **SEC-19.** Prevent IDOR: validate resource ownership before access
- **SEC-20.** Tenant isolation: enforce boundaries in multi-tenant systems

## Security: Information Disclosure (typical severity: High)

**Detection heuristics** — search for: `Debug` or `Display` impls that format secret fields, `tracing::info/debug/error!` or `log::` calls with connection strings or credentials, error messages returning internal paths or stack traces, `panic!` messages containing sensitive context.

- **SEC-21.** No secrets, stack traces, or internal-path details in log output, error messages returned to users, or error chains (covers both logging and error-type leakage; see also ERR-1--10 for idiomatic error handling). Map internal errors to public error types at system boundaries (ERR-7)
- **SEC-22.** No fingerprinting surface on user-facing responses: do not expose server versions (`Server:` header, banner), library versions, OS details, build hashes, or feature flags. These aid reconnaissance and CVE targeting. Fix: strip or override framework-default identifying headers; route verbose errors to structured logs, not responses
- **SEC-23.** Disable debug endpoints and verbose logging in production; gate behind explicit `cfg(debug_assertions)` or feature flags, not environment variables that can be toggled by an attacker

## Security: Concurrency (typical severity: High--Critical)

**Detection heuristics** — search for: `unsafe impl Sync` or `unsafe impl Send` (verify manually), `RefCell` in types shared across threads, file/resource check-then-use patterns (TOCTOU), inconsistent lock ordering across functions, callback or async handler code that mutates shared state without guards.

- **SEC-24.** In `unsafe impl Sync`/`Send`, verify no `RefCell<T>` is exposed across threads — `RefCell<T>` is `!Sync` by design and safe Rust prevents cross-thread use at compile time; this is only reachable via manual `unsafe impl`. Use `Arc<Mutex<T>>` or `Arc<RwLock<T>>` instead (see OWN-10 for idiomatic usage)
- **SEC-25.** TOCTOU (time-of-check-to-time-of-use) in file/resource operations: any `metadata()`/`exists()`/`access()` check followed by an independent open/read/write is racy — the filesystem can change between the two calls. Fix: perform the operation directly and handle errors (e.g., `OpenOptions::new().create_new(true).open(path)` instead of "check then create"), use `openat`/handle-based APIs where available, and prefer `std::fs::File::options()` primitives that atomically combine check and act
- **SEC-38.** Reentrancy in callbacks, signal handlers, and async state machines: state mutation during a nested/reentrant call can bypass invariants the outer call assumed (e.g., a handler that recurses into itself via an event loop, or an async task re-entering a state machine while it's still being updated). Fix: encode valid transitions as a typestate or enum-state machine and reject calls in wrong states; or install a reentrancy guard (e.g., `AtomicBool` flag set on entry, cleared on exit, with nested entry rejected or deferred); never mutate shared state while dispatching callbacks that may re-enter
- **SEC-26.** Treat deadlock as a DoS vulnerability on request-handling paths: a single attacker-triggered lock-order inversion or await-holding-guard can freeze a worker pool. Enforce a documented global lock order for locks that can be held together, prefer `try_lock`-with-backoff for optional locks, and never hold a `Mutex`/`RwLock` guard across an `.await` (see CONC-2). Audit for: (1) two locks acquired in different orders in different code paths, (2) guards held across `.await`, (3) recursive locking of non-reentrant locks

## Security: FFI (typical severity: High--Critical)

- **SEC-34.** Validate all raw pointers at FFI boundaries before dereferencing; document caller invariants ("caller must ensure buffer is initialized and valid for N bytes")
- **SEC-35.** Never use `std::mem::uninitialized()` (deprecated, instant UB); use `MaybeUninit` instead
- **SEC-36.** Audit FFI bindings for correct nullability, lifetime, and ownership transfer semantics; verify function signatures match C expectations (ABI, calling convention, signedness)
- **SEC-39.** Treat every exported symbol as global namespace. `#[unsafe(no_mangle)]` publishes a function or static under its bare Rust name, so two crates in one link unit that both export `init` collide — either a link error or, with dynamic linking and symbol interposition, the wrong function silently wins. Review checks: (1) prefix exported names with the crate or project (`#[unsafe(export_name = "mylib_init")]`) rather than relying on a bare `#[unsafe(no_mangle)]` for anything generically named; (2) exported functions must declare an explicit ABI (`pub extern "C" fn`) — the default Rust ABI is unstable and calling it from C is UB; (3) panics must not escape across the boundary — since Rust 1.71 an unwind out of `extern "C"` aborts the process rather than being UB, which turns a recoverable error into a crash, so wrap fallible bodies in `std::panic::catch_unwind` and convert to an error code, or use `extern "C-unwind"` when the foreign caller genuinely expects to propagate unwinding. Both attributes require the `unsafe(...)` wrapper in the 2024 edition (UNSAFE-7)

**FFI audit checklist**: For each FFI boundary, verify: (1) all returned raw pointers null-checked before deref, (2) caller invariants documented on every `unsafe fn`, (3) no `std::mem::uninitialized()` (use `MaybeUninit`), (4) ownership transfer semantics clear (who frees?), (5) lifetime validity of pointers across calls, (6) exported symbols namespaced and panic-safe (SEC-39)
- **SEC-40.** Across a boundary between two Rust dynamic libraries (or between a DLL and its host), only **portable** data may be exchanged — a strict subset of FFI-safe. rustc compiles each dynamic library as an independent artifact: every one gets its own copy of every `static` and `thread_local!` (CONC-10), its own `TypeId` values, and its own layout for any `#[repr(Rust)]` type, which is unspecified and free to differ between two compilations of the same source. Passing a `String`, `Vec<u8>`, `Box<T>`, or any non-`#[repr(C)]` struct between two such libraries is therefore undefined behaviour in practice, not just in theory — the receiver reads a different layout than the sender wrote, and freeing an allocation made by the other library's allocator corrupts the heap. So is anything routed through a `TypeId` (`dyn Any` downcasts, type-keyed registries), and anything that touches a runtime relying on statics (`tokio`, `log`, `tracing` subscribers) on the far side. Portable means `#[repr(C)]` (or otherwise layout-guaranteed) **and** no interaction with any static, thread-local, or `TypeId`, **and** containing no pointer or reference into non-portable data. Note the trap the signature hides: a `&CommonService` argument is UB if any type nested inside it differs in layout, and a method called on it *appears* to execute in the callee's library while actually running the caller's code against the callee's data — mixing one library's statics with the other's state. Cross-library sharing must go through a C ABI with owned, `#[repr(C)]` message types and per-library allocation/free entry points (SEC-39, ARCH-14)

## Security: Dependencies (typical severity: High)

- **SEC-27.** Review unmaintained or abandoned dependencies; check for known vulnerabilities; vet dependency source trustworthiness (unverified registries, unknown maintainers, weak security track record). Run `cargo audit` (RustSec advisory database) in CI to detect known CVEs in the dependency tree; combine with `cargo outdated` to surface stale dependencies before they reach end-of-life
- **SEC-28.** Pin dependency versions; ensure `Cargo.lock` is committed (missing lockfile allows silent dependency drift); audit lockfile changes in PRs; consider `cargo-deny` for license and security policy enforcement

## Security: Configuration (typical severity: High)

- **SEC-29.** Secure defaults: TLS enabled, auth required, debug disabled; verify configuration file permissions are not world-readable
- **SEC-30.** Validate configuration at startup; fail fast on insecure settings; implement secret rotation mechanisms and key expiration where applicable

## Security: Error Handling (typical severity: High)

- **SEC-31.** No security bypass on error; fail closed
- **SEC-32.** Ensure cleanup of sensitive resources on error paths

## Security: Testing & Verification (typical severity: Medium--High)

- **SEC-37.** Fuzz security-critical parsing and deserialization code with fuzzing tools; prioritize code that handles untrusted input, protocol parsing, and format conversion
