# rust-meta Evaluation — 2026-08-09 (Crates)

**Source**: pasted article, Michael Preston, "Ten Rust Libraries That Deserve More Attention" — a survey of eleven crates (the title undercounts) that solve recurring engineering problems.

## Executive Summary

| | Count |
|---|---|
| Pieces extracted | 12 (11 crates + the closing meta-thesis) |
| Approved (integrated) | 10 (7 new rules + 3 enhancements to existing rules) |
| Rejected | 2 |
| Needs clarification | 0 |

Rust version compatibility: nothing approved depends on an unstable feature or a language version above the 1.87 ingestion baseline. The only MSRV constraint carried into a rule is `compact_str`'s own 1.71.

**Overall assessment.** A materially better source than the previous two ingestions from this genre. It is a crate catalogue, but the framing is the useful one — each entry names the *class of mistake* the crate removes and states a counter-case where the crate is wrong, which is exactly the shape a review rule needs. Ten of twelve entries survived evaluation, the highest ratio so far.

The value added during integration is mostly in three places the article leaves implicit: the **overlap arbitration** between `arc-swap` and `tokio::sync::watch` (both cover read-mostly config, and the existing CONC-8 already recommended the latter), the **cheaper-alternative-first** ordering for `compact_str` (borrowed `&str` and `Box<str>`/`Arc<str>` come before a new string type), and the **failure mode of the tool itself** for `insta`/`trycmd` (blind snapshot acceptance, nondeterministic snapshot content) and `moka` (a cache is a behavioural change, not a free speedup).

## Verification performed

All eleven crates checked against the crates.io API for maintenance status; every one is actively maintained with a release inside the last 12 months. Facts asserted in new rules were verified at source rather than taken from the article:

| Crate | Latest stable | Last release | Verified claim |
|---|---|---|---|
| `camino` | 1.2.5 | 2026-07-28 | `Utf8Path` / `Utf8PathBuf`, serde support |
| `fs-err` | 3.3.1 | 2026-07-03 | `std::fs` mirror; **`tokio` optional dep** → `fs_err::tokio` mirrors `tokio::fs` (article omits this) |
| `serde_path_to_error` | 0.1.20 | 2025-09-15 | `deserialize()` wrapper, `err.path()` / `err.inner()` |
| `miette` | 7.6.0 | 2025-04-27 | `#[derive(Diagnostic)]`, source spans/labels |
| `insta` | 1.48.0 | 2026-06-11 | `assert_snapshot!` family; filters/redactions for nondeterminism |
| `trycmd` | 1.2.1 | 2026-07-21 | transcript fixtures; `TRYCMD=overwrite` |
| `compact_str` | 0.10.0 | 2026-07-13 | **24 bytes inline (12 on 32-bit)**, `size_of == size_of::<String>()`, **MSRV 1.71** |
| `arc-swap` | 1.9.2 | 2026-06-28 | `load()` guard / `store()`; positioned as read-mostly `RwLock<Arc<T>>` replacement |
| `moka` | 0.12.15 | 2026-03-22 | `sync`/`future` caches, `get_with` per-key atomic insertion; **≥ 0.12 no longer uses background threads** (article omits this) |
| `bon` | 3.9.3 | 2026-06-15 | `#[builder]` on struct / fn / method; typestate-enforced required fields |
| `capnp` | 0.27.0 | 2026-08-02 | maintained — rejected on relevance, not staleness |

No factual errors were found in the article itself. Two claims were *incomplete* in ways that would have made the derived rule wrong in context, and both were corrected on integration: `fs-err` presented as `std::fs`-only (it would have read as "adopt this and lose async I/O", contradicting CONC-5), and `moka` described without the 0.12 threading change (the article's "background threads" framing predates the current release).

## Detailed Results

### 1. `camino` — UTF-8 paths as a typed invariant — Approved (new rule)

**Status**: Approved → **API-12** (`rules-structure.md`).
**Reasoning**: fills a gap. Nothing in API-1--11 or OWN covered path handling. Complements API-2 directly — this is the newtype argument applied to a std type, and the design philosophy in `rules.md` ("encode preconditions in the type system") already endorses the move. Actionable scan signal exists: repeated `to_str().unwrap()` / `to_string_lossy()` on the same values.
**Rust version**: no constraint.
**Modifications**: sharpened the cost of *not* adopting it into three concrete failure shapes (`to_str().unwrap()` is a panic on input the code claims to support; `to_string_lossy()` is silent data corruption of a real filename; an `.ok_or` arm the caller cannot act on) — the article says only "creates friction". Kept the article's counter-case (do not use where arbitrary OS paths must round-trip) verbatim in substance, since it is what keeps the rule from being wrong for filesystem tooling.

### 2. `fs-err` — path context in filesystem errors — Approved (new rule)

**Status**: Approved → **ERR-13** (`rules-core.md`).
**Reasoning**: fills a gap and complements ERR-4. ERR-4 ("add context with `.with_context()`") is the manual half; the argument that a *scattered* concern needs a mechanism rather than discipline is the genuinely new content. Practical: `std::fs` errors omitting the path is a real, common, low-quality-diagnostic failure mode.
**Rust version**: no constraint.
**Modifications**: added the `fs_err::tokio` module (verified as an optional `tokio` dependency in the crate manifest), cross-linked to CONC-5. Without it a reviewer applying this rule to an async codebase would be steering it back onto blocking I/O — a direct conflict with an existing rule. Also kept ERR-4 as a legitimate alternative rather than presenting the crate as the only answer, matching the article's own hedge.

### 3. `serde_path_to_error` — field paths in deserialization errors — Approved (new rule)

**Status**: Approved → **ERR-14** (`rules-core.md`).
**Reasoning**: fills a gap. The rule set had nothing on deserialization *diagnostics*; SEC-11 covers deserialization *safety* (size limits, depth, unknown fields) and is a different axis.
**Rust version**: no constraint.
**Modifications**: bounded the scope explicitly — the article says "does not replace schema validation" in passing, and that boundary is load-bearing here because SEC-11 owns the adjacent rule. Added the SEC-21 caveat the article does not consider: a field path is for the operator editing the file; echoing it back to an untrusted caller is information disclosure.

### 4. `miette` — source-span diagnostics — Approved (enhancement)

**Status**: Approved → enhancement to **ERR-3** (`rules-core.md`).
**Reasoning**: "similar but adds nuance", so enhanced rather than added. ERR-3 already frames error-crate choice on one axis (do callers match on variants?). `miette` is not another point on that axis — it is a second axis (does the error point into a document a human wrote?), which is why it belongs *in* ERR-3 rather than beside it.
**Rust version**: no constraint.
**Modifications**: kept the article's most useful sentence — the engineering judgment to hold rich diagnostics at the human boundary and not force internal errors through a pretty-printing abstraction — and cross-linked READ-8, which already establishes that service code should emit structured events.

### 5. `insta` — snapshot testing — Approved (new rule)

**Status**: Approved → **TEST-30** (`rules-tests.md`).
**Reasoning**: fills a gap. The TEST rules covered assertions (TEST-1, TEST-11, TEST-29), property tests (TEST-9), and tooling (TEST-27, TEST-28) but had nothing on snapshot testing. The article's own framing of the value — output changes become *reviewable*, rather than assertions becoming easier — is the correct one and is what makes it a rule rather than a preference.
**Rust version**: no constraint.
**Modifications**: two additions. The article names the lazy-approval risk; the rule makes it a review check (unexplained `.snap` churn must be justified). The article does *not* mention determinism at all, which is the more common way snapshot suites rot — timestamps, UUIDs, absolute paths, and hash-ordered iteration in a snapshot are a flakiness source, so the rule cross-links TEST-16/TEST-18 and points at `insta`'s filters and redactions instead of re-accepting each run.

### 6. `trycmd` — binary-level CLI testing — Approved (new rule)

**Status**: Approved → **TEST-31** (`rules-tests.md`).
**Reasoning**: fills a gap. TEST-3 places integration tests in `tests/` but says nothing about testing the binary as a binary. Strong pairing with an existing rule: READ-8 already mandates the CLI `stdout`/`stderr` contract, and *nothing in the rule set could have detected a violation of it* — TEST-31 closes that loop.
**Rust version**: no constraint.
**Modifications**: kept `assert_cmd` as a co-equal option rather than adopting the article's mild preference for `trycmd` — the two solve the same problem and the choice is a project-convention call, not a correctness one. Added that `trycmd` fixtures inherit TEST-30's failure mode (`TRYCMD=overwrite` is blind snapshot acceptance under another name).

### 7. `compact_str` — small-string optimization — Approved (new rule)

**Status**: Approved → **PERF-15** (`rules-core.md`).
**Reasoning**: complements **PERF-9** (`SmallVec`/`ArrayVec`) — same optimization, different container, and the asymmetry of having one without the other was a real gap. The article's discipline ("not a default replacement for `String`; reach for it only when profiling or workload shape justifies it") aligns with PERF-6 and keeps this from becoming cargo-culting.
**Rust version**: crate MSRV 1.71, stated in the rule.
**Modifications**: replaced the article's vague size claim with the verified numbers (24 bytes inline, 12 on 32-bit, same `size_of` as `String`). Added the cheaper-alternatives-first ordering the article omits: if the tokens do not outlive the source buffer, borrowed `&str` (PATTERN-3) costs nothing at all; if they are immutable after construction, `Box<str>`/`Arc<str>` drops the capacity word without a dependency. A rule that jumps straight to a new string type would frequently be recommending the third-best option.

### 8. `arc-swap` — lock-free read-mostly state — Approved (enhancement)

**Status**: Approved → enhancement to **CONC-1** (`rules-core.md`).
**Reasoning**: "similar but adds nuance". CONC-1 already routes read-dominated state to `Arc<RwLock<T>>`, so `ArcSwap` refines an existing recommendation rather than filling a gap — enhancement, not a new rule. The whole-value-replacement semantics (immutable snapshots, atomic publication, no half-updated state) is the part worth recording.
**Rust version**: no constraint.
**Modifications**: **overlap arbitration.** The article does not mention `tokio::sync::watch`, but CONC-8 already recommends it for "latest-value broadcast (config updates, state)" — the exact use case the article gives `ArcSwap`. Rather than flagging the conflict, the enhancement resolves it with an explicit split: `watch` when the code is async and readers need to *await* changes, `ArcSwap` when readers only sample the current value (including from sync code, where `watch` does not apply). Also stated the counter-case the article leaves implicit — replacement semantics are wrong for state that must be edited field-by-field.

### 9. `moka` — caching with an actual policy — Approved (new rule)

**Status**: Approved → **PERF-16** (`rules-core.md`).
**Reasoning**: fills a gap, and a load-bearing one — the rule set had no cache rule at all, while an unbounded ad-hoc cache is simultaneously a performance issue, a memory-growth issue, and a SEC-33 resource-exhaustion path when keys are attacker-influenced. The article's closing line ("the crate solves the mechanics; you still own the policy") is the right rule and was adopted as its core.
**Rust version**: no constraint.
**Modifications**: added the verified 0.12 threading change (background threads removed) — the article's implicit model is stale. Named `get_with` specifically as the stampede fix; the article says caches "make cache stampedes worse" without naming the mechanism that solves it, which would leave a reviewer with a complaint and no remedy. Made the policy requirement the actual finding criterion (key, value, max size, TTL, invalidation expectation) so the rule fires on hand-rolled caches rather than merely advertising a crate.

### 10. `bon` — generated builders — Approved (enhancement)

**Status**: Approved → enhancement to **API-4** (`rules-structure.md`).
**Reasoning**: "similar but adds nuance". API-4 said only "Builder pattern for complex construction; initialize all fields" — it asserted *when* without *how*, and had no position on handwritten versus generated. The article supplies both halves: the when-not (a builder is an API choice, not decoration) and the drift argument (a handwritten builder silently lacks a setter for each newly added field).
**Rust version**: no constraint.
**Modifications**: listed `typed-builder` and `derive_builder` alongside `bon` so the rule is about generation rather than one crate. Added the typestate point (compile-time required-field enforcement replaces a runtime "field not set" error arm), which is the concrete advantage over hand-rolling and fits the rule set's compile-time-over-runtime philosophy. Cross-linked DUP-3 (repeated boilerplate) and DUP-7 (`..Default::default()` as the correct answer for inert data).

### 11. `capnp` — binary serialization — Rejected (not actionable as a review rule)

The Rust Cap'n Proto implementation, proposed for internal, schema-driven, performance-sensitive boundaries in place of JSON.

**Reasoning**: the underlying observation is fair — codebases do keep text formats on boundaries long after those boundaries became internal and hot. But it cannot become a finding. The article supplies no threshold at which JSON stops being appropriate, and the correct answer at that threshold is highly context-dependent (`prost`/protobuf where cross-language schema evolution matters, `postcard`/`bincode` for compact Rust-to-Rust, `rkyv` for zero-copy) — Cap'n Proto is one option among several, not the conclusion. Adoption also drags in a schema compiler as a build dependency and a reader/builder API that is not a drop-in for serde structs, making it an architecture decision rather than a code-review correction. Where serialization cost is actually the problem, PERF-6 already governs (profile first, then fix the dominant hotspot). **Criterion failed**: Worth Adding (not actionable; no threshold; solution space too wide for a single recommendation).

### 12. "Adopt a focused crate before the codebase grows a private version" — Rejected (too generic)

The closing thesis: a local helper module starts small, then accretes edge cases, inconsistent behaviour, weak tests, and unclear ownership, so a narrow well-maintained crate is often the better dependency.

**Reasoning**: true, and it is the connective tissue of the article, but it is unfalsifiable as a review rule — the article immediately supplies the equal-and-opposite consideration (compile time, audit surface, version management, API commitment) and then concedes the real question is per-codebase. A rule that resolves to "it depends" produces no finding. The specific instances that *are* actionable were integrated individually as items 1--10 above, which is where the value actually lives. The adjacent structural concern is already covered: **ARCH-4** rejects grab-bag `helpers`/`utils` modules and **ARCH-6** requires matching abstraction to problem complexity. **Criterion failed**: Worth Adding (too generic), Makes Sense (no actionable rationale — cuts both ways by the author's own argument).

## Summary

### Approved — new rules (7)

| Rule | File | Subject |
|---|---|---|
| **ERR-13** | `rules-core.md` | Filesystem errors must name the path (`fs-err`, or ERR-4 by hand) |
| **ERR-14** | `rules-core.md` | Deserialization errors must name the field (`serde_path_to_error`) |
| **PERF-15** | `rules-core.md` | Small-string optimization for short-string-dominated workloads (`compact_str`) |
| **PERF-16** | `rules-core.md` | Caches need eviction, size cap, TTL, and stampede handling (`moka`) |
| **API-12** | `rules-structure.md` | UTF-8 paths as a typed invariant (`camino`) |
| **TEST-30** | `rules-tests.md` | Snapshot testing for verbose/structured output (`insta`) |
| **TEST-31** | `rules-tests.md` | Test the CLI binary as a binary (`trycmd` / `assert_cmd`) |

### Approved — enhancements (3)

| Rule | File | Added |
|---|---|---|
| **ERR-3** | `rules-core.md` | `miette` as the source-span-diagnostics case, bounded to the human boundary |
| **CONC-1** | `rules-core.md` | `arc_swap::ArcSwap` for read-mostly whole-value state, arbitrated against `tokio::sync::watch` (CONC-8) |
| **API-4** | `rules-structure.md` | Generate builders (`bon` et al.) rather than hand-writing; when a builder is warranted at all |

### Rejected (2)

- **`capnp` / binary serialization** — not actionable; no threshold given, solution space too wide, adoption is an architecture decision. PERF-6 governs the underlying concern.
- **"Adopt a focused crate before growing a private helper"** — too generic; resolves to "it depends" by the author's own counter-argument. ARCH-4 and ARCH-6 cover the structural half.

### Needs clarification (0)

The one candidate — `arc-swap` overlapping `tokio::sync::watch` (CONC-8) — was resolved during integration with an explicit split rule rather than deferred, since both options were already documented and the distinguishing criterion (does the reader need to *await* changes?) is unambiguous.

## Updated files

| File | Change |
|---|---|
| `skills/code-review-rust/references/rules-core.md` | +4 rules (ERR-13, ERR-14, PERF-15, PERF-16); enhanced ERR-3, CONC-1 |
| `skills/code-review-rust/references/rules-structure.md` | +1 rule (API-12); enhanced API-4 |
| `skills/code-review-rust/references/rules-tests.md` | +2 rules (TEST-30, TEST-31) |
| `skills/code-review-rust/SKILL.md` | +6 rows in the Scan Checklist for the new rules |

Rule numbering remains sequential in every prefix touched (ERR now runs to 14, PERF to 16, API to 12, TEST to 31). No retired IDs were reused. All cross-references added (ERR-4, CONC-5, CONC-7, CONC-8, SEC-11, SEC-21, SEC-33, PERF-6, PERF-9, PATTERN-3, API-2, READ-8, TEST-11, TEST-16, TEST-18, DUP-3, DUP-7, FN-3) resolve to existing rules.
