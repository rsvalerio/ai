# rust-meta Evaluation — 2026-08-09

**Source**: pasted article, "Common macros work, but this macro improves compile-time safety, debugging, deployments, and code generation" — a survey of 20 lesser-known Rust standard-library macros.

## Executive Summary

| | Count |
|---|---|
| Pieces extracted | 20 |
| Approved (integrated) | 15 (merged into **11** rules) |
| Rejected | 4 |
| Needs clarification | 1 |

Rust version compatibility: all approved material is stable well below the 1.87 ingestion baseline (oldest new claim: `#[track_caller]` 1.46; newest: `std::pin::pin!` 1.68, `thread_local!` `const {}` 1.59).

**Overall assessment.** The source is an accurate-but-shallow catalogue: it describes what each macro does correctly, but its "without / with" framing is frequently a strawman (nobody writes `format!("v{}.{}", 1, 2)`), and several entries would be actively harmful as review rules if adopted verbatim — notably `assert!` for argument validation (conflicts with ERR-2/ERR-10) and `dbg!` presented as a practice to adopt rather than a leak to catch. One factual error was found and corrected before integration.

Value came almost entirely from **the caveats the article omits**, which is where the integrated rules put their weight: `debug_assert!` vanishing in release (unsoundness), `thread_local!` breaking under tokio task migration, `cfg!` not gating compilation, `option_env!` staleness without `rerun-if-env-changed`.

## Corrections made to source material

- **`env!("TARGET")` is wrong.** The article lists "Build target (TARGET)" as an `env!` use. `TARGET`, `HOST`, `PROFILE`, and `OPT_LEVEL` are set by Cargo only for **build scripts**; `env!("TARGET")` in ordinary crate source is a compile error. PATTERN-7 states this and gives the `cargo::rustc-env=` workaround.
- **`format_args!` example buys nothing.** The article's `buffer.write_fmt(format_args!(…))` is precisely what `write!` expands to — no allocation is saved relative to `write!`. Integrated under PERF-13 with its actual use (forwarding `fmt::Arguments` through a custom API) and its real constraint (borrows temporaries, cannot be `let`-bound).
- **`assert!(b != 0)` before `a / b` is a poor example.** Integer division by zero already panics; and panicking on a public function's argument conflicts with returning `Result`. ERR-11 reframes as panic-for-bugs / `Result`-for-expected-failure.
- **`dbg!` polarity inverted.** The article recommends adopting it. As a review rule the useful direction is the opposite: it is not stripped in release and must not be committed (READ-9).

## Detailed Results

### Approved

| # | Source item | Target | Integration |
|---|---|---|---|
| 1, 2 | `include_str!`, `include_bytes!` | **PATTERN-6** (new, `rules-core.md`) | Merged into one rule. Added the boundary the article lacks: not for operator-mutable config, not for large assets; noted paths resolve relative to the including file and Cargo tracks them. |
| 3, 4, 5 | `concat!`, `env!`, `option_env!` | **PATTERN-7** (new, `rules-core.md`) | Merged — `concat!` has no standalone value but is the natural composer for `env!` literals. Added the `cargo::rerun-if-env-changed` staleness caveat and the `TARGET` correction. |
| 6 | `compile_error!` | **ARCH-12** (new, `rules-structure.md`) | Placed with the workspace/build-config rules next to ARCH-11. Extended beyond the article: features are additive, so guards must cover **both** none-selected and over-selected (`--all-features`); noted mutually exclusive features are themselves a design smell. |
| 7 | `cfg!` | **PATTERN-8** (new, `rules-core.md`) | Reframed as the `cfg!` vs `#[cfg]` decision — both `cfg!` branches must type-check on every target, so it cannot gate platform-specific APIs. |
| 8, 10 | `write!`/`writeln!`, `format_args!` | **PERF-13** (new, `rules-core.md`) | Merged. Anchored on the concrete cases (`Display` impls, reused buffers per PERF-11); added the `fmt::Write`/`io::Write` name collision, the `BufWriter` syscall-per-write point, and the corrected `format_args!` role. |
| 9 | `eprintln!` | **READ-8** (enhanced, `rules-structure.md`) | Not a new rule — READ-8 already flags `println!`/`eprintln!` outside binaries. Added the stdout/stderr contract for CLI binaries, where direct printing *is* correct. |
| 13 | `dbg!` | **READ-9** (new, `rules-structure.md`) | Polarity inverted per above. Added: not release-stripped, takes ownership (can change move semantics), leaks internal state (SEC-21), and `clippy::dbg_macro` as the mechanical check. |
| 14 | `file!`/`line!`/`column!`/`module_path!` | **ERR-12** (new, `rules-core.md`) | The manual approach is largely obsolete; rule points at `#[track_caller]` + `Location::caller()` for caller attribution and notes `tracing` records callsites automatically. Manual capture retained as valid only inside macro definitions. |
| 15, 17, 18 | `assert!`, `unreachable!`, `todo!`/`unimplemented!` | **ERR-11** (new, `rules-core.md`) | Merged into one panic-vs-`Result` rule. Adds: prefer unrepresentable state over `unreachable!`; `unreachable!` reachable from untrusted input is a remote panic (→ SEC-33); `todo!`/`unimplemented!` on a shipped path is a panic bomb. |
| 16 | `debug_assert!` | **UNSAFE-9** (new, `rules-core.md`) | Routed to UNSAFE rather than ERR per the conditional-routing guidance — the load-bearing point is that `debug_assertions` is off in release, so a `debug_assert!` guarding an `unsafe` precondition turns a caught bug into UB. Cross-referenced SEC-31. |
| 19 | `thread_local!` | **CONC-11** (new, `rules-core.md`) | Added the `const {}` initializer (1.59) and, as the centrepiece, the async footgun the article misses: tokio tasks migrate across worker threads at `.await`, so `thread_local!` cannot carry per-task context — use `tracing::Span` / `tokio::task_local!`. Also noted destructors do not run for unjoined threads. |
| 20 | `pin!` | **ASYNC-12** (new, `rules-core.md`) | Grounded in the real use case: `tokio::select!` over `&mut fut` in a loop. Boundary stated — `Box::pin` when the future must outlive the scope or be stored. |

### Rejected

| # | Source item | Criterion failed | Reason |
|---|---|---|---|
| 3 | `concat!` as a standalone practice | Makes Sense (strawman example), Worth Adding | `format!("v{}.{}", 1, 2)` is not code anyone writes; `concat!` over plain literals is replaceable by writing the literal. Its genuine value is composing macro-expanded literals — retained inside PATTERN-7, rejected standalone. |
| 11 | `matches!` | Worth Adding (already expressed) | Covered by **READ-7** (pattern matching over nested if/else, explicitly naming `clippy::match_like_matches_macro`) and referenced in **TEST-29**. The pattern-guard variant adds no reviewable nuance. |
| 12 | `stringify!` | Worth Adding (not actionable) | Almost exclusively a macro-authoring tool. Produces no reviewable condition in ordinary application or library code. |
| 15b | `assert!` for public-API argument validation | Makes Sense, Worth Adding (conflicts) | Conflicts with ERR-2 / ERR-10 / SEC-11: external input must return `Result`. The salvageable half (internal invariants) is integrated as ERR-11. |

### Needs Clarification

- **`include_str!` / `include_bytes!` binary-size budget (PATTERN-6).** The rule says "large assets inflate binary size and compile time" without a threshold, because no defensible universal number exists — it depends on deployment target (container image vs. embedded vs. CLI distributed by download). Left qualitative deliberately. **Question for the user**: if this workspace has a binary-size budget worth encoding, PATTERN-6 can carry a concrete cutoff.

## Files Modified

**`skills/code-review-rust/references/rules-core.md`**

- Added ERR-11 (panic vs `Result`; `assert!`/`unreachable!`/`todo!`/`unimplemented!`), ERR-12 (`#[track_caller]`)
- Added CONC-11 (`thread_local!`, incl. tokio task-migration footgun)
- Added ASYNC-12 (`std::pin::pin!`)
- Added PERF-13 (`write!`/`writeln!`/`format_args!`)
- Added UNSAFE-9 (`debug_assert!` erased in release)
- Added PATTERN-6 (`include_str!`/`include_bytes!`), PATTERN-7 (`env!`/`option_env!`/`concat!`), PATTERN-8 (`cfg!` vs `#[cfg]`)

**`skills/code-review-rust/references/rules-structure.md`**

- Enhanced READ-8 (stdout/stderr contract for CLI binaries)
- Added READ-9 (`dbg!` must not be committed)
- Added ARCH-12 (`compile_error!` for feature-flag invariants)

No changes needed to `rules.md` — all new IDs use existing prefixes already indexed there. Rule numbering verified sequential in all touched prefixes; no retired IDs reused.
