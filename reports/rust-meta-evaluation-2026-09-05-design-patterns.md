# Rust Meta Evaluation — "Rust Design Patterns" (rust-unofficial)

**Date**: 2026-09-05
**Source**: the rust-unofficial "Rust Design Patterns" book, rendered to plain text locally
(4 551 lines; upstream <https://rust-unofficial.github.io/patterns/>,
last news entry 2025-12-14)
**Shape of source**: a community pattern book — 15 idioms, 14 design patterns (behavioural,
creational, structural, FFI), 3 anti-patterns, and a functional-programming chapter, each with
Description / Motivation / Example / Advantages / Disadvantages sections.

## Executive Summary

| Metric | Count |
|---|---|
| Pieces extracted | 35 |
| Approved — new rules | 9 |
| Approved — enhancements to existing rules | 4 |
| Rejected — already expressed | 17 |
| Rejected — too generic / not actionable | 4 |
| Rejected — superseded or historical | 1 |
| Needs clarification | 0 |

**Overall assessment**: **High source quality, low-to-moderate gap value.** The book is already
cited by `API-16` as complementary reading, and the rule set has evidently absorbed most of it
already — over half the source is a direct duplicate of an existing rule (Newtype → `API-2`,
Builder → `API-4`, Deref polymorphism → `OWN-12`, clone-to-satisfy-borrowck → `OWN-8`,
`#[non_exhaustive]` → `API-9`, Strategy → `TRAIT-7`/`ARCH-2`, constructors and `Default` →
`API-16`'s C-CTOR / C-COMMON-TRAITS). The value that remained is concentrated in three places the
rule set was thin on: **borrow-checker-driven struct design**, **RAII/`Drop` mechanics**, and
**FFI ergonomics below the architectural level of `ARCH-14`**. The two FFI string/handle rules are
the highest-severity additions — both describe use-after-free bugs that compile, pass review, and
usually work.

The book's age shows in exactly one place (a rustc-1.48-era lint list), which was not integrated;
everything else validated against Rust 1.98.

## Gap analysis before integration

| Source chapter | Prior coverage in `code-review-rust` |
|---|---|
| Idioms (borrowed args, temporary mutability, closures) | `OWN-1`, `OWN-7` — generic-bound guidance only, nothing on plain `&String`/`&Box<T>` parameters |
| Finalisation in destructors / RAII guards | None. `Drop` appeared only inside `TEST-23` and `CONC-14` |
| Struct decomposition for independent borrowing | None. `OWN-8` says "rethink ownership design" without saying how |
| Custom traits to simplify bounds | `TRAIT-3` (`where` clauses) — layout only, not parameter elimination |
| On-stack dynamic dispatch | None. `PERF-17` covers avoiding `Arc`, not avoiding `Box<dyn>` |
| FFI strings / handle lifetimes | `SEC-34--36`, `ARCH-14` — pointer validity and crate layout, nothing on `CString` temporaries or borrowed handles |
| Return consumed argument on error | None |
| `#![deny(warnings)]` | None. `ARCH-11` covers lint centralization, `READ-10` covers `expect` vs `allow` |
| Doc-test initialization | `API-6` ("doc tests with `///`") — one clause, no mention of the never-run trap |
| Behavioural/creational patterns, functional chapter | Well covered (`API-2`, `API-4`, `TRAIT-7`, `PATTERN-1`, `ARCH-2`) |

## Approved — new rules

| # | Source | Rule | Target | Reasoning |
|---|---|---|---|---|
| 1 | Struct decomposition for independent borrowing | **OWN-13** | `rules-core.md` | Fills a gap: names the fix `OWN-8` gestures at. Adds the field-vs-struct borrow distinction and the "don't split what has no name" caveat |
| 2 | Use custom traits to avoid complex type bounds | **TRAIT-14** | `rules-core.md` | Complements `TRAIT-3`: eliminates a type parameter rather than reformatting bounds. Blanket-impl example compiled and verified on 1.98 |
| 3 | Finalisation in destructors + RAII with guards | **PATTERN-9** | `rules-core.md` | Two source chapters merged. The `let _ =` vs `let _guard =` trap is a real, silent, single-character defect not covered anywhere; the "destructors are not guaranteed" caveat keeps it from being read as a durability guarantee |
| 4 | On-Stack Dynamic Dispatch | **PATTERN-10** | `rules-core.md` | Fills a gap. Example compiled on 1.98; the Rust 1.79 attribution is the book's and is carried with an MSRV caveat rather than asserted as verified |
| 5 | Return consumed argument on error | **API-21** | `rules-structure.md` | Fills a gap. Backed by `std` precedent (`FromUtf8Error::into_bytes`, `mpsc::SendError<T>`), and prevents the defensive-clone pattern `PERF-3` would otherwise flag downstream |
| 6 | `#![deny(warnings)]` anti-pattern | **ARCH-18** | `rules-structure.md` | Fills a gap. The mechanism (future rustc breaks the build; `--cap-lints` protects consumers but not CI or contributors) is unchanged since the book was written |
| 7 | Accepting Strings + Passing Strings (FFI) | **SEC-41** | `rules-security.md` | Critical-severity gap. The dangling-`CString`-temporary bug is in the `std` docs *because* it is common; `SEC-34--36` do not cover temporary lifetimes |
| 8 | Object-Based APIs + Type Consolidation into Wrappers | **SEC-42** | `rules-security.md` | Critical-severity gap. Two source chapters merged into one rule; adds the aliasing half (a stored iterator makes a later `&mut` non-exclusive, UB even unread) which the book supplies in a footnote |
| 9 | Easy doc initialization | **TEST-34** | `rules-tests.md` | Fills a gap. The source presents the wrapper as an idiom and mentions in passing that the assertions never run — inverted here into the review signal |

## Approved — enhancements to existing rules

| # | Source | Enhanced rule | What was added |
|---|---|---|---|
| 10 | Temporary mutability | **OWN-1** | Narrowing mutability in *time* (block-return or `let data = data;` rebinding), alongside the existing narrowing in scope |
| 11 | Use borrowed types for arguments | **OWN-7** | `&str`/`&[T]`/`&Path`/`&T` over `&String`/`&Vec<T>`/`&PathBuf`/`&Box<T>` in plain-reference parameters, the double-indirection rationale, and the note that `clippy::ptr_arg` catches all but the smart-pointer cases |
| 12 | Contain unsafety in small modules | **UNSAFE-5** | The audit unit is the privacy boundary, not the `unsafe` block; `std::String` as the model; a `pub(crate)` field defeats the containment |
| 13 | Generics as Type Classes | **PATTERN-1** | Splitting an API by variant with a generic parameter, with the scan signal (`Option<T>` field that some call sites know is `Some`) and the monomorphization cost |

## Rejected — already expressed

| Source item | Existing coverage |
|---|---|
| Newtype pattern | `API-2`, `API-1` |
| Builder pattern | `API-4` (deeper than the source: generated builders, validation in `build()`) |
| Constructors (`new` convention, `new` alongside `Default`) | `API-16` (C-CTOR) |
| The `Default` trait, `..Default::default()` | `API-16` (C-COMMON-TRAITS), `TRAIT-4`, `DUP-7` |
| Collections are smart pointers | `OWN-12` |
| `mem::take`/`replace` in changed enums | `PERF-3`, `OWN-8` |
| `#[non_exhaustive]` and private fields | `API-9` |
| Clone to satisfy the borrow checker | `OWN-8`, `PERF-3`, anti-patterns |
| Deref polymorphism | `OWN-12`, anti-patterns |
| Strategy (aka Policy) | `TRAIT-7`, `ARCH-2`, `API-18` |
| Command | `TRAIT-7`, `API-18` (dispatch-choice guidance) |
| Visitor / Fold | `TRAIT-7`, `ARCH-2` — pattern catalogue, no review signal |
| Interpreter | `MACRO-1` (a macro needs a reason), `TRAIT-8` |
| Error Handling in FFI (flat/structured enums → codes) | `SEC-39`, `ARCH-14`, `ERR-2` |
| Contain unsafety (base claim) | `UNSAFE-5` — the nuance was merged in as enhancement 12 |
| Prefer small crates | `ARCH-1`, `ARCH-15`, `ARCH-16` |
| SOLID / DRY / KISS / LoD appendix | `DUP-1--10`, `ARCH-1`, `TRAIT-6` (ISP), `READ-1` |

## Rejected — too generic or not actionable

| Source item | Reasoning |
|---|---|
| Concatenating strings with `format!` | Style preference with no correctness or reliability consequence; `PERF-13` already covers the performance half, and more precisely (`write!` into the destination) |
| Iterating over an `Option` | `.extend(opt)` / `.chain(opt)` / `iter::once` are API trivia, not a review signal; the source itself says `if let` is usually preferable |
| Pass variables to closure (rebinding block) | Formatting-level idiom. No failure mode, nothing to detect in review |
| Functional Language Optics (Iso / Poly Iso / Prism) | Explanatory material for reading serde's API, not guidance for writing code. No actionable rule extractable |

## Rejected — superseded or historical

| Source item | Reasoning |
|---|---|
| The `#![deny(...)]` lint lists in the anti-pattern chapter | Explicitly dated "as of rustc 1.48.0" and now wrong: `const_err` and `private_in_public` were removed from rustc, `bad_style` is a deprecated lint group. The chapter's *argument* was integrated as `ARCH-18`; its lint list was not |

## Validation performed

- **Compiled on rustc 1.98.0 (edition 2024)**: the `TRAIT-14` `Getter` trait with its blanket
  `impl<F: FnMut() -> Result<T, Error>, T: Display>`, and the `PATTERN-10` on-stack
  `&mut dyn io::Read` across an `if`/`else` with a `?` in one branch. Both compile clean.
- **Version claims**: the Rust 1.79 temporary-lifetime-extension attribution in `PATTERN-10` is the
  book's; it is stated as the origin of the behaviour and paired with an MSRV check (`API-15`)
  rather than presented as independently verified.
- **Not carried over**: every pre-1.85 or rustc-1.48-era detail (the lint list above), and the
  book's `Box<dyn io::Read>` "disadvantage" framing, which its own text retracts.

## Updated files

| File | Change |
|---|---|
| `references/rules-core.md` | +`OWN-13`, `TRAIT-14`, `PATTERN-9`, `PATTERN-10`; enhanced `OWN-1`, `OWN-7`, `UNSAFE-5`, `PATTERN-1` |
| `references/rules-structure.md` | +`ARCH-18`, `API-21` |
| `references/rules-security.md` | +`SEC-41`, `SEC-42` (FFI section) |
| `references/rules-tests.md` | +`TEST-34` |
| `references/anti-patterns.md` | +whole-struct-borrow (Ownership), new **Resources & Cleanup** section (guard bound to `_`, `Drop` as durability), +doctest-that-never-runs (Testing), +dangling `CString` and borrowed FFI handle (Security), new **Build Configuration** section (`#![deny(warnings)]`) |
| `SKILL.md` | +11 rows in the Scan Checklist covering every new rule and the two parameter-level enhancements |
