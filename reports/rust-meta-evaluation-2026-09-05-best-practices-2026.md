# rust-meta Evaluation — "Rust Best Practices 2026: Security, Idioms & Error Handling" (Corgea)

**Date**: 2026-09-05
**Source**: Corgea blog, "Rust Best Practices 2026: Security, Idioms & Error Handling" (pasted article text)
**Target skill**: `code-review-rust`

## Executive Summary

| Metric | Count |
|--------|-------|
| Knowledge pieces extracted | 38 |
| Approved & integrated | 14 |
| Rejected (already expressed) | 21 |
| Rejected (factually wrong) | 1 |
| Needs clarification | 2 |

**Overall assessment**: The article is a broad, competently written survey aimed at readers new to the topic. Against a ruleset that already carries 380+ rules across 21 prefixes, the great majority of it is **already expressed, usually in more depth than the source** — borrowing in signatures, `Cow`, `thiserror`/`anyhow`, `unwrap` policy, newtypes, parse-don't-validate, `must_use`/`non_exhaustive`, SAFETY comments, Miri, lock-across-`.await`, `spawn_blocking`, `JoinHandle` detachment, `Path::join`, integer overflow, and the crypto crate list all map to existing rules verbatim.

What it *did* contribute was concentrated in three places the existing rules had thinner coverage: **cancellation safety as a per-method property** (a genuine gap — the rules covered timeout-drops but not the `select!` arm shape), **supply-chain review scope** (`build.rs`/proc macros executing at compile time, `--locked`), and a set of **specific DoS shapes** (pre-allocation from a wire length, decompression ratio). One item was also a **correction opportunity in the other direction**: the article's generic ReDoS advice does not describe the `regex` crate, which is linear-time by construction — SEC-16 was previously terse enough to invite that false finding, and now says so explicitly.

**Rust version compatibility**: All integrated content targets current stable and the 2024 edition. Stability verified: `thread::scope` 1.63, `[lints]` table 1.74, `unsafe_op_in_unsafe_fn` default-warn in edition 2024, MSRV-aware resolver (`resolver = "3"`) implied by edition 2024. Baseline of Rust 1.87+ (evaluation-criteria.md) is satisfied throughout.

## Detailed Results — Approved

### A1. Cancellation safety is a per-method property of every `select!` arm

- **Extracted**: A future is cancellation-safe if dropping it partway loses no data. `select!` drops every losing branch. `mpsc::Receiver::recv` is safe; `read_exact` is not, because bytes already read are gone.
- **Status**: **Approved** — fills gap
- **Reasoning** (Worth Adding): ASYNC-6 covered "a timeout cancels, it does not roll back" and CONC-14 noted that losing a `select!` race drops a future, but nothing stated cancellation safety as a *property to look up per method*, nor listed which tokio methods have it. The failure mode (a stream left mid-message, every later read misaligned) is silent and hard to attribute.
- **Rust version**: current stable; tokio 1.x
- **Target**: `rules-core.md` → Async → **new ASYNC-16**
- **Modifications**: expanded well beyond the source — added the safe/unsafe method inventory (verified against tokio docs), both fixes (`pin!` outside the loop; move to a task), the "future constructed inside the arm restarts it" trap, and a scan signal. Cross-referenced ASYNC-12, ASYNC-6, CONC-8, CONC-14.

### A2. `#![forbid(unsafe_code)]` in crates that do not need `unsafe`

- **Status**: **Approved** — fills gap
- **Reasoning**: The UNSAFE section had eleven rules on *writing* unsafe correctly and none on *excluding* it. ARCH-11 lists a `[workspace.lints]` baseline that omits `unsafe_code`.
- **Target**: `rules-core.md` → Unsafe → **new UNSAFE-12**
- **Modifications**: added the `forbid`-vs-`deny` distinction the source only implied; distinguished it from the ARCH-18 `#![deny(warnings)]` anti-pattern (a reader could otherwise read the two as contradictory); added the two real costs the source omits — `forbid` applies to the crate being compiled (not to separately compiled dependency code) and so rejects `unsafe` tokens a dependency's macro expands *into* this crate, unless that macro is marked `allow_internal_unsafe`; and the `unsafe(...)` attribute wrapper edition 2024 requires on `#[no_mangle]` (UNSAFE-7).

### A3. `std::thread::scope` for borrowing stack data in threads

- **Status**: **Approved** — fills gap
- **Reasoning**: CONC-1 covered `Arc<Mutex<T>>` selection and PERF-10 covered rayon; nothing covered the middle case where `'static` is being satisfied by ceremony rather than by need.
- **Rust version**: stable since 1.63 ✓
- **Target**: `rules-core.md` → Concurrency → **new CONC-15**
- **Modifications**: added the disjoint-`chunks_mut`-needs-no-lock point, the panic-propagation-at-join caveat, and the "blocks the caller, so not from async" caveat — none of which the source mentions.

### A4. Argument injection: a leading `-` survives `Command::arg`

- **Status**: **Approved** — complements SEC-13
- **Reasoning**: SEC-13 was a single line ("no shell interpolation"). The source's observation that `.arg()` stops *command* injection but not *argument* injection is a real and commonly missed second half.
- **Target**: `rules-security.md` → SEC-13 (enhanced)
- **Modifications**: added concrete flags (`--upload-file`, `-e`, `--exec`, `-o`), the `--` separator and `./` prefix fixes, plus two surfaces the source omits: environment inheritance without `.env_clear()` (`LD_PRELOAD`, `PATH`, `IFS`, `BASH_ENV`) and `PATH` resolution of a bare program name.

### A5. `canonicalize` requires the path to exist — check the parent for paths about to be created

- **Status**: **Approved** — complements SEC-14
- **Reasoning**: SEC-14 already had strong `Path::join` coverage but assumed the target exists; the create-path case is where the check gets silently dropped or turned into a fail-open (SEC-31).
- **Target**: `rules-security.md` → SEC-14 (appended)
- **Modifications**: added the TOCTOU cross-reference to SEC-25, which the source does not make.

### A6. The `regex` crate is linear-time; classic ReDoS does not apply to it

- **Status**: **Approved** — complements *and corrects the framing of* SEC-16
- **Reasoning** (Makes Sense + Worth Adding): SEC-16 read "ReDoS: avoid unbounded regex on user input; set size limits" — terse enough that a reviewer could file a false finding against a perfectly safe `regex` matcher. The source correctly notes `regex` guarantees linear time. This is the one place the article improved an existing rule by *narrowing* it.
- **Target**: `rules-security.md` → SEC-16 (rewritten)
- **Modifications**: went well beyond the source — named the three risks that *do* apply (untrusted pattern compilation without `RegexBuilder::size_limit`/`dfa_size_limit`; recompiling in a loop, cross-referenced to CONC-10; and `fancy-regex`/PCRE/Oniguruma bindings, which *are* backtracking), and stated explicitly that recommending a rewrite for backtracking ReDoS against `regex` is a false finding.

### A7. Pre-allocation from an untrusted length

- **Status**: **Approved** — complements SEC-33
- **Reasoning**: SEC-33 said "bound resource consumption" generically. `Vec::with_capacity(hdr.count)` is the specific shape that looks bounded and is not, and it interacts with PERF-2, which recommends `with_capacity` for *trusted* sizes — worth disambiguating so the two rules do not appear to conflict.
- **Target**: `rules-security.md` → SEC-33 (expanded)
- **Modifications**: added the `read_to_end`/`Read::take(limit)` companion case.

### A8. Decompression ratio: a bounded body is unbounded after inflation

- **Status**: **Approved** — complements SEC-33
- **Target**: `rules-security.md` → SEC-33 (expanded)

### A9. Depth limits are not size limits (`serde_json`)

- **Status**: **Approved** — complements SEC-33 and SEC-11
- **Reasoning**: SEC-11 required "size limits and max nesting depth"; the source's point is sharper — `serde_json`'s default 128-depth cap satisfies the depth half automatically and bounds nothing else, so a flat 100 MB array passes.
- **Rust version**: verified against serde_json's documented default recursion limit.
- **Target**: `rules-security.md` → SEC-33 (expanded)
- **Modifications**: added the `#[serde(flatten)]`/untagged backtracking-cost note, not in the source.

### A10. `build.rs` and proc macros execute at compile time — supply-chain review scope

- **Status**: **Approved** — fills a real gap in SEC-27
- **Reasoning**: SEC-27 covered advisories and maintenance status but nothing about *when* dependency code runs. The consequence — that `cargo check` and a rust-analyzer save are enough to execute a dev-dependency's build script with CI credentials in scope — invalidates the two most common dismissals ("only a dev-dependency", "we never call it").
- **Target**: `rules-security.md` → SEC-27 (appended)
- **Modifications**: added `cargo tree`, typosquat verification (repository link, maintainer, download history — not the name alone), and `cargo vet` as the artifact that makes review reviewable.

### A11. `--locked` in CI; `cargo auditable` for deployed binaries; `deny.toml` scope

- **Status**: **Approved** — complements SEC-28
- **Reasoning**: SEC-28 required a committed lockfile, which is half the control — a lockfile every CI job silently re-resolves provides no more assurance than none.
- **Target**: `rules-security.md` → SEC-28 (appended)
- **Modifications**: enumerated the `deny.toml` axes (advisories, licenses, duplicates, wildcards, `unknown-registry`/`unknown-git` sources).

### A12. `[profile.release]`: `lto`, `codegen-units = 1`, `strip`

- **Status**: **Approved** — complements PERF-21
- **Reasoning**: PERF-5 mentioned LTO only as context for `#[inline]`, and PERF-21 covered allocator and `target-cpu` but not the profile itself.
- **Target**: `rules-core.md` → PERF-21 (appended)
- **Modifications**: linked back to PERF-5 (LTO is what makes cross-crate `#[inline]` unnecessary), kept the source's correct "leave `panic = \"unwind\"` alone" point with the CONC-13 reason attached, noted `debug = 1` as the alternative to `strip` where the binary is symbolicated in production, and cross-referenced SEC-15 for `overflow-checks`.

### A13. `cargo llvm-cov` and `cargo nextest`

- **Status**: **Approved** — TEST-27 enhanced (llvm-cov), **new TEST-36** (nextest)
- **Reasoning**: TEST-27 recommended `cargo tarpaulin`/`grcov`; `cargo llvm-cov` is the current default choice and TEST-27 was stale. `nextest` earned its own rule because process-per-test changes what the suite can *catch* (aborts attributed to the right test; shared-`static` cross-talk eliminated, TEST-18/CONC-10), not only how fast it runs.
- **Target**: `rules-tests.md`
- **Modifications**: added the two limits the source omits — nextest does not run doctests (TEST-34 still needs `cargo test --doc`), and per-process startup makes a suite of very many trivial tests slower.

### A14. `loom` for concurrent data structures

- **Status**: **Approved** — fills gap
- **Reasoning**: The rules had Miri (UNSAFE-10, ARCH-11) and property testing (TEST-9) but nothing on interleaving coverage; CONC-9 discusses explicit atomic orderings with no corresponding verification tool.
- **Target**: `rules-tests.md` → **new TEST-35**
- **Modifications**: added the scoping the source omits — loom tests must be *minimal* models because the state space is exponential, it is complementary to Miri rather than a substitute ("Miri finds UB along one execution, loom finds the execution"), and code that merely *uses* `Mutex`/`mpsc` does not need it.

## Detailed Results — Rejected (already expressed)

| # | Extracted content | Already expressed |
|---|-------------------|-------------------|
| R1 | rustfmt/Clippy in CI; `[lints]` table; `[workspace.lints]` | ARCH-11 (with a far more specific lint baseline, incl. a second restriction tier) |
| R2 | `rust-version` MSRV, test against MSRV in CI | API-15, ARCH-17 |
| R3 | Workspace layout; `[workspace.dependencies]` | ARCH-11, ARCH-15 |
| R4 | `&str`/`&[T]`/`&Path` in signatures | OWN-7 (which also covers the `impl AsRef` and `&Box<T>` cases) |
| R5 | Treat `clone` as a design decision | OWN-8, PERF-3 |
| R6 | `Cow` for conditional ownership | OWN-4 |
| R7 | Return `Result`, propagate with `?` | ERR-1 |
| R8 | `thiserror` for libraries, `anyhow` for applications; do not expose `anyhow` from a library API | ERR-3, ERR-7, ERR-10 |
| R9 | No `unwrap` in libraries or on untrusted paths | ERR-5 (with the test-module scanning filter the source lacks) |
| R10 | Have a panics policy; `panic = "abort"`; `catch_unwind` belongs at FFI boundaries | ERR-11, ERR-15, CONC-13 |
| R11 | Newtypes for domain identifiers (the IDOR argument) | API-1, API-2, SEC-19 |
| R12 | Parse, don't validate; private inner field | API-2 (incl. the derived-`Deserialize` bypass the source misses) |
| R13 | Enums instead of booleans | PATTERN-1, anti-patterns "correlated flag beside its payload" |
| R14 | Builders; typestate for ordered construction | API-4, PATTERN-1 |
| R15 | `#[must_use]` and `#[non_exhaustive]` | API-5, API-9 |
| R16 | Small `unsafe` blocks; `// SAFETY:` comments; safe wrappers; `unsafe fn` contracts | UNSAFE-1, UNSAFE-2, UNSAFE-5 |
| R17 | Run Miri | UNSAFE-10, ARCH-11 |
| R18 | `Send`/`Sync`; do not `unsafe impl Send`; channels vs. shared state | TRAIT-13, SEC-4, CONC-1, CONC-3, CONC-8 |
| R19 | Tokio: no `std` mutex across `.await`; `spawn_blocking`; dropped `JoinHandle` detaches; timeout everything | CONC-2, CONC-5, ASYNC-1, CONC-13, ASYNC-6 |
| R20 | Allowlist over denylist input validation; `deny_unknown_fields`; secrets (`secrecy`, `zeroize`, `subtle`); vetted crypto (`OsRng`, argon2, rustls) | SEC-11, SEC-5, SEC-6, SEC-7, SEC-9, SEC-10 |
| R21 | Integer overflow wraps in release; `overflow-checks`; `checked_`/`saturating_`/`wrapping_`; `try_from` over `as` | SEC-15 (materially more detailed) |
| R22 | Unit/integration/doc tests; proptest; cargo-fuzz | TEST-1, TEST-9, TEST-34, SEC-37 |
| R23 | Avoid allocation in hot loops; profile with criterion/flamegraph first | PERF-1, PERF-2, PERF-6, PERF-11 |
| R24 | FFI: validate pointers/lengths, `CStr::to_str` is fallible, no unwind into C, bindgen/cxx | SEC-34, SEC-36, SEC-39, SEC-41, ARCH-14 |

## Rejected (factually incorrect)

### R25. "Since Rust 1.81, a panic escaping an `extern "C"` function aborts the process"

- **Status**: **Rejected** — Still Valid fails
- **Reasoning**: The abort-on-unwind behaviour for `extern "C"` (and the stabilization of `extern "C-unwind"`) landed in **Rust 1.71**, not 1.81. The existing SEC-39 already states 1.71 correctly. No change made; recorded here so a future ingestion of the same claim is not treated as new.

## Needs Clarification

### C1. `cargo geiger` for counting `unsafe` across the dependency tree

- **Makes Sense**: yes in principle — an `unsafe`-density signal for deciding which dependencies deserve a closer read.
- **Still Valid**: **uncertain**. The crate's maintenance activity has been intermittent and it has historically broken against newer cargo metadata formats. The rules already get most of this value from UNSAFE-12 (crates that forbid `unsafe` are self-declaring) and SEC-27.
- **Question for the user**: is a dependency-tree `unsafe` census something your review process would act on? If so, confirm `cargo-geiger` still builds against current stable before it goes into a rule; otherwise this stays out.

### C2. Article's `strip_bom` `Cow` example

- The source's example returns `Cow::Borrowed` in **both** match arms, so it demonstrates nothing about conditional ownership (its `escape_html` example, immediately following, is correct). Not integrated; OWN-4 already covers the pattern. Noted only as a signal about the source's example-checking rigor — the other code samples in the article were spot-checked and are sound.

## Updated Files

| File | Change |
|------|--------|
| `skills/code-review-rust/references/rules-core.md` | **New**: CONC-15 (scoped threads), ASYNC-16 (cancellation safety), UNSAFE-12 (`forbid(unsafe_code)`). **Enhanced**: PERF-21 (release profile) |
| `skills/code-review-rust/references/rules-security.md` | **Enhanced**: SEC-13 (argument injection, env/`PATH` inheritance), SEC-14 (`canonicalize` on non-existent paths), SEC-16 (rewritten — `regex` is linear-time), SEC-27 (compile-time execution of build scripts/proc macros), SEC-28 (`--locked`, `cargo auditable`, `deny.toml` scope), SEC-33 (pre-allocation, decompression ratio, depth≠size) |
| `skills/code-review-rust/references/rules-tests.md` | **New**: TEST-35 (`loom`), TEST-36 (`cargo nextest`). **Enhanced**: TEST-27 (`cargo llvm-cov`) |
| `skills/code-review-rust/references/anti-patterns.md` | 10 new scan signals across Async & Concurrency, Security, and Build Configuration |
| `skills/code-review-rust/SKILL.md` | 9 new rows in the scan-signal table |

Rule-ID sequences after this run: ASYNC→16, CONC→15, UNSAFE→12, TEST→36. SEC and PERF unchanged (enhancements only).
