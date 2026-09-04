# Rust Meta Evaluation — Microsoft "Pragmatic Rust Guidelines"

**Date**: 2026-09-04
**Source**: <https://microsoft.github.io/rust-guidelines/agents/all.txt> (3 504 lines, ~135 KB; MIT-licensed, Microsoft Corporation)
**Shape of source**: a curated guideline book, not an article — ~90 numbered `M-*` guidelines across
AI, Application, Correctness, Documentation, FFI, Macros, Performance, Project, Universal, and
Libraries (Building / Interoperability / Resilience / UX) chapters.

## Executive Summary

| Metric | Count |
|---|---|
| Guidelines extracted | 90 |
| Approved — new rules | 38 |
| Approved — enhancements to existing rules | 19 |
| Rejected — already expressed | 6 |
| Rejected — too generic / not actionable | 1 |
| Rejected — conflicts with existing guidance (user decision, 2026-09-04) | 2 |

Counts sum to 66 integration decisions over 90 source guidelines; the remaining 24 were folded into
a smaller number of consolidated rules (e.g. six macro guidelines became `MACRO-1--3`, five
re-export/prelude/leak guidelines became `API-13`) and are itemised in the mapping table below.

**Overall assessment**: **High source quality, high gap value.** Unlike a blog post, this is an
internally consistent, cross-referenced guideline set from a large Rust deployment, and essentially
nothing in it is factually wrong. Its value here is almost entirely *complementary* rather than
corrective: `code-review-rust` was strong on correctness, async, concurrency, security, and testing,
and had close to nothing on **public API surface design, documentation, macro design, crate/workspace
layout, FFI architecture, and allocation-level performance**. Those are precisely the chapters this
source is strongest on.

Two guidelines were **not** integrated because they contradict existing rules on a genuine design
disagreement rather than on a matter of fact. Both were escalated and **declined on 2026-09-04**:
the existing `SEC-5` and `ERR-2`/`ERR-3` stand unchanged. The reasoning is retained below so the
question is not re-opened from the same source next time.

## Gap analysis before integration

Searched the existing rule set for coverage of each source chapter:

| Source chapter | Prior coverage in `code-review-rust` |
|---|---|
| Macros | One clause in `TRAIT-8` ("prefer traits over macros") — no proc-macro, hygiene, or crate-split guidance |
| Documentation | `API-6` (doc tests) and `READ-4` (why not what) — no doc-section, summary-sentence, or module-doc rules |
| API surface / re-exports | `ARCH-9` (minimal surface), `ARCH-4` (curated re-exports) — nothing on path duplication, globs, preludes, or type leakage |
| FFI architecture | `SEC-34--36`, `SEC-39` (safety only) — nothing on core-vs-`-ffi` crate separation or DLL state |
| Workspace / crate layout | `ARCH-7` (file layout), `ARCH-11` (workspace deps) — nothing on crate folder layout or crate splitting |
| Allocation-level perf | `PERF-2`, `PERF-11`, `PERF-15` — nothing on `shrink_to_fit`, boxed DSTs, indirection depth, or telemetry cost |
| Build-level perf | none — no `target-cpu`, no global allocator |

## Approved — new rules (38)

| Source guideline(s) | New rule | File |
|---|---|---|
| M-PANIC-CONTINUATION | `ERR-15` catch_unwind is a last resort | rules-core |
| M-ESSENTIAL-FN-INHERENT | `TRAIT-12` essential functionality is inherent | rules-core |
| M-TYPES-SEND | `TRAIT-13` public types are `Send`; assert it statically | rules-core |
| M-MACRO-LAST-RESORT, M-EXAMPLE-OVER-PROC | `MACRO-1` macros are a last resort; declarative over proc | rules-core |
| M-MACROS-DONT-LIE, M-PROC-IMPLIED-ITEMS | `MACRO-2` macros must not lie or emit hidden items | rules-core |
| M-MACRO-HELPERS, M-PROC-IMPL, M-MACRO-MAIN-CRATE | `MACRO-3` macro crate structure and testability | rules-core |
| M-ASYNC-STACK-SIZE, M-ASYNC-FN | `ASYNC-15` `async fn` by default; future size on hot paths | rules-core |
| M-AVOID-INDIRECTION | `PERF-17` avoid needless nested indirection | rules-core |
| M-BOX-DST | `PERF-18` boxed slices/strings for immutable sequences | rules-core |
| M-LOG-OVERHEAD | `PERF-19` telemetry must not tank the hot path | rules-core |
| M-SHRINK-TO-FIT | `PERF-20` shrink long-lived grown collections | rules-core |
| M-MIMALLOC-APPS, M-TARGET-CPU | `PERF-21` build-level knobs for applications | rules-core |
| M-UNSAFE | `UNSAFE-10` unsafe needs a reason, Miri, adversarial tests | rules-core |
| M-UNSOUND | `UNSAFE-11` unsafe vs unsound; module-scoped soundness | rules-core |
| M-LATEST-EDITION | `ARCH-17` new crates target the latest edition | rules-structure |
| M-DOCUMENTED-MAGIC | `READ-11` magic values are named and justified | rules-structure |
| M-LOG-STRUCTURED | `READ-12` structured logging with message templates | rules-structure |
| M-NO-META-DESIGN-DOCUMENTATION | `READ-13` docs describe the end state, not the journey | rules-structure |
| M-RUST-SHAPED | `ARCH-13` ported code is reshaped, not transliterated | rules-structure |
| M-FFI-TRANSLATES, M-FFI-NAMING, M-ESCAPE-HATCHES | `ARCH-14` FFI crates translate; logic stays in the core crate | rules-structure |
| M-CRATES-FLAT-FOLDER, M-SMALLER-CRATES | `ARCH-15` workspace layout; when in doubt, split the crate | rules-structure |
| M-OOBE, M-SYS-CRATES | `ARCH-16` libraries build with only cargo and rustc | rules-structure |
| M-SINGLE-ITEM-PATH, M-NO-GLOB-REEXPORTS, M-NO-PRELUDE, M-FOREIGN-REEXPORTS, M-DOC-INLINE, M-DONT-LEAK-TYPES | `API-13` one public path per item; surface hygiene | rules-structure |
| M-CANONICAL-DOCS, M-FIRST-DOC-SENTENCE, M-MODULE-DOCS | `API-14` canonical doc sections and module docs | rules-structure |
| M-MSRV | `API-15` MSRV is set and conservatively updated | rules-structure |
| M-UPSTREAM-GUIDELINES, M-PUBLIC-DISPLAY | `API-16` follow the upstream API guidelines | rules-structure |
| M-REGULAR-FN | `API-17` regular functions over associated functions | rules-structure |
| M-DI-HIERARCHY, M-AVOID-WRAPPERS, M-SIMPLE-ABSTRACTIONS, M-SERVICES-CLONE | `API-18` types > generics > `dyn`; no visible wrappers | rules-structure |
| M-IMPL-RANGEBOUNDS, M-IMPL-IO | `API-19` accept the most general parameter type | rules-structure |
| M-COLLECTION-TRAITS | `API-20` collections implement the iterator traits | rules-structure |
| M-TAUTOLOGICAL-TESTS | `TEST-32` tests do not assert ground truth | rules-tests |
| M-MOCKABLE-SYSCALLS, M-TEST-UTIL | `TEST-33` I/O and syscalls are mockable and gated | rules-tests |
| M-ISOLATE-DLL-STATE | `SEC-40` only portable state crosses a Rust DLL boundary | rules-security |

## Approved — enhancements to existing rules (19)

| Source guideline | Enhanced rule | What it added |
|---|---|---|
| M-IMPL-ASREF | `OWN-7` | `AsRef` belongs on functions, not on types; the ownership-cost caveat |
| M-FROM-ERROR | `ERR-7` | Define `From` once for your own error types; `map_err` only for foreign errors or added context |
| M-PANIC-MESSAGE, M-PANIC-IS-STOP | `ERR-11` | Panic messages must carry the offending values; a library's panic is the application's `panic = "abort"` |
| M-AVOID-STATICS | `CONC-10` | Statics are duplicated per linked crate major and per DLL — correctness state must not live in one |
| M-THROUGHPUT | `ASYNC-4` | Items-per-cycle framing; no hot-spinning, no per-item work stealing |
| M-YIELD-POINTS | `ASYNC-8` | 10--100µs spacing between yields; tokio's cooperative-budget API |
| M-INITIAL-CAPACITY | `PERF-2` | Applies to all growable collections; `collect()` already does it via `size_hint` |
| M-HOTPATH | `PERF-6` | `divan`; `[profile.bench] debug = 1`; CPU time vs wall time; document hot paths |
| M-FAST-HASHER | `PERF-8` | `foldhash` (hashbrown 0.15+ default) alongside `ahash` |
| M-MEM-REUSE | `PERF-11` | Buffer reuse is an API obligation (`get_into`), not only a local one |
| M-UNSAFE-IMPLIES-UB | `UNSAFE-2` | `unsafe` marks UB risk only — not "dangerous"; `unsafe fn delete_database()` is a misuse |
| M-PARAMETER-CONSISTENCY, M-INIT-CASCADED | `FN-3` | Consistent parameter ordering across a crate; cascade construction through domain types |
| M-BALANCED-MODULES | `ARCH-3` | Essential items in the crate root; no `traits`/`errors` buckets; both extremes are findings |
| M-CARGO-WORKSPACE, M-CRATES-IN-WORKSPACE, M-STATIC-VERIFICATION | `ARCH-11` | Declare every dep in the workspace with `default-features = false`; members are workspace deps too; a concrete compiler/clippy baseline plus `cargo-hack`, `cargo-udeps`, `miri` |
| M-FEATURES-ADDITIVE | `ARCH-12` | What "additive" means concretely; no `no-std` feature; `cargo hack --feature-powerset` |
| M-SHORT-NAMES, M-WEASEL-WORDS | `API-1` | Two-word names, no module prefixes; `Service`/`Manager`/`Factory` are non-information |
| M-STRONG-TYPES-GUARD | `API-2` | A newtype encoding an invariant must enforce it: private field, fallible constructor, no infallible `From`, `const fn` for literals |
| M-INIT-BUILDER, M-BUILD-RESULT | `API-4` | Builder shape conventions; validation belongs in `.build()`; required params via `impl Into<Deps>` |
| M-INTEGRATION-TESTS | `TEST-3` | The dividing line is the surface under test; prefer `tests/` when either would work |

Also updated: `references/rules.md` (added the `MACRO` prefix to the category table),
`references/anti-patterns.md` (three new sections — Macros & Public Surface, Ports from Other
Languages, Testing — 11 entries), and `SKILL.md` (31 new scan-signal rows; `MACRO` added to the
core-rules reference line).

## Rejected

| Guideline | Criterion failed | Reason |
|---|---|---|
| M-APP-ERROR | Worth Adding — already expressed | `ERR-3` already routes `anyhow` vs `thiserror` by caller intent, with more nuance (it also covers `miette`) |
| M-PANIC-ON-BUG | Worth Adding — already expressed | `ERR-11` states exactly this, including the internal-invariant vs external-input split |
| M-LINT-OVERRIDE-EXPECT | Worth Adding — already expressed | `READ-10` covers `#[expect]` over `#[allow]` plus the `reason` field and the cfg-dependent footgun the source omits |
| M-LOG-NOT-PRINT | Worth Adding — already expressed | `READ-8`, which additionally specifies the CLI stdout/stderr contract |
| M-INITIAL-CAPACITY (core claim) | Worth Adding — already expressed | `PERF-2`; only the `size_hint` detail was new (integrated as an enhancement) |
| M-STRONG-TYPES | Worth Adding — already expressed | "Use `PathBuf` not `String`" is primitive obsession, covered by `API-2`, `API-12`, and the anti-patterns file |
| M-DESIGN-FOR-AI | Makes Sense — too generic | A meta-chapter of pointers to other guidelines ("write good docs", "use strong types"); nothing reviewable |

## Rejected — conflicts, resolved 2026-09-04

Both were put to the user and both were declined; **neither is integrated**, and the existing rules
are unchanged. Recorded here as decided precedent.

### 1. `M-PUBLIC-DEBUG` conflicts with `SEC-5` — **declined, `SEC-5` unchanged**

**Source position**: all public types should implement `Debug`, *including* secret-bearing ones — via a
hand-written impl that renders `UserSecret(...)`, backed by a unit test asserting the secret string does
not appear in `format!("{:?}", value)`.

**Current rule**: `SEC-5` — "Secret types: disable `Debug`/`Clone`, auto-zeroize on drop."

This is a real design disagreement, not a factual error. The source's position has ecosystem support
(`secrecy::SecretBox` implements a redacting `Debug` rather than omitting it), and a missing `Debug`
propagates: any struct containing the secret type loses `#[derive(Debug)]` too, which tends to end in
someone writing a manual impl that is *less* careful. Against it: a redacting `Debug` is one careless
edit away from leaking, whereas an absent one cannot.

**Decision (2026-09-04)**: declined. `SEC-5` keeps "disable `Debug`/`Clone`" as written — an absent
`Debug` cannot leak, a redacting one can. The proposed regression test was not added either, since it
only has a subject once a hand-written `Debug` exists. **Criterion failed**: Worth Adding (conflicts).

### 2. `M-ERRORS-CANONICAL-STRUCTS` conflicts with `ERR-2` / `ERR-3` — **declined, `ERR-2`/`ERR-3` unchanged**

**Source position**: errors should be situation-specific **structs** carrying a `Backtrace` and a
*private* `ErrorKind`, exposing `is_io()` / `is_protocol()` predicates rather than public variants —
so callers are not exposed to failure modes the author considers internal.

**Current rules**: `ERR-2` ("define domain error enums; document which variants each public function may
return") and `ERR-3` (`thiserror` when callers match on variants).

Both positions are defensible and widely practised; the source's is more conservative about API
evolution, the existing rules are closer to ecosystem convention and to what `thiserror` generates.
Note the existing rule set already solves the future-proofing half differently, via `#[non_exhaustive]`
(`API-9`), which `cargo semver-checks` understands and predicate methods do not.

**Decision (2026-09-04)**: declined — not adopted, and not recorded as an alternative under `ERR-2`.
Public `thiserror` enums plus `#[non_exhaustive]` (`API-9`) remain the guidance; the opaque-struct
plus `is_*()`-predicate shape is not added as a second sanctioned pattern. **Criterion failed**:
Worth Adding (conflicts).

## Validation performed

The source is documentation rather than runnable examples, so validation focused on version and
crate-status claims rather than compilation.

| Claim | Check | Result |
|---|---|---|
| `foldhash` is hashbrown's default hasher | crate/ecosystem status | Confirmed for hashbrown 0.15+; `ahash` retained in the rule as the `DashMap` default |
| `divan` is a maintained benchmark crate | crate status | Confirmed; added alongside `criterion`, not in place of it |
| `target-cpu=x86-64-v3` via `.cargo/config.toml` | rustc/cargo docs | Confirmed; the SIGILL failure mode on older hosts was added as the guardrail the source omits |
| mimalloc "up to 25%" benchmark gain | unverifiable vendor-side claim | **Not repeated.** `PERF-21` says "commonly a double-digit percentage on allocation-heavy benchmarks", requires measuring on your own workload, and points at removing allocations first |
| tokio `has_budget_remaining` | API name/location moved across releases | **Hedged.** `ASYNC-8` names `tokio::task::coop` and instructs checking against the tokio version in `Cargo.toml` rather than asserting a stable path |
| `unsafe extern`/`#[unsafe(no_mangle)]` in source examples | 2024 edition syntax | Source uses pre-2024 `#[no_mangle]`; existing `SEC-39` / `UNSAFE-7` already carry the current syntax, so the examples were not copied |
| `ohno`, `fundle`, `data_privacy` crates | adoption | **Omitted.** Low-adoption crates named in the source; the underlying patterns were kept, the crate names were not |
| `{{property}}` message-template syntax | tracing compatibility | Kept, with the caveat the source itself notes — it trips `clippy::literal_string_with_formatting_args`, so `READ-12` says allow that lint deliberately if you adopt the convention |

## Post-integration checks

- Rule IDs: no duplicates across all rule files; every prefix numbers sequentially from 1 with no
  gaps except the pre-existing retired IDs (`OWN-2`, `OWN-5`, `FN-7`, `ASYNC-2`, `CL-1`, `CL-2`) and
  the pre-existing `VER-2`/`VER-3` gap.
- All rule IDs referenced from new text resolve to rules that exist.
- Category table in `rules.md` updated for the new `MACRO` prefix; `SKILL.md` reference line matches.
- No existing rule text was deleted; all 19 enhancements are appends or in-place extensions.
