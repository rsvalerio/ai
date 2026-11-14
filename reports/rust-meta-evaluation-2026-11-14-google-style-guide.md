# Rust Meta Evaluation — Google Rust Style Guide

**Date**: 2026-11-14
**Source**: pasted plain-text copy of Google's Rust Style Guide
(<https://google.github.io/styleguide/rustguide.html>, gh-pages @ `a9c5f82b1981`, retrieved 2026-11-14)
**Shape of source**: a house style guide for a monorepo-scale organisation. Roughly a third is
codebase-specific (Chromium, Fuchsia, Android), a third restates the upstream Rust API Guidelines
or default-on Clippy lints, and a third is review-level judgement. Rationales are often absent
or are "this rule exists to avoid reviewer disagreements" and "helps Large-Scale Changes".

## Executive Summary

| Metric | Count |
|---|---|
| Pieces extracted | 59 |
| Approved — new rules | 4 |
| Approved — enhancements to existing rules | 8 |
| Rejected — already expressed | 26 |
| Rejected — codebase-specific (Chromium / Fuchsia / LSC) | 9 |
| Rejected — mechanical (default Clippy / rustfmt / compiler) or too generic | 9 |
| Conflicts with existing guidance — not integrated | 3 |
| Needs clarification — resolved by the user and integrated (counted above) | 4 |

**Overall assessment**: **authoritative source, low gap value.** The rule set already holds the
guide's position on ownership, flexible parameters, error reporting, traits versus inherent impls,
macros, unsafe, `#[must_use]`, `#[non_exhaustive]`, `catch_unwind` and documentation, usually with
more rationale than the guide gives. Two real gaps produced new rules: **API-23** (`bool`
parameters) and **ARCH-19** (code before `main`). Six existing rules gained a concrete shape or a
stated cost they lacked. Four further pieces were flagged for the user, who decided all four in
favour of integration: **CONC-16** (poisoned locks, absolute position, retiring `VER-4`),
**READ-14** (lifetime names), and extensions to `READ-7` and `TRAIT-1`.

Nothing integrated depends on a Rust version newer than 1.40 (`#[non_exhaustive]`); all of it is
valid on the 1.98 ingestion baseline and in both the 2021 and 2024 editions.

## Detailed Results

### Approved

| # | Extracted content | Reasoning | Target | Integration |
|---|---|---|---|---|
| 1 | Prefer `enum` over `bool` in APIs where the parameter's purpose is not obvious | *Fills gap.* No rule covered boolean parameters; `FN-3` covers mix-ups of same-typed arguments only in general. Clippy's `fn_params_excessive_bools` (pedantic) fires only above three, so the ordinary case is unowned. Exemptions written in (single-argument setters, private helpers) to keep it from generating noise | **`API-23`** (new) | New rule, index line, scan row |
| 2 | Do not run code before `main()` (`ctor`) | *Fills gap.* The guide gives no rationale; the one supplied is from the `ctor` crate's own warning (stay within libc, no std runtime services) plus unspecified constructor ordering. Extended to `inventory` (same mechanism) and pointed at `linkme` (link-time data, no pre-`main` code) for the legitimate registry use | **`ARCH-19`** (new) | New rule, index line, scan row |
| 3 | Mark a public function `const` only if you expect it to stay `const` | *Fills gap, small.* Removing `const` is a breaking change that `cargo semver-checks` reports; nothing said so. Note added that `clippy::missing_const_for_fn` (nursery) pushes the opposite way | `API-10` | Appended |
| 4 | Treat `#[doc(hidden)]` items you do not own as private | *Fills gap, small.* Hidden `pub` items are outside the semver promise; the finding is in the consumer. Cross-referenced to `MACRO-3`, which is where such items legitimately come from | `API-10` | Appended (same sentence group as #3: what is and is not in the semver surface) |
| 5 | `#[non_exhaustive]` exceptions: closed ontologies, and structs meant for functional record update | *Complements.* `API-9` said when to use the attribute but not its cost. Verified: a `#[non_exhaustive]` struct cannot be built with a struct expression outside its crate, `..Default::default()` included (E0639), which collides with the options-struct idiom in `DUP-7` | `API-9` | Appended |
| 6 | `with_foo(\|foo\| …)` closure accessors in place of returning `MutexGuard` (leaks an implementation detail) | *Complements.* `API-18` bans ownership and synchronisation wrappers in public signatures but named only parameter and owned-return shapes; a guard in a return type is the same leak. Added the `.await` benefit (`CONC-2`) and the re-entrancy caveat, which the guide omits | `API-18` | Sentence inserted in the "smart pointers and wrappers" paragraph; scan row widened |
| 7 | No combinator chain in a `for` header; avoid `Iterator::for_each`; chains that mutate external state should be loops; prefer a combinator over a loop that reimplements `any()` | *Complements.* `READ-3` set a length bound only. These are three length-independent shapes plus the converse | `READ-3` | Appended; scan row |
| 8 | Extension traits carry the `Ext` suffix | *Fills gap, small.* RFC 445 convention, followed by std (`OsStrExt`) and the ecosystem (`StreamExt`). The guide's ownership clause ("the team that owns the type should own the extension trait") is organisational and was reduced to its technical core: same-named methods from two extension traits are ambiguous (E0034) | `TRAIT-5` | Appended; scan row |

### Conflicts with existing guidance — flagged, not integrated

| # | Extracted content | Conflict |
|---|---|---|
| 9 | Error types: implement `Copy` whenever possible | Pulls against `ERR-4`, `ERR-9`, `ERR-13` and `ERR-14`, which require errors to carry context, a source chain, the path and the field. An error that does that is not `Copy`. Applies to small status-code enums only, which `API-16` (C-COMMON-TRAITS) already covers |
| 10 | Constructors: `new_with_foo()` when there is more than one | std and `API-17` / C-CTOR use `with_foo` (`Vec::with_capacity`). `try_new()` for fallible constructors is consistent and already implied by `API-2` |
| 11 | Prefer type annotations on the declaration over turbofish | `READ-3`'s own example is `collect::<Result<Vec<_>, _>>()?`, which cannot be written as a declaration annotation without splitting the `?`. Style preference with no stated rationale |

Also noted: the guide permits `pub use submodule::*` in non-leaf modules, which `API-13` forbids.
`API-13`'s reasoning (unreviewable in a diff) stands; no change.

### Needs clarification — resolved and integrated

Flagged on first pass; the user decided each one on 2026-11-14.

| # | Extracted content | Question raised | Decision | Integration |
|---|---|---|---|---|
| 12 | "Never reach inside a poisoned mutex" | The guide gives no rationale, and `VER-4` allowed `clear_poison` after recovery | **Absolute position** | **`CONC-16`** (new): `PoisonError::into_inner` / `get_ref` / `get_mut` and `clear_poison` are findings; propagate with `expect`. Rationale supplied from `ERR-15` (state may be half-updated). **`VER-4` retired** with a pointer to `CONC-16`. Index line, scan row |
| 13 | On a `#[non_exhaustive]` enum, list every known variant: `Shape::Triangle \| _ => {}` | The pattern trips the default-on `clippy::wildcard_in_or_patterns` | **Integrate as a comment convention** | `READ-7` extended: the `_` arm carries a comment naming the variants deliberately ignored; `if let` / `let … else` when one variant matters; no `_` arm on enums the crate owns. Scan row |
| 14 | Descriptive lifetime names on types; at most two single-letter lifetimes locally | Pure naming rule | **Yes, Low severity** | **`READ-14`** (new), with the guide's exemptions (`'_`, one local `'a`, `for<'a>`, `Cow`-like wrappers). Index line, scan row |
| 15 | Pair an important `From` impl with `new()` / `from_foo()` | No rationale given | **Do it** | `TRAIT-1` extended; rationale supplied (discoverability in the method list, call-site readability, no inference annotation). Scan row |

### Rejected — already expressed

| Extracted content | Already expressed in |
|---|---|
| Avoid `Rc` / `Arc`; prefer unique ownership | `OWN-9`, `PERF-17`, `API-18` |
| Borrow instead of deep-copying; `.clone()` not a substitute for borrowing | `OWN-8`, `OWN-13`, `PERF-3` |
| `&T` / `&[T]` / `&str` / `Option<&T>` over `&Box<T>` / `&Vec<T>` / `&String` / `&Option<T>` | `OWN-6`, `OWN-7` (scan row exists) |
| Return iterators over `Vec`, with exceptions | `API-3` |
| Accept iterators / `IntoIterator` in library parameters; slices fine in application code | `API-19`, bounded by `API-18` |
| `impl Into<T>` only when call-site ergonomics are paramount; almost never in application code | `API-18` (bound creep), `OWN-7` |
| `Option` / `Result` / `panic!` by contract | `ERR-11`, `ERR-6`, `ERR-2` |
| Newtype instead of type alias | `API-2` |
| Named fields over tuples | `FN-4` |
| Add trait impls when necessary (libraries eagerly, applications lazily) | `TRAIT-4`, `API-16` (C-COMMON-TRAITS) |
| `Copy`, `Clone`, `Hash` + `Eq`, `Ord` guidance for important traits | `API-16`, `TRAIT-4` |
| Generics over `dyn Trait` in libraries | `API-18`, `TRAIT-7` |
| Define a trait only for generics, `impl`/`dyn Trait`, or extension; not to organise code | `TRAIT-9`, `TRAIT-12`, `API-18` (scan row: trait implemented exactly once) |
| Options structs implement `Default` | `DUP-7`, `FN-3`, `API-4` |
| Macro preference order: functions, `macro_rules!`, codegen, proc macros | `MACRO-1`, `TRAIT-8` |
| `as_` / `to_` / `into_` naming | `API-16` (C-CONV) |
| Getter `foo()`, not `get_foo()` | `API-16` (C-GETTER) |
| Avoid abbreviations unless well known | `API-1` |
| Document public APIs, panics, unsafe invariants; `//!` for modules | `API-14` |
| Comments should say what the code does not | `READ-4`, `READ-13` |
| Unsafe: avoid, encapsulate, `SAFETY:` comment, justify with benchmarks | `UNSAFE-1`, `UNSAFE-5`, `UNSAFE-10` |
| `#[non_exhaustive]` on public enums and structs | `API-9` |
| `#[must_use]` on functions and types | `API-5` |
| Pattern matching over check-then-unwrap; `expect` over `unwrap` | `ERR-5` (names the exact `is_some()` / `unwrap()` shape) |
| Context strings on assertions; do not merely restate the condition | `ERR-11` (scan row exists) |
| No `catch_unwind`; meaningless under `panic=abort` | `ERR-15` |

### Rejected — codebase-specific

Prefer small crates [chrome]; flat `rust_library` layout [chrome] (contradicts Cargo layout by its
own admission; `ARCH-7`, `ARCH-15` govern); `chromium::import!`; `git cl format`; no `async` in
Chromium; sequences instead of threads; `fuchsia_sync::Mutex`; per-codebase test frameworks; and
the leaf-module rules (name the file after its primary item, no code in non-leaf modules), which
exist for LSC tooling. `ARCH-8` keeps the `lib.rs` form of the latter.

### Rejected — mechanical, unstable, or too generic

| Extracted content | Reason |
|---|---|
| No glob imports | `clippy::wildcard_imports` (pedantic) is the mechanical check and `rust-make-clippy-pedantic` files it; the re-export and prelude half is `API-13` |
| `imports_granularity = Module` | **Still Valid fails**: unstable rustfmt option, nightly only |
| `max_width`, `hex_literal_case`, `format_macro_matchers`; `#[rustfmt::skip]` only for alignment | Formatter configuration, partly unstable; not a review finding |
| Locally-scoped trait imports; qualify free functions with the module; import types unqualified | Convention with no defect behind it; the guide's stated rationale is avoiding reviewer disagreement |
| Implement the std trait instead of a look-alike method; `#[derive]` instead of a manual impl; `Default` beside `new()`; `is_empty()` beside `len()` | Default-on Clippy: `should_implement_trait`, `derivable_impls`, `new_without_default`, `len_without_is_empty` |
| No unstable features | Enforced by the stable compiler |
| Operator overloading only for mathematical meaning | Upstream C-OVERLOAD, deferred to by `API-16`; `OWN-12` covers the `Deref` case |
| Prefer `PartialEq` over `Eq`, `PartialOrd` over `Ord` | No rationale; contradicts C-COMMON-TRAITS, which asks for both where the semantics hold |
| `format!` over `+` because it "requires fewer allocations"; `format!` over `str::replace` templating | Performance claim unverified (`a + &b + &c` reuses `a`'s buffer); `PERF-13` covers the measured case |
| Short generic parameter names indicative of the bound | Too generic to act on |

## Rust version verification

- `#[non_exhaustive]` struct-expression restriction (E0639), including with `..base` — current behaviour since 1.40.
- `const fn` removal as a breaking change — language semantics; `cargo semver-checks` carries lints for free functions and inherent methods.
- `clippy::fn_params_excessive_bools`, `struct_excessive_bools`, `needless_for_each`: pedantic. `missing_const_for_fn`: nursery. `wildcard_in_or_patterns`: default-on (complexity).
- `ctor` / `inventory` run constructors at load time; `linkme` distributed slices are link-section data with no runtime initialisation.
- Extension-trait `Ext` suffix: RFC 445; ambiguous method resolution is E0034.

Not compiled: the signatures quoted in the new text are illustrative fragments.

## Updated files

| File | Change |
|---|---|
| `plugins/dev/skills/code-review-rust/references/rules/API.md` | **`API-23`** new; `API-9`, `API-10`, `API-18` extended |
| `plugins/dev/skills/code-review-rust/references/rules/ARCH.md` | **`ARCH-19`** new |
| `plugins/dev/skills/code-review-rust/references/rules/READ.md` | **`READ-14`** new; `READ-3`, `READ-7` extended |
| `plugins/dev/skills/code-review-rust/references/rules/TRAIT.md` | `TRAIT-1`, `TRAIT-5` extended |
| `plugins/dev/skills/code-review-rust/references/rules/CONC.md` | **`CONC-16`** new |
| `plugins/dev/skills/code-review-rust/references/rules/VER.md` | `VER-4` retired (superseded by `CONC-16`) |
| `plugins/dev/skills/code-review-rust/references/rules/index.md` | `API-23`, `ARCH-19`, `CONC-16`, `READ-14` lines; `VER-4` marked retired; size labels for API, ARCH, CONC, READ, TRAIT |
| `plugins/dev/skills/code-review-rust/references/scan-checklist.md` | 9 new rows; `API-18` row widened |

No rule was renumbered; `VER-4` is retired in place. `API-23`, `ARCH-19`, `CONC-16` and `READ-14` are the next free numbers in their ranges.
