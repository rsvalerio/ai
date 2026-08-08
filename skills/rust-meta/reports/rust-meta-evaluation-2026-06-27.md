# Rust Meta Evaluation — 2026-06-27

**Source:** "You're Doing Async Rust Wrong in 2026 — Rust 1.96 Proves It" by Ashish Sharda (Medium, 2026-06-18).
**Topics:** async closures (`AsyncFn`/`AsyncFnMut`/`AsyncFnOnce`), Rust 2024 edition migration, `core::range` Copy ranges, `assert_matches!`.

## Executive Summary

- **Extracted:** 9 discrete pieces
- **Approved:** 3 (2 new rules, 1 enhancement)
- **Rejected:** 6 (already expressed / superseded by existing coverage / not-yet-stable)
- **Needs clarification:** 0
- **Rust version compatibility:** Article's two headline version claims (Rust 1.96 `core::range` Copy types and `assert_matches!` stabilization) were **verified against the official Rust 1.96.0 release blog** (2026-05-28) — both genuinely stable. The article's framing that range *literals* now yield Copy types is **incorrect**; literals still produce legacy `std::ops::Range`. Correction baked into the integrated rule.
- **Overall:** Most of the article duplicates existing async-closure coverage (ASYNC-11, VER-5). Real new value is confined to the two 1.96 features plus a `Send`-bound nuance for async closures.

## Detailed Results

### 1. Async closures `async || {}` with `AsyncFn` family (Rust 1.85) — REJECTED

- **Already expressed:** ASYNC-11 and VER-5 both cover this, including the `|| async {}` borrow-capture pitfall the article raises.
- **Criterion failed:** Worth Adding (duplicate).

### 2. `AsyncFn` ⊃ `AsyncFnMut` ⊃ `AsyncFnOnce` hierarchy — APPROVED (merged into enhancement #4)

- **Makes Sense:** yes; **Still Valid:** yes (1.85+).
- Marginal on its own, but folded into the ASYNC-11 enhancement as the "accept the least-restrictive bound" guidance.

### 3. Borrowing captured variables across `.await` — REJECTED

- **Already expressed:** VER-5 already states `async || {}` is preferred because `|| async {}` "captures borrows incorrectly." Article adds narrative but no new actionable rule.
- **Criterion failed:** Worth Adding (too similar).

### 4. `AsyncFn` `Send`-bound gotcha for `tokio::spawn` — APPROVED (enhancement)

- **Makes Sense:** yes — the `AsyncFn`-family `Send` story is genuinely incomplete; spawning on a multi-thread runtime needs an explicit `Fut: Future + Send + 'static` bound or `async move`.
- **Still Valid:** yes (current as of 1.96).
- **Worth Adding:** complements ASYNC-11 / ASYNC-10 with a practical caveat not previously stated.
- **Target:** ASYNC-11 (rules-core.md) — enhanced in place.

### 5. `core::range` Copy range types (Rust 1.96) — APPROVED (new rule VER-9)

- **Makes Sense:** yes — `Copy` ranges removable the `start`/`end` split when storing ranges in structs/captures.
- **Still Valid:** verified stable in Rust 1.96.0 (release blog 2026-05-28).
- **Worth Adding:** fills a gap; no existing VER rule covers it.
- **Modification:** corrected the article's claim that range literals produce Copy types — they still yield `std::ops::Range`; explicit `core::range::Range { .. }` construction required. Caveat included in the rule.
- **Target:** VER-9 (rules-core.md, Version-Specific Features).

### 6. `assert_matches!` / `debug_assert_matches!` (Rust 1.96) — APPROVED (new rule TEST-29)

- **Makes Sense:** yes — better failure messages (`Debug` of actual value) than `matches!` + `assert!`.
- **Still Valid:** verified stable in Rust 1.96.0; not in prelude, manual import `use std::assert_matches::assert_matches;`.
- **Worth Adding:** fills a testing-assertion gap; extends TEST-11; lets projects drop the third-party `assert_matches` crate at MSRV ≥ 1.96.
- **Target:** TEST-29 (rules-tests.md, Test Assertions & Quality).

### 7. `cargo fix --edition` + `edition = "2024"` migration — REJECTED

- **Already expressed:** EDITION-5 ("apply edition migration fixes before updating `edition = \"2024\"`") and the EDITION-1..5 reference block.
- **Criterion failed:** Worth Adding (duplicate).

### 8. `run_parallel` higher-order `Fn -> Fut + Send + Sync + 'static` pattern — REJECTED

- **Already expressed:** covered by ASYNC-10 (Send-bounded futures), CONC-6 (`JoinSet`/structured concurrency), and now ASYNC-11's enhanced `Send` caveat. The generic example adds no new rule.
- **Criterion failed:** Worth Adding (overlap).

### 9. `gen` blocks / `AsyncIterator` future features — REJECTED

- **Still Valid:** not stable (nightly / reserved keyword only). EDITION-1 already records that `gen` is a reserved keyword.
- **Criterion failed:** Still Valid (not stable); speculative.

## Summary

**Approved (integrated):**

- ASYNC-11 (enhanced) — async-closure trait hierarchy + `Send`-bound caveat → `rules-core.md`
- VER-9 (new) — `core::range` Copy range types (Rust 1.96), with literal caveat → `rules-core.md`
- TEST-29 (new) — `assert_matches!`/`debug_assert_matches!` (Rust 1.96) → `rules-tests.md`

**Rejected:** async closures basics (ASYNC-11/VER-5 dup); borrow-across-await (VER-5 dup); edition migration (EDITION-5 dup); `run_parallel` Send pattern (ASYNC-10/CONC-6 overlap); `gen`/`AsyncIterator` (not stable).

**Needs clarification:** none.

## Updated Files

- `skills/code-review-rust/references/rules-core.md` — ASYNC-11 enhanced; VER-9 added.
- `skills/code-review-rust/references/rules-tests.md` — TEST-29 added.

## Sources

- [Announcing Rust 1.96.0 — Rust Blog](https://blog.rust-lang.org/2026/05/28/Rust-1.96.0/)
- [1.96.0 — releases.rs](https://releases.rs/docs/1.96.0/)
