# rust-meta Evaluation — 2026-08-09 (Attributes)

**Source**: pasted article, "Attributes are powerful tools in Rust, but many of them are underused" — a survey of 15 lesser-known Rust attributes.

## Executive Summary

| | Count |
|---|---|
| Pieces extracted | 15 |
| Approved (integrated) | 9 (6 new rules + 3 enhancements to existing rules) |
| Rejected | 6 |
| Needs clarification | 0 |

Rust version compatibility: all approved material is stable at or below the 1.87 ingestion baseline. Oldest new claim: `#[repr(align(N))]` and `#[repr(transparent)]` (1.25/1.28); newest: `#[diagnostic::do_not_recommend]` (1.85), referenced as a cross-link only.

**Overall assessment.** This is the second ingestion from the same genre of source — a catalogue that describes each feature correctly but frames its value through toy examples. The pattern from the previous evaluation repeats: roughly a third of the entries are already covered by existing rules, a third are real gaps, and the integrated value sits mostly in the constraints the article omits (false sharing as the actual reason to care about alignment, symbol collision and unwind-abort as the actual risks of `no_mangle`, the self-cleaning property that makes `#[expect]` better than `#[allow]`).

Two factual errors were found and corrected before integration. Six entries were rejected: four because existing rules already express them (in two cases with strictly more nuance than the source), and two because they describe editor/docs ergonomics that could never be a review finding.

## Corrections made to source material

- **`#[diagnostic::on_unimplemented]` is not nightly.** The article's example includes `#![feature(diagnostic_on_unimplemented)]`, implying a feature gate. The attribute was stabilized in **Rust 1.78**; the `#![feature]` line would itself fail to compile on stable. TRAIT-11 states the stable version explicitly and flags the claim.
- **The `#[must_use]` "without" example does not compile clean.** The article shows `fn divide(…) -> Option<i32>` called and discarded, captioned "compiles without warnings". `Option` (like `Result`) is already annotated `#[must_use]` in std, so that baseline *does* warn. The real gap the attribute fills is user-defined types and non-`Option`/`Result` returns — which is how API-5 was extended.
- **`#[inline(always)]` framing is misleading.** The article implies `square(5)` becomes `5 * 5` because of the attribute. At any optimization level LLVM inlines a function that small regardless; the attribute changes nothing in the example. Rejected in favour of PERF-5, which already states the profiling-first rule.

## Detailed Results

### 1. `#[track_caller]` — Rejected (already expressed)

Attribute reports the caller's location on panic; also drives `Location::caller()`.

**Already expressed**: **ERR-12** (`rules-core.md`), added in the 2026-08-09 macro evaluation, covers both halves including the `Location::caller()` interaction and the "don't hand-roll `file!()`/`line!()`" corollary. Nothing new. **Criterion failed**: Worth Adding.

### 2. `#[must_use = "…"]` — Approved (enhancement)

Custom message; applicable to types, not just functions.

**Status**: Approved → enhancement to **API-5** (`rules-structure.md`).
**Reasoning**: API-5 previously said only "`#[must_use]` on Results, Futures, builders" — which, taken literally, is advice to annotate things std already annotates. The genuinely useful applications (own types whose construction is pointless if discarded; always using the message form) were absent. Rust version: 1.0 / 1.27 for the message form.
**Modifications**: reframed around the std-already-covers-this correction, and added the requirement that the message state the forgotten *action*.

### 3. `#[cold]` — Approved (new rule)

Marks rarely-executed functions so the optimizer moves them off the hot path.

**Status**: Approved → **PERF-14** (`rules-core.md`).
**Reasoning**: fills a gap — PERF-5 covers `#[inline]` but nothing covered cold-path placement. Complements PERF-6 (profile first).
**Modifications**: added the two caveats that bound its real-world value — rustc already treats panicking/`Err` paths as cold, and the win requires *extracting* the cold work into its own function. Without those the rule would encourage annotation cargo-culting.

### 4. `#[deprecated]` — Approved (new rule)

Marks items obsolete with `since` and `note`.

**Status**: Approved → **API-11** (`rules-structure.md`).
**Reasoning**: fills a gap in the API-evolution cluster (API-9 `#[non_exhaustive]`, API-10 `cargo semver-checks`) — deprecation is the missing third piece of the "evolve without breaking" story.
**Modifications**: added three points the source omits — it is a no-op on trait impls (`useless_deprecated`), `since` means the shipping version not the removal version, and internal call sites also warn and should be migrated rather than blanket-`allow`ed.

### 5. `#[inline(always)]` / `#[inline(never)]` — Rejected (already expressed)

**Already expressed**: **PERF-5** (`rules-core.md`), which is more precise than the source — it explains the cross-crate/cross-CGU mechanism, the LTO interaction, and requires profiling before `inline(always)`. The article's example additionally misattributes ordinary LLVM inlining to the attribute (see corrections). **Criterion failed**: Worth Adding, Makes Sense.

### 6. `#[used]` — Rejected (not relevant)

Keeps an apparently-unused static in the binary for linker sections, interrupt vector tables, firmware headers.

**Reasoning**: legitimate, but exclusively an embedded/bare-metal concern. This rule set targets services, CLIs, and NATS/JetStream applications; a rule that can never fire in the target corpus is noise in a review checklist. Also has unstable sub-forms (`#[used(linker)]` / `#[used(compiler)]`) and does not on its own guarantee retention without linker-script cooperation — nuance that would need to be carried for the rule to be correct. **Criterion failed**: Worth Adding (not relevant).

### 7. `#[non_exhaustive]` — Rejected (already expressed)

**Already expressed**: **API-9** (`rules-structure.md`), which covers enums *and* structs, the stable-since version (1.40), the `cargo semver-checks` interaction, and the `_private: ()` alternative for the case `#[non_exhaustive]` cannot express. Strictly more nuanced than the source. **Criterion failed**: Worth Adding.

### 8. `#[diagnostic::on_unimplemented]` — Approved (new rule)

Custom compiler error when a trait bound is unsatisfied.

**Status**: Approved → **TRAIT-11** (`rules-core.md`).
**Reasoning**: fills a gap; nothing in TRAIT-1–10 addresses diagnostics as an API-design surface. Pairs naturally with API-8 (sealed traits), where the default error is especially unhelpful.
**Modifications**: corrected the stability claim (1.78, no feature gate — see corrections); added that the `diagnostic` namespace is best-effort so typos silently no-op; cross-linked `#[diagnostic::do_not_recommend]` (1.85).

### 9. `#[doc(alias = "…")]` — Rejected (not a review finding)

Adds rustdoc search keywords.

**Reasoning**: technically correct and harmless, but a missing doc alias is not a defect — no reviewer would file it, and it fails the "specific and actionable *as a finding*" bar in the Worth Adding criterion. Documentation quality is represented by API-6 (doc tests), which *is* falsifiable. **Criterion failed**: Worth Adding.

### 10. `#[rustfmt::skip]` — Rejected (not a review finding)

Preserves hand-formatting on an item.

**Reasoning**: formatter configuration, not code quality; `make fmt`-equivalent tooling owns this. Additionally the source omits that it is only stable on *items* — on statements and expressions it requires the nightly `stmt_expr_attributes` feature — so adopting the advice as written would fail to build in the most common case (skipping a single statement). **Criterion failed**: Worth Adding, Still Valid (as stated).

### 11. `#[repr(align(N))]` — Approved (new rule, reframed)

Raises a type's minimum alignment.

**Status**: Approved → **CONC-12** (`rules-core.md`).
**Reasoning**: the source frames this as SIMD/hardware trivia, which is outside this rule set's scope. The review-relevant application is **false sharing** — independently-written atomics colliding in one cache line — which no existing CONC rule covered despite CONC-7 and CONC-9 living adjacent to it.
**Modifications**: reframed entirely around false sharing; added `crossbeam_utils::CachePadded` as the preferred mechanism and the correction that a hardcoded 64-byte line is wrong on x86-64 and aarch64 (128 bytes, adjacent-line prefetch) — precisely the platforms where contention hurts most.

### 12. `#[expect(lint)]` — Approved (new rule)

Suppresses a lint and warns if the lint stops firing.

**Status**: Approved → **READ-10** (`rules-structure.md`).
**Reasoning**: fills a gap and connects to existing policy — `rules-classification.md` already grants a severity reduction for justified `#[allow]`s, but nothing told reviewers that a self-expiring suppression exists. Rust version: 1.81 for both `#[expect]` and the `reason` field.
**Modifications**: added the cfg/feature footgun (an `#[expect]` whose lint fires in only some configurations warns as unfulfilled in all the others), and tied it to the existing severity-reduction rule.

### 13. `#[no_mangle]` / `#[export_name]` — Approved (new rule, reframed)

Control exported symbol names for FFI.

**Status**: Approved → **SEC-39** (`rules-security.md`, FFI section).
**Reasoning**: complements SEC-34–36, which cover the *inbound* FFI direction (validating what C hands us) but never the *outbound* direction (what we publish to C).
**Modifications**: reframed from "how to export a symbol" to the three things that make it a security finding — global-namespace collision and symbol interposition, the requirement for an explicit `extern "C"` ABI, and unwind-across-FFI aborting the process since Rust 1.71 (so a fallible export needs `catch_unwind` or `extern "C-unwind"`). Added item (6) to the FFI audit checklist.

### 14. `#[cfg_attr(…)]` — Approved (enhancement)

Conditionally applies another attribute.

**Status**: Approved → enhancement to **PATTERN-8** (`rules-core.md`).
**Reasoning**: PATTERN-8 (added in the previous evaluation) already covers `cfg!` vs `#[cfg]`; `#[cfg_attr]` is the third member of the same family, so per the integration workflow it belongs appended to that rule rather than as a new one.
**Modifications**: kept the article's genuinely good point — that duplicating an entire item under `#[cfg(feature)]` / `#[cfg(not(feature))]` to vary one derive is an anti-pattern — and made it the flaggable behaviour, since the duplicated copies inevitably diverge.

### 15. `#[repr(transparent)]` — Approved (enhancement)

Guarantees a single-field wrapper has its field's layout and ABI.

**Status**: Approved → enhancement to **API-2** (`rules-structure.md`).
**Reasoning**: API-2 already prescribes the newtype pattern and calls it a "zero-cost abstraction". That phrase is about performance and is easily misread as a layout guarantee — which it is not. The enhancement closes exactly that misreading.
**Modifications**: stated the boundary — required for FFI (cross-linked SEC-36) and for wrappers the caller may reinterpret; unnecessary on domain newtypes that never leave Rust, so it does not become a reflexive annotation.

## Summary

### Approved — new rules (6)

| Rule | File | Topic |
|---|---|---|
| TRAIT-11 | `rules-core.md` | `#[diagnostic::on_unimplemented]` for unsatisfied trait bounds |
| CONC-12 | `rules-core.md` | Cache-line padding against false sharing |
| PERF-14 | `rules-core.md` | `#[cold]` for extracted rare paths |
| READ-10 | `rules-structure.md` | `#[expect]` over `#[allow]` for temporary suppressions |
| API-11 | `rules-structure.md` | `#[deprecated]` as the non-breaking retirement path |
| SEC-39 | `rules-security.md` | Exported symbol collision and unwind safety |

### Approved — enhancements (3)

| Rule | File | Addition |
|---|---|---|
| API-2 | `rules-structure.md` | `#[repr(transparent)]` when a newtype needs layout/ABI guarantees |
| API-5 | `rules-structure.md` | Message form and own-type application; std already covers `Result`/`Option` |
| PATTERN-8 | `rules-core.md` | `#[cfg_attr]` instead of duplicating items per feature |

### Rejected (6)

| Piece | Reason |
|---|---|
| `#[track_caller]` | Already expressed — ERR-12 |
| `#[inline(always)]` / `#[inline(never)]` | Already expressed — PERF-5, which is more precise |
| `#[non_exhaustive]` | Already expressed — API-9, which is more nuanced |
| `#[used]` | Embedded-only; cannot fire in this rule set's target corpus |
| `#[doc(alias)]` | Not a defect; unfalsifiable as a review finding |
| `#[rustfmt::skip]` | Formatter configuration; also unstable on statements as the source presents it |

**Needs clarification**: none.

## Updated files

| File | Change |
|---|---|
| `skills/code-review-rust/references/rules-core.md` | +TRAIT-11, +CONC-12, +PERF-14; PATTERN-8 extended with `#[cfg_attr]` |
| `skills/code-review-rust/references/rules-structure.md` | +READ-10, +API-11; API-2 and API-5 extended |
| `skills/code-review-rust/references/rules-security.md` | +SEC-39; FFI audit checklist item (6) |

No rule IDs were reused and no existing rule was retired. Numbering continues from the state after PR #2 merged: ERR-12, CONC-11, ASYNC-12, PERF-13, UNSAFE-9, PATTERN-8, READ-9, ARCH-12, SEC-38.
