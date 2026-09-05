# Rust Meta Evaluation — "Common Rust Pitfalls" (pasted article)

**Date:** 2026-09-05
**Source:** Pasted article text — a "Rust production pitfalls" survey (integer overflow, `as` conversions, bounded/newtype domain types, invalid states, `Default`, `Debug`/serde secret leakage, TOCTOU, constant-time comparison, unbounded input, `Path::join`, `cargo-geiger`, a clippy lint set)
**Target skill:** `code-review-rust`
**Baseline:** Rust 1.87+ (per evaluation-criteria.md), edition 2021/2024

## Executive Summary

| Metric | Count |
|--------|-------|
| Pieces extracted | 17 |
| Approved | 9 |
| Rejected (already expressed) | 6 |
| Needs clarification | 2 |

Overall assessment: the article is a competent but largely **derivative** survey — roughly a third of it restates rules `code-review-rust` already carries at greater depth (SEC-15, SEC-7, SEC-33, API-2, SEC-25). Its value is concentrated in four places the existing rule set genuinely did not cover: **`Path::join`'s absolute-segment replacement**, **panicking slice indexing on untrusted indices**, **`#[derive(Default)]` producing invalid states**, and **derived `Deserialize` bypassing a validating newtype's constructor**. Those four are now integrated, along with three smaller enhancements (the `overflow-checks` release knob, the destructuring `Debug` impl technique, and the handle-first TOCTOU fix with its CVE).

Two technical errors in the source were caught and **not** propagated (see "Source errors caught" below). One out-of-band correction to an unrelated existing rule was made and is disclosed.

Rust-version compatibility: no issues. Everything integrated is stable well below the 1.87 baseline; the single version-gated item (`split_at_checked`, stable 1.80) is marked as MSRV-dependent in the rule text.

---

## Detailed Results

### 1. Integer overflow — use checked arithmetic

- **Status:** Rejected (core claim) / Approved (two details)
- **Reasoning:** *Worth Adding* fails for the main claim. **Already expressed:** SEC-15 already covers checked/saturating arithmetic on untrusted input, the debug-panic vs. release-wrap asymmetry, and `try_from` preference — in more detail than the article.
- **Approved details:** (a) `overflow-checks = true` under `[profile.release]` as an explicit mitigation — SEC-15 named the asymmetry but not the knob that fixes it; (b) the `checked_*` / `saturating_*` / `wrapping_*` selection being a statement of intent rather than three interchangeable ways to silence a warning.
- **Target:** SEC-15 (`rules-security.md`) — enhancement, not a new rule.
- **Modification:** the article's quantitative cost claim ("a few percent", citing a Dan Luu post) was dropped — it is unverified against a current toolchain and benchmark-dependent. Replaced with a qualitative trade-off framing. The article's compile-time-overflow example is correct (`arithmetic_overflow` is deny-by-default) and was folded in as a scoping note.

### 2. Avoid `as` for numeric conversions; prefer `From` / `TryFrom`

- **Status:** Approved (as enhancement)
- **Reasoning:** *Worth Adding* — partial. SEC-15 already says "audit `as` casts… prefer `try_from`/`try_into`". The article adds the three-way **decision rule** (lossless → `From`; lossy → `TryFrom`; intended truncation → `as`) and, more usefully, the four clippy lints that enforce it mechanically: `cast_possible_truncation`, `cast_sign_loss`, `cast_possible_wrap`, `cast_precision_loss`. None appeared anywhere in the skill.
- **Rust version:** all four lints are long-stable pedantic lints.
- **Target:** SEC-15 (`rules-security.md`), with a cross-reference to ARCH-11.
- **Note:** a latent tension exists between SEC-3 ("prefer safe casts (`as`, `From`/`Into`)") and SEC-15 ("audit `as` casts"). Not a real conflict — SEC-3's context is `transmute` alternatives, where `as` genuinely is the safe option — so SEC-3 was left alone.

### 3. Bounded types for numeric values (`NonZeroUsize`, custom `Distance`)

- **Status:** Rejected
- **Reasoning:** *Worth Adding* fails. **Already expressed:** API-2 (newtype with private field and fallible constructor) and VER-9 (`NonZero<T>` unified generic). The existing rules are stricter than the article's, which does not require the field be private.

### 4. Avoid primitive types for business logic (`Username` newtype)

- **Status:** Rejected
- **Reasoning:** *Worth Adding* fails. **Already expressed:** API-2, API-1, and the "Primitive obsession" entry in `anti-patterns.md`.

### 5. Don't index arrays without bounds checking; use `.get()`

- **Status:** Approved — **fills a gap**
- **Reasoning:** *Makes Sense* yes; *Still Valid* yes; *Worth Adding* yes. Genuine gap: no rule covered panicking indexing, and `clippy::indexing_slicing` appeared nowhere in the skill. ERR-5 covers `unwrap`/`expect` and ERR-11 covers panic policy, but neither reaches `v[i]` — which is the same panic with no syntactic marker at all.
- **Target:** **New rule ERR-16** in `rules-core.md` (next available in the ERR range; previous high was ERR-15).
- **Modification:** the article's framing ("whenever I see this I get goosebumps") would produce a blanket ban and a flood of false positives. The rule as written makes **provenance of the index** the test — an index from a loop counter or a just-checked length stays as `[]` — and carries a `**Scanning guidance:**` block, matching the convention SKILL.md establishes for high-false-positive rules (TEST-1, ERR-5, TEST-11). Also added: an `unwrap`ped `get` is the same panic with more ceremony, not a fix.

### 6. `split_at_checked` instead of `split_at`

- **Status:** Approved (merged into #5)
- **Reasoning:** Same failure family as #5 — one rule, not two. The article's specific observation is worth keeping: `split_at` is widely assumed to saturate, and `[1,2,3].split_at(4)` panics rather than returning the slice plus an empty tail.
- **Rust version:** `split_at_checked` stable since **1.80** — below the 1.87 baseline, but the rule notes the MSRV dependency (API-15) since individual projects may sit lower.
- **Target:** ERR-16.

### 7. Make invalid states unrepresentable (`ssl: bool` + `ssl_cert: Option<String>`)

- **Status:** Approved (as enhancement)
- **Reasoning:** *Worth Adding* — partial. The **principle** is already the skill's stated Design Philosophy ("use types to represent states, not flags") and PATTERN-1 covers the typestate form. What is new is the specific **scan signal**: a `bool` field sitting next to the `Option` field it gates, where `(true, None)` is representable. PATTERN-1's existing scan signal covers the `Option`-always-`Some` variant split, not the correlated-flag shape.
- **Target:** PATTERN-1 scan signal (`rules-core.md`), plus an `anti-patterns.md` entry.
- **Modification:** noted that this shape needs an **enum**, not a type parameter — reaching for typestate here would be over-engineering, and PATTERN-1's own cost caveat already warns against that.

### 8. Handle `Default` carefully — derived zeros can be invalid states

- **Status:** Approved — **fills a gap**
- **Reasoning:** *Makes Sense* yes; *Worth Adding* yes. A real gap with a mild inconsistency behind it: DUP-7 and API-4 both **recommend** `Default` for reducing initialization duplication, and nothing anywhere warned that the derived value can be an invalid state. TRAIT-4 already carries the "derive with intent" philosophy and is the natural home.
- **Target:** TRAIT-4 (`rules-core.md`) enhancement, plus an `anti-patterns.md` entry.
- **Modification / correction:** the article's example is right but its fix is thin. Extended with: `unwrap_or_default()` and `Default`-bounded generics as the additional exposure routes the article misses; the builder-vs-`Default` split; and the durable field-level fix (`NonZero<u16>`, a `Port` newtype) that makes the wrong derive a compile error rather than a wrong value. Note that `#[default]` is an **enum-variant** attribute — the article's structure implies per-field struct defaults, which `#[derive(Default)]` does not support; the rule states this precisely.

### 9. Implement `Debug` safely — don't leak secrets; destructure to catch new fields

- **Status:** Approved (the destructuring technique) / Rejected (the leak itself)
- **Reasoning:** The leak is **already expressed** — SEC-5, SEC-21, TRAIT-4, and the SEC-5 detection heuristics all name `Debug` derive on secret-bearing types. The **destructuring technique** is genuinely new and specific: writing `let DatabaseUri { scheme, user, password: _, host, database } = self;` makes the compiler fail when a field is added, where the `self.field` form silently keeps printing the stale subset.
- **Target:** SEC-5 (`rules-security.md`).
- **Modification:** the article presents this as guarding against forgetting to *print* a new field. Both failure directions are stated in the integrated text — the added field is either leaked or silently omitted, depending on which mistake was made — since the leak direction is the one that matters for a security rule. Also added the per-field redaction pattern (a `Password` newtype whose `Debug` writes `[REDACTED]`, so the enclosing struct keeps a useful derive) and **`Serialize` as the forgotten half**, which the article mentions separately but which belongs with `Debug`.

### 10. Careful with serialization — `#[serde(try_from = "FromType")]` for validation

- **Status:** Approved — **fills a gap** (strongest single item in the source)
- **Reasoning:** *Makes Sense* yes; *Still Valid* yes; *Worth Adding* yes. This closes a real hole between two existing rules: API-2 requires a validated newtype to have a private field and a fallible constructor, and SEC-11 requires validation at boundaries — but nothing said that **`#[derive(Deserialize)]` constructs the value field-by-field without ever calling that constructor**, voiding the invariant for exactly the untrusted input it existed to check.
- **Target:** API-2 (`rules-structure.md`), appended to the "a newtype that encodes an invariant must enforce it" paragraph, plus an `anti-patterns.md` entry and a SKILL.md scan row.
- **Modification:** generalized beyond the article — the same bypass exists for `Default` (cross-referenced to TRAIT-4), `From`, `arbitrary`, and zero-copy readers such as `rkyv`, and for a plain `pub` field which needs no derive at all. Added `#[serde(into = "String")]` as the symmetric serialize-direction knob, a cross-reference to ERR-14 for the resulting error's field path, and a concrete scan signal (validating constructor + `Deserialize` in the derive list + no `try_from` attribute).
- **Dropped:** the article's `#[serde(default)]` example. Its claim — that `#[serde(default)]` on a `String` "accepts empty strings when deserializing" — is trivially true of any `String` field and is not what `#[serde(default)]` does wrong; the framing muddles a real point about missing-vs-empty with an unrelated attribute.

### 11. TOCTOU — open first, then check the handle

- **Status:** Approved (as enhancement)
- **Reasoning:** *Worth Adding* — partial. **Already expressed:** SEC-25 covers TOCTOU, `create_new`, and "handle-based APIs where available". The article adds three things SEC-25 lacked: the **symlink-swap** mechanism that makes the race exploitable rather than merely racy, the concrete `O_NOFOLLOW | O_DIRECTORY` recipe via `OpenOptionsExt::custom_flags`, and **CVE-2022-21658** — a bug in `std::fs::remove_dir_all` itself, which is the argument that stops this being dismissed as theoretical.
- **Target:** SEC-25 (`rules-security.md`), plus an `anti-patterns.md` entry.
- **Modification:** added `cap-std` and `rustix` as the crates that make handle-relative operations the default rather than a hand-rolled `custom_flags` call, and stated the underlying principle explicitly — check *the handle*, never re-resolve the path.

### 12. Constant-time comparison for sensitive data

- **Status:** Rejected
- **Reasoning:** *Worth Adding* fails. **Already expressed:** SEC-7, naming the same crate and trait (`subtle::ConstantTimeEq`). The article adds nothing.

### 13. Don't accept unbounded input (`MAX_REQUEST_SIZE`)

- **Status:** Rejected
- **Reasoning:** *Worth Adding* fails. **Already expressed:** SEC-33 (bound resource consumption on untrusted input) and SEC-11 (size limits and max nesting depth on deserialization). Both are more thorough than the article's single constant.

### 14. `Path::join` with an absolute path silently replaces the base

- **Status:** Approved — **fills a gap**
- **Reasoning:** *Makes Sense* yes; *Still Valid* yes (behaviour is documented and stable, and will not change); *Worth Adding* yes. SEC-14 covered path traversal generically — canonicalize and validate against roots — but never named this footgun, and `clippy::join_absolute_paths` appeared nowhere in the skill. It is a direct traversal vector whenever the joined segment is user-controlled, and it produces neither an error nor a panic.
- **Target:** SEC-14 (`rules-security.md`), plus an `anti-patterns.md` entry and a SKILL.md scan row.
- **Modification:** the article ends at "be aware of this behavior", which is not a review rule. Made actionable: `PathBuf::push` has the same behaviour; the check is `is_absolute()` **plus** `Component::RootDir` / `ParentDir` / `Prefix` rejection — a literal `".."` string check is insufficient — followed by canonicalization against the allowed root. Noted that `clippy::join_absolute_paths` fires only on literal arguments, so it is a floor rather than the check; the article's clippy list implies it covers the case.

### 15. Clippy lint set for these issues

- **Status:** Approved (partial) — see "Source errors caught"
- **Reasoning:** *Worth Adding* — partial. ARCH-11 already prescribes a lint baseline (compiler lints off by default, the major clippy groups, six restriction lints). Five lints from the article's list are genuinely useful and absent: `indexing_slicing`, `join_absolute_paths`, `unchecked_duration_subtraction`, `integer_division`, `arithmetic_side_effects`.
- **Target:** ARCH-11 (`rules-structure.md`), as an explicitly-labelled **second restriction tier**.
- **Modification — important:** the article's claim that "`cargo clippy` will catch all issues at compile time 😎" is misleading, and adopting its lint block verbatim would be actively harmful. These are `restriction` lints precisely because they fire on correct code as readily as wrong code; the article sets most of them to `deny`. The integrated text states the noise cost, recommends per-crate adoption at `warn` with scoped `#[expect(…, reason = "…")]` (READ-10), and cross-references ARCH-18's prohibition on crate-wide `deny`.

### 16. `cargo-geiger` for unsafe code in dependencies

- **Status:** **Needs clarification** — not integrated
- **Reasoning:** *Makes Sense* yes — measuring the `unsafe` surface of a dependency tree is a legitimate supply-chain signal, and SEC-27/SEC-28 cover advisories and licensing but not this. *Still Valid* is the problem: `cargo-geiger` has a history of long maintenance gaps and of breaking against newer toolchains and Cargo metadata formats, and its output (a raw count of `unsafe` expressions) is easy to over-read — a high count in a well-audited crate like `bytes` or `tokio` means nothing on its own.
- **Question for you:** do you want a dependency-`unsafe`-surface rule at all? If so, should it name `cargo-geiger`, or point at `cargo-vet` / `cargo-crev` (human review attestations, actively maintained) as the better-supported answer to the same question? I did not want to add a tool recommendation that may not run on a current toolchain.

### 17. "Enable overflow checks in release" as a general recommendation

- **Status:** **Needs clarification** — integrated conditionally
- **Reasoning:** Integrated into SEC-15 as a **conditional** ("where the workload can absorb the cost"), not as a blanket recommendation. The article presents it as a near-free win backed by a benchmark link; the honest position is that the cost is workload-dependent and that a panic is a failure mode, not a fix.
- **Question for you:** should this be a **finding-generating** check for the projects you review — i.e. "a service handling untrusted numeric input with no `overflow-checks` in its release profile is a finding" — or reference material only? It is currently the latter. The answer probably depends on whether your services run with `panic = "abort"`, where enabling it converts a wraparound into a process kill.

---

## Source errors caught (not propagated)

Two miscategorizations in the article's clippy section were identified during technical validation and excluded:

1. **`clippy::serde_api_misuse` filed under "Serialization issues"** — this lint catches incorrect *implementations* of serde's `Visitor`/`Deserialize` API (e.g. implementing `visit_string` without `visit_str`). It has nothing to do with `#[serde(default)]` or with the credential-leak example it is placed under.
2. **`clippy::uninit_vec` filed under "Unbounded input"** — this lint catches `set_len` on a `Vec` with uninitialized elements (the article's own final example). It is a memory-safety lint, unrelated to input bounding; SEC-33/SEC-11 own that topic and no lint enforces them.

Neither was integrated. The lint names themselves are real and correct — only the article's categorization is wrong.

---

## Out-of-band correction (disclosed)

While integrating #9, I found that **SEC-6 named a stale crate API**: it read "`secrecy::Secret<T>` prevents logging/copying secrets", but `secrecy` 0.10 renamed `Secret<T>` to `SecretBox<T>` (retaining `SecretString`). A review skill naming a type that no longer exists produces findings whose suggested fix does not compile.

This is not from the article. I fixed it rather than leaving it, and made the guidance **version-conditional** (0.8 vs 0.10+) with an instruction to check `Cargo.toml` before filing — matching how SEC-10 already handles the equivalent `rand` `OsRng`/`SysRng` rename. Flagging it so the change is visible rather than buried in the diff; revert it if you would rather handle crate-version drift as a separate sweep.

---

## Summary

### Approved (9)

| Item | Target | Kind |
|------|--------|------|
| `overflow-checks` release profile + checked/saturating/wrapping intent | SEC-15 | Enhancement |
| `as` vs `From` vs `TryFrom` decision rule + four cast clippy lints | SEC-15 | Enhancement |
| Panicking indexing on untrusted indices; `get`, `split_at_checked` | **ERR-16 (new)** | New rule |
| `bool` flag beside the `Option` it gates | PATTERN-1 scan signal | Enhancement |
| `#[derive(Default)]` producing invalid states | TRAIT-4 | Enhancement |
| Destructuring hand-written `Debug`; `Serialize` as the forgotten leak | SEC-5 | Enhancement |
| Derived `Deserialize` bypassing the validating constructor | API-2 | Enhancement |
| Symlink-swap TOCTOU; handle-first, `O_NOFOLLOW`, CVE-2022-21658 | SEC-25 | Enhancement |
| `Path::join` absolute-segment replacement | SEC-14 | Enhancement |
| Second restriction lint tier (5 lints, with noise caveat) | ARCH-11 | Enhancement |

### Rejected (6)

| Item | Reason |
|------|--------|
| Integer overflow / checked arithmetic (core claim) | Already expressed — SEC-15 |
| Bounded types / `NonZero` for numeric values | Already expressed — API-2, VER-9 |
| Newtype instead of primitives for business logic | Already expressed — API-2, API-1, anti-patterns |
| Constant-time comparison | Already expressed — SEC-7 |
| Unbounded input / `MAX_REQUEST_SIZE` | Already expressed — SEC-33, SEC-11 |
| `Debug` derive leaking secrets (the leak itself) | Already expressed — SEC-5, SEC-21, TRAIT-4 |

### Needs clarification (2)

1. `cargo-geiger` — maintenance status uncertain; is a dependency-`unsafe`-surface rule wanted, and if so should it name `cargo-vet`/`cargo-crev` instead?
2. `overflow-checks = true` — reference material (current state) or a finding-generating check for services handling untrusted numeric input?

---

## Updated files

| File | Change |
|------|--------|
| `references/rules-core.md` | **New ERR-16** (indexing panics, with scanning guidance); TRAIT-4 extended with `Default`-as-semantic-claim; PATTERN-1 scan signal extended with the correlated-flag shape |
| `references/rules-security.md` | SEC-5 (`Serialize` leak, per-field redaction, destructuring `Debug`); SEC-6 (crate-version correction — see disclosure); SEC-14 (`Path::join`); SEC-15 (`overflow-checks`, cast lints, conversion decision rule); SEC-25 (symlink swap, handle-first, CVE) |
| `references/rules-structure.md` | API-2 (derived `Deserialize` bypass, `#[serde(try_from)]`); ARCH-11 (second restriction lint tier) |
| `references/anti-patterns.md` | 7 new entries across Type Safety (3) and Security (4) |
| `SKILL.md` | 9 new Scan Checklist rows |

No rule IDs were retired or renumbered; ERR-16 is the only new ID. Cross-references were added in both directions (ERR-16 ↔ ARCH-11/SEC-33, SEC-14 ↔ ARCH-11, API-2 ↔ TRAIT-4/SEC-11/ERR-14) and all resolve to existing rules.
