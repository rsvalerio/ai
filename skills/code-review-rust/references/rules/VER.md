# VER rules

## Version-Specific Features (typical severity: Low)

> **Maintenance note**: Verify version-specific claims against [Rust release notes](https://releases.rs/) before adopting. Incorrect version tags mislead MSRV decisions. Features listed below were verified against release announcements; re-check if your toolchain differs.

- **VER-1.** `RwLockWriteGuard::downgrade()` (stable since Rust 1.81): converts write lock to read lock atomically; use when you need to modify data then continue reading without releasing the lock — prevents other writers from jumping in; check project MSRV before adopting
- **VER-4.** `Mutex::clear_poison` and `RwLock::clear_poison` (stable since Rust 1.84): explicitly reset a poisoned lock after recovering from a panic, instead of unwrapping `PoisonError` or recreating the lock. Use when a lock's invariant is re-established by a recovery path; check project MSRV before adopting
- **VER-5.** Async closures with `AsyncFn`/`AsyncFnMut`/`AsyncFnOnce` traits (stable since Rust 1.85): prefer `async || {}` over `|| async {}` workarounds — the latter captures borrows incorrectly; see also ASYNC-11; check project MSRV before adopting
- **VER-6.** `HashMap`/`HashSet` expose `extract_if` (stable since Rust 1.87): drain entries matching a predicate in-place without collecting; replaces `retain` + side-effect patterns; check project MSRV before adopting
- **VER-7.** `ptr::fn_addr_eq` (stable since Rust 1.85): compare function pointers for equality by address without `as usize` casts; prefer over manual casting; check project MSRV before adopting
- **VER-8.** `NonZero<T>` unified generic (stable since Rust 1.79): replaces individual `NonZeroU8`, `NonZeroU32`, etc. with a single generic. The individual aliases remain but `NonZero<u32>` is preferred in new code; check project MSRV before adopting
- **VER-9.** `core::range` Copy range types (stable since Rust 1.96): `core::range::Range`, `RangeFrom`, `RangeInclusive` implement `IntoIterator` instead of `Iterator`, so the range value is plain `Copy` data — store it in a struct or capture it by value without splitting into `start`/`end` or cloning. Use when a range needs to live in `Copy`/`#[derive(Clone, Copy)]` state. **Caveat:** range *literal* syntax (`0..5`) still produces the legacy `std::ops::Range` (which is not `Copy`) in the 2024 edition — you must construct `core::range::Range { start, end }` explicitly to get the `Copy` type; literal migration is deferred to a future edition. Check project MSRV before adopting
