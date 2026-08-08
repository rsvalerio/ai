# Evaluation Criteria

**Evaluation is the PRIMARY FUNCTION of rust-meta.** Never skip, rush, or deprioritize evaluation. Every piece of extracted knowledge must pass through all phases below before integration.

Evaluate each knowledge/pattern against all three criteria below. This file defines **what** to evaluate; see [integration-workflow](integration-workflow.md) for **how** to integrate approved items.

## Evaluation Phases

Apply these phases in order for each piece of extracted knowledge:

1. **Cross-Reference Check** — Search code-review-rust rules for duplicates, overlaps, conflicts, or complementary content. Identify the relationship: already expressed (reject), similar but adds nuance (flag), conflicts (flag for user), complements (approve with integration point), fills gap (approve)
2. **Rust Version Verification** — Confirm the feature/pattern is stable in current Rust; check edition compatibility (2021/2024); verify crate maintenance status if external crates are mentioned; identify if newer alternatives supersede it
3. **Technical Validation** — Verify correctness of examples and claims; check that code compiles; validate performance claims against benchmarks or credible sources
4. **Value Assessment** — Is it specific and actionable (not generic)? Does it fill a gap or meaningfully enhance existing content? Is it practical for real codebases?

## 1. Makes Sense

Technically sound, clear rationale, actionable, correct and complete examples.

**Reject**: Too generic/obvious, lacks rationale, incorrect or incomplete examples, unclear.

## 2. Still Valid

Compatible with current Rust stable; stable features (not deprecated); applies to the target edition (2021; 2024 for projects that have migrated — check project's `Cargo.toml`; 2015/2018 only for legacy compatibility). No deprecated crates/patterns; no newer alternatives that supersede it. Minimum baseline: Rust 1.87+ (last reviewed: 2026-03-13; review and bump periodically). This baseline applies to knowledge ingestion — individual projects may have a lower MSRV; check `rust-version` in `Cargo.toml`.

**Reject**: Deprecated features/APIs, pre-1.85 only, newer alternatives exist, unmaintained crates.

**Flag**: Version unspecified or may be version-dependent; feature stability unclear.

## 3. Worth Adding

Unique value, specific and actionable, practical, no conflicts, fills a gap or enhances existing content.

**Reject**: Duplicate (already in rules), too similar, conflicts, too generic, not relevant.

**Flag**: Similar but adds nuance; complements existing; needs integration rather than new addition.

## Examples

### Approved

- "`tokio::time::sleep` instead of `std::thread::sleep` in async" → Makes Sense: yes (blocks runtime). Still Valid: yes. Worth Adding: fills gap in CONC rules. → CONC section in rules.md.
- "Batch Tokio tasks to reduce scheduler overhead" → Makes Sense: yes (many small spawns add cost). Still Valid: yes. Worth Adding: complements ASYNC-4 with scheduler context. → ASYNC section in rules.md.

### Rejected

- **Duplicate**: "Avoid `unwrap()` in production" → Already expressed in ERR-5 (with severity adjustment for provably infallible paths). **Already Expressed**: Error Handling section.
- **Outdated**: "Use `try!()` macro for error propagation" → Deprecated since Rust 2018; use `?` operator instead. **Criterion failed**: Still Valid.
- **Conflicts**: "Use `unsafe` blocks for performance" → Generic advice without invariant justification; conflicts with UNSAFE-1--8. **Criterion failed**: Makes Sense (too generic), Worth Adding (conflicts).
- **Superseded**: "Use `lazy_static!` for global state" → Superseded by `std::sync::LazyLock` (stable since Rust 1.80). **Criterion failed**: Still Valid.

### Needs Clarification

- "`parking_lot` for better mutex performance" → Makes Sense: yes. Still Valid: yes, but verify maintenance status and whether `std::sync::Mutex` improvements (Rust 1.62+ fast-path) close the gap. **Action**: check benchmarks, maintenance activity, and whether the delta justifies the dependency. → Flag for user review.
- "Use `io-uring` for file I/O on Linux" → Makes Sense: yes for high-throughput I/O. Still Valid: partial — requires Linux 5.1+ minimum, many features need 5.6+/5.10+. **Action**: verify async runtime compatibility and feature-flag matrix before adding. → Flag for user review.

## Output per piece

- **Status**: Approved | Rejected | Needs Clarification
- **Reasoning**: Which criterion (Makes Sense / Still Valid / Worth Adding) and why
- **Rust Version**: Valid for [version] or concerns
- **Already Expressed**: Section and rule ID if duplicate or similar
- **Target**: Which section in rules.md to update (if approved)
- **Integration Point**: Section or location in target
- **Modifications Needed**: If approved but needs editing before merging (e.g., condensing verbose examples, adjusting terminology to match style, adding cross-references)
