# rust-meta Evaluation — Baseline refresh, Rust 1.87 → 1.98

**Date**: 2026-09-29
**Source**: Rust release notes 1.88.0–1.98.1 ([RELEASES.md](https://raw.githubusercontent.com/rust-lang/rust/master/RELEASES.md), [releases.rs](https://releases.rs/), the 1.95 announcement); crates.io API and upstream Cargo.toml / CHANGELOG for `jiff`, `time`, `chrono`, `hashbrown`, `dashmap`, `async-std`; RUSTSEC-2025-0052; [owasp.org/Top10](https://owasp.org/Top10/)
**Target skill**: `code-review-rust` (plus `rust-meta`'s own baseline)
**Task**: TASK-0009

## Executive Summary

| Metric | Count |
|--------|-------|
| Knowledge pieces extracted | 45 |
| Approved & integrated | 24 |
| Rejected | 14 (plus ~40 release-note items dropped at extraction as trivia, compiler-enforced or platform-specific) |
| Needs clarification | 7 |

**Overall assessment**: eleven releases, but the corpus had already absorbed some of them (VER-1 at 1.92, VER-9 and TEST-29 at 1.96), so the refresh was as much correction as addition. It found **three wrong statements**:

- TEST-29's import path `std::assert_matches::assert_matches` does not compile on stable (E0432).
- VER-9 dated `RangeInclusive` one release late.
- PERF-8 said `hashbrown`'s `HashMap` reaches `ahash` and that `DashMap` uses it. Neither is true now.

It also found two **stale ecosystem claims**: `async-std` offered as a live runtime although it is discontinued, and the OWASP note waiting for a 2025 list that has since been published.

Additions are mostly **std APIs that remove a panic or a dependency**: `floor_char_boundary`, `array_windows`, `as_chunks`, `as_array`, `push_mut`, `pop_front_if`, `strict_*`, `cfg_select!` (replaces `cfg-if`), `File::lock` (replaces `fs2`/`fs4`), `NumBuffer` (replaces `itoa`). Each is attached to the rule a reviewer already reaches, not added as a free-standing tip.

**Verification**: every API named in an integrated item was compiled and run on `rustc 1.98.0`, edition 2024. That includes `Atomic*::update`'s `(set_order, fetch_order, f)` argument order, `BTreeMap::extract_if`'s range argument, and `core::fmt::NumBuffer` resolving where `std::fmt::NumBuffer` does not. The four unsafe lints were checked against `rustc -W help` for name and default level. `build.warnings` was checked by running `CARGO_BUILD_WARNINGS=deny cargo build` on cargo 1.98.

**Baseline**: `rust-meta`'s ingestion baseline moves to **1.98+** (reviewed 2026-09-29). The `pre-1.85 only` reject cutoff stays at 1.85, now labelled as the 2024-edition floor that does not track the baseline. Moving it would reject guidance usable by the many crates whose MSRV sits at 1.85 (`rand` 0.10, `getrandom` 0.4, `hashbrown` 0.17).

## Detailed Results — Corrections

| # | Rule | Was | Now | Evidence |
|---|------|-----|-----|----------|
| C1 | TEST-29 | `use std::assert_matches::assert_matches;` | `use std::assert_matches;` (crate-root macro) | E0432 on 1.98; std docs |
| C2 | VER-9 (+ index) | all three types "stable since 1.96" | `RangeInclusive` 1.95; `Range`, `RangeFrom`, `RangeToInclusive` 1.96; `std::range::legacy` 1.98 | RELEASES.md 1.95/1.96/1.98 |
| C3 | PERF-8 (+ index) | "`ahash` via `HashMap` from `hashbrown`", "used by `DashMap`" | `foldhash` is hashbrown's default since 0.15; DashMap claim dropped | hashbrown 0.17.1 Cargo.toml (`default-hasher = ["dep:foldhash"]`); dashmap 6.2.1 deps |
| C4 | FN-2, CL.md deep-nesting | let-chains "stable in Rust 2024" | since 1.88, edition 2024 only; CL now offers the let-chain form too | RELEASES.md 1.88 |
| C5 | ASYNC.md header, flakiness-patterns.md | `async-std` as an alternative runtime | discontinued; a project on it is a SEC-27 finding | RUSTSEC-2025-0052 |
| C6 | owasp-2021.md note | "no final 2025 ranking has been published" | 2025 list is published; mapping pending migration (new backlog task) | owasp.org/Top10 → top10.owasp.org/2025 |
| C7 | TIME-1 | "pre-1.0, so expect breaking minor releases" | 0.2.x releases are semver-compatible; the breaking step is 0.2 → 1.0 | jiff README, issue #622 |

## Detailed Results — Approved additions

| # | Release | Item | Target | Status |
|---|---------|------|--------|--------|
| A1 | 1.91 | `str::floor_char_boundary` | ERR-16 | Approved: fills the missing String-specific fix |
| A2 | 1.94 / 1.88 / 1.93 | `array_windows`, `as_chunks`, `as_array` | ERR-16 | Approved: removes indexing and `try_into().unwrap()` |
| A3 | 1.95 / 1.93 | `Vec::push_mut`, `VecDeque::pop_front_if` | ERR-5 | Approved: replace, don't downgrade, the infallible unwrap |
| A4 | 1.91 / 1.90 | `strict_*`; `checked_sub_signed` | SEC-15 | Approved: fourth intent choice, per call site |
| A5 | 1.91 / 1.88–1.89 | `integer_to_ptr_transmutes`, `dangling_pointers_from_locals`, `invalid_null_arguments`, `dangerous_implicit_autorefs` | SEC-3 (+ index) | Approved: an `allow` of these is a finding |
| A6 | 1.95 | `cfg_select!` | PATTERN-8 | Approved: replaces `cfg-if` |
| A7 | 1.95 | `core::hint::cold_path` | PERF-14 | Approved: in-place cold hint |
| A8 | 1.95 | `if let` guards | FN-2 | Approved: small; exhaustiveness caveat stated |
| A9 | 1.97 | `build.warnings` / `CARGO_BUILD_WARNINGS` | ARCH-18 | Approved: preferred over `RUSTFLAGS="-D warnings"` (no fingerprint churn) |
| A10 | 1.98 | stricter `repr(transparent)` trivial fields | API-2 | Approved: `repr(C)` ZST rejection compile-verified; cross-crate case from the release note |
| A11 | 1.91 | `BTreeMap`/`BTreeSet::extract_if`, lazy-drop trap | VER-6 (+ index) | Approved |
| A12 | 1.95 | `Atomic*::update` / `try_update` | VER-10 (new) | Approved |
| A13 | 1.93 | `fmt::from_fn` | VER-11 (new) | Approved |
| A14 | 1.89 | `File::lock` family | VER-12 (new) | Approved: replaces `fs2`/`fs4`/`fd-lock`; drop-unlock trap via PATTERN-9 |
| A15 | 1.98 | `bool::ok_or` / `ok_or_else` | VER-13 (new) | Approved |
| A16 | 1.98 | `format_into` + `core::fmt::NumBuffer` | VER-14 (new) | Approved: replaces `itoa`; `core::fmt` path noted |
| A17 | — | TIME-1 figures: jiff 0.2.37 / MSRV 1.70, time 0.3.55 / 1.88, chrono 0.4.45 / 1.62; `time` 0.3.54 `Duration` → `SignedDuration` | TIME-1 | Approved: figure refresh. **jiff promotion not triggered** (not 1.0) |

No signal rows added. VER is reached through the `## Sweep` list, and a category in both the sweep and the table fails `validate-rules`. ERR-16's existing row (`&s[a..b]` on parsed input) already covers A1–A2.

## Needs Clarification (not integrated)

- **TRAIT-4: `Ord`/`PartialOrd` consistency.** Per the 1.96/1.98 compatibility notes, `BTreeMap::append` may panic on an incorrect `Ord`, and derived `PartialOrd` takes an `Ord` fast path. The principle is sound, but the fast-path semantics were read from a one-line note and not from the PR.
- **ARCH-11: `dead_code_pub_in_binary`** (1.97, allow-by-default). How noisy it is on real workspaces is unknown.
- **SEC-39: `invalid_`/`suspicious_runtime_symbol_definitions`** (1.98). Upstream says their coverage grows over the next releases, so re-check at the next refresh.
- **SEC-36: `c_void_returns`** (1.98, warn). Real, but it already warns by default.
- **ASYNC-12: `pin!` no longer deref-coerces** (1.97). The old code now fails to compile rather than misbehaving.
- **CONC-10: `LazyLock::get`** (1.94). Probably not worth the words.
- **PATTERN-4: `Box`/`Rc`/`Arc::new_zeroed`** (1.92). Matters only for non-`Vec` owners.

## Rejected

- `Result::flatten` (1.89): already in ASYNC-6.
- `PanicHookInfo::payload_as_str` (1.91): low value.
- TRAIT-11 diagnostic-attribute lint split (1.90): a wording nicety only.
- `std::char` deprecations (1.97): only `deprecated_in_future`; check clippy's `legacy_numeric_constants` first.
- Compiler-enforced changes, where a review has nothing to add:
  - never-type fallback, `deref_nullptr`, `semicolon_in_expressions_from_macros`, `missing_fragment_specifier`, `mismatched_lifetime_syntaxes`
  - drop-order and closure-capture changes
  - ambiguous-import errors
- Build or tooling items that belong in `rust-make-build-fast`, not review rules: lld default (already in its checks), `build.build-dir`, cargo auto-GC, `include` config, `resolver.lockfile-path`.
- Niche APIs: bit-width ops, `substr_range`, `strip_circumfix`, `into_raw_parts`, `Peekable::next_if_map`, the `unchecked_*` ops, `Duration::from_mins`, `Cell::update`.

## Unverified

- Why `jiff` 0.2.36 was yanked, and what 0.2.37 changes (no CHANGELOG entry yet).
- The exact publication date of OWASP Top 10:2025.
- Rust 1.99 is expected on 2026-10-01 by the six-week cadence. The next refresh starts from 1.98.

## Updated files

- `code-review-rust/references/rules/`: `VER.md` (VER-6, VER-9 amended; VER-10–14 new), `ERR.md` (ERR-5, ERR-16), `SEC.md` (SEC-3, SEC-15), `PATTERN.md` (PATTERN-8), `PERF.md` (PERF-8, PERF-14), `ARCH.md` (ARCH-18), `TEST.md` (TEST-29), `API.md` (API-2), `FN.md` (FN-2), `CL.md`, `ASYNC.md` (header), `TIME.md` (TIME-1), `index.md`
- `code-review-rust/references/`: `flakiness-patterns.md`, `owasp-2021.md`
- `rust-meta/references/evaluation-criteria.md`: baseline 1.98+, reject cutoff labelled
