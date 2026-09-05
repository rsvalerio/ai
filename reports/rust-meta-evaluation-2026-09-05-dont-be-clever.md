# Rust Meta Evaluation — "Don't Be Clever"

**Date**: 2026-09-05
**Source**: pasted essay, "Don't Be Clever" (Matthias Endler / corrode.dev style; sections:
Why Simple is Hard, Generics Are A Liability, Simple Code Is Often Fast Code, Keep Your Users in
Mind, Tips For Fighting Complexity, How to Recognize The Right Level of Abstraction)
**Shape of source**: an opinion essay on simplicity and accidental complexity in Rust — no
benchmarks, few APIs, one worked signature-escalation example and one API-layering example.

## Executive Summary

| Metric | Count |
|---|---|
| Pieces extracted | 12 |
| Approved — new rules | 1 |
| Approved — enhancements to existing rules | 3 |
| Rejected — already expressed | 6 |
| Rejected — too generic / not actionable | 2 |
| Needs clarification | 0 |

**Overall assessment**: **Good source quality, narrow gap value.** The essay's thesis — clarity
over cleverness — is already the rule set's own position (`READ-1`, with `CL-1`/`CL-2` retired
into it, plus `CL-5`'s cognitive-load heuristic and `ARCH-6`'s YAGNI line), so half the source is
a restatement. The value that survived is concentrated in three places where the existing rules
stated a *preference* without stating its *cost or its counterweight*:

1. `API-18` ranked concrete > generic > `dyn` but never said what a generic costs
   (monomorphization: compile time, binary size) or that bounds are requirements imposed on every
   caller. The essay's `&str` → `impl AsRef<str>` → `<'a, S: AsRef<str> + Send + Sync + ?Sized>`
   escalation is the best short illustration of that failure mode I have seen and is now cited.
2. `ARCH-6` was a nine-word rule ("Match abstraction to problem complexity; YAGNI") with no
   guidance on *when* to abstract. The essay's "defer the refactor, let repetition be the signal"
   argument and its two litmus tests give it teeth.
3. Nothing in the rule set pushed back on **over-optimization**. `PERF-3`, `PERF-17`, `OWN-8`, and
   `PERF-15` all push toward removing allocations; only `PERF-6` ("never optimize without
   profiling") pushed the other way, and it is filed under benchmarking workflow. In a review
   skill this is a false-positive generator — a reviewer following the PERF rules literally will
   flag clones in cold code. `PERF-3` now carries the inverse finding explicitly.

One genuine gap produced a new rule: **API-22**, the common-case entry point.

The essay is version-agnostic; nothing in it depends on a Rust version, and every claim
integrated was checked against current stable behaviour.

## Detailed Results

### Approved

| # | Extracted content | Status | Reasoning | Target | Integration |
|---|---|---|---|---|---|
| 1 | Generics are a liability: each is monomorphized into a separate copy per concrete type, costing compile time and binary size; the test is "is this generic functionality?" not "could this be generic?" | **Approved** | *Complements.* `API-18` gave the ladder but not the cost that motivates staying on the low rung. Verified: monomorphization semantics are correct; `cargo llvm-lines` / `cargo bloat` are the right measurement tools, and `clippy::extra_unused_type_parameters` covers only the degenerate case | `API-18` | New third paragraph |
| 2 | The signature-escalation example (`&str` → `impl AsRef<str>` → generic + lifetime → `+ Send + Sync + ?Sized`), each step "reasonable", the result unreadable | **Approved** | *Fills gap.* Named as **bound creep**, plus the related **over-constrained bounds** finding the example implies: `Send + Sync` on a parameter the body never sends is a requirement imposed on every caller and is a compatibility break to remove later (`API-10`). Also added the mitigation the essay omits — generic shell delegating to a non-generic inner fn, as `std::fs::File::open` does | `API-18`, `anti-patterns.md` | Same paragraph + two new anti-pattern entries |
| 3 | Give the dominant use case a one-call entry point; don't make users reach `base64_encode("hello")` through a four-setter builder | **Approved** | *Fills gap.* `API-4` says when a builder is warranted and `API-14` covers docs, but nothing said the general form must not be the *only* form. The `base64` crate's move to engine-based APIs (and the `prelude` module shipped to claw back the ergonomics) is a real, checkable case study | **API-22** (new) | After `API-21` |
| 4 | Defer refactoring; a wrong abstraction is harder to undo than a simple concrete implementation and hides the better decomposition; repetition, not anticipation, is the signal; a reverted abstraction attempt is a success if written down. Litmus tests: adding the next feature feels obvious; the doc comment says "X", not "X and Y" | **Approved** | *Complements.* Expands the thinnest rule in the set. The CSV-exporter narrative generalizes cleanly to the review question "which caller needs this flexibility *in this change*?" | `ARCH-6` | Rule rewritten, cross-refs to `DUP-1--10`, `TEST-33`, `ARCH-1`, `FN-6` |
| 5 | "Performance crimes are OK" — clone liberally, use `Arc`/`Box` where it keeps code simple; Rust's visible allocation costs push developers to add complexity avoiding allocations in code that isn't performance-critical | **Approved** | *Complements, with scoping.* Integrated as the **inverse finding**, not as licence: complexity added for an unprofiled allocation on a startup, config, CLI, or error path is itself reviewable. Enumerated the cold paths so the rule is applicable rather than attitudinal; kept `PERF-6`'s profile-first ordering as the arbiter | `PERF-3`, `anti-patterns.md` | Appended to `PERF-3`; one anti-pattern entry |

### Rejected — already expressed

| Extracted content | Already expressed in |
|---|---|
| "Don't be clever"; clarity over cleverness; write code for humans | `READ-1` (`CL-1`/`CL-2` were explicitly retired into it) |
| Use familiar idioms over exotic type-level programming | `CL-4`, verbatim in substance |
| Application code should be straightforward; library code consumed by experts may tolerate more | `CL-5` and its five-factor decision heuristic — strictly more developed than the source |
| `Vec` vs `impl Iterator`: return `Vec` when the caller collects anyway or iterates twice | `API-3` ("return `Vec` when indexing, length, or owned storage is required") — the essay's criteria reduce to owned storage |
| Resist premature optimization; measure before optimizing | `PERF-6` (profile → find the 1--2 dominant hotspots → optimize → re-measure) |
| Simple is not sloppy; compile-time invariants and unrepresentable illegal states add safety without accidental complexity | `CL-3`, `READ-5`, `API-2`, `CL-4` |

### Rejected — too generic / not actionable

| Extracted content | Reason |
|---|---|
| "Simple code is often fast code"; the quicksort illustration; CPUs favour predictable access patterns | True but unfalsifiable as a review rule — no signal a reviewer can scan for. The essay's own quicksort is 20× slower than `slice::sort`, which undercuts it as evidence |
| Seinfeld's "creating mode vs editing mode"; write the naïve version first | Process advice about how to write code, not a property of code under review. `ARCH-6`'s "defer the abstraction" captures the reviewable half |

## Rust version verification

Nothing in the source is version-dependent. Claims checked against current stable:

- Monomorphization producing one body per instantiation, with compile-time and binary-size cost — correct, unchanged.
- `std::fs::File::open<P: AsRef<Path>>` narrowing to `&Path` before doing work — verified in std source; the pattern cited for thinning generic bodies.
- `Send`/`Sync` bounds as caller-facing requirements whose removal is non-breaking but whose addition is breaking — consistent with `API-10` / `cargo semver-checks`.
- `base64`'s free `encode`/`decode` functions superseded by the `Engine` trait, with a `prelude` module added for ergonomics — stated qualitatively rather than pinned to a version.

## Updated files

| File | Change |
|---|---|
| `skills/code-review-rust/references/rules-structure.md` | `API-18` +1 paragraph (cost of generics, bound creep, over-constrained bounds, thinning generic bodies); **`API-22`** new (common-case entry point); `ARCH-6` rewritten (defer the abstraction, repetition as signal, two litmus tests) |
| `skills/code-review-rust/references/rules-core.md` | `PERF-3` +1 paragraph (the inverse finding: complexity added for unprofiled allocations in cold code) |
| `skills/code-review-rust/references/anti-patterns.md` | New **Abstraction & Generics** section, 5 entries |
| `skills/code-review-rust/SKILL.md` | 4 new scan-checklist rows |

No rule was removed or renumbered; `API-22` is the next free number in the `API` range.
