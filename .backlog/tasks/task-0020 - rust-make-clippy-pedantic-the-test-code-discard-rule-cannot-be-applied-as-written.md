---
id: TASK-0020
title: 'rust-make-clippy-pedantic: the test-code discard rule cannot be applied as written'
status: Done
assignee: []
created_date: '2026-10-03 09:23'
updated_date: '2026-10-03 10:55'
labels:
  - rust
  - dogfood
dependencies: []
modified_files:
  - plugins/dev/skills/rust-make-clippy-pedantic/SKILL.md
  - plugins/dev/skills/rust-make-clippy-pedantic/references/extraction.md
priority: high
ordinal: 1000
dedup_key: 'followup:ped-test-discard-rule'
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**What**: Step 4 drops "test-only style findings", names three lints with "such as", then says "a finding that disappears when test code is excluded is not filed". The two readings differ by hundreds of rows: on dbsec 654 of 1,027 findings sat in test code, of which only 338 were the four lints with an `allow-*-in-tests` key; the rest were `arithmetic_side_effects`, `as_conversions`, casts and so on, which the applied policy still fires on. The run took the broad reading. There is also no row field for `#[cfg(test)]` modules: `targetKind` is `lib` for them, so 160 rows needed a hand-rolled line-range heuristic.

**How**: state one rule (every finding in test code, or exactly the lints with an in-tests key) and give the mechanical test for "in test code" — ideally a field from `ops clippy-findings`, otherwise a documented heuristic.

**Origin: TASK-0011 dogfood run on dbsec, 2026-10-03 (branch dogfood/task-0011 there).**
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Step 4 gives one unambiguous discard rule and a mechanical way to decide whether a row is in test code
- [x] #2 ops verify passes

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Fixed on fix/rust-make-dogfood-followups. One rule: nothing is discarded for being in test code. The pedantic pass now runs with CLIPPY_CONF_DIR pointing at the clippy.toml Step 7 would write, built in scratch, so Clippy itself applies the four allow-*-in-tests keys (and the foundation thresholds, which the sweep was also missing). Every remaining row is filed because the applied policy fires on it. No ops change needed; checked on a scratch crate that the override reaches Clippy through ops clippy-findings and exempts a cfg(test) helper but not a non-#[test] helper in tests/. Step 7's --apply procedure moved to apply-config.md to keep SKILL.md under the 5,000-token limit. Not re-run on dbsec.
<!-- SECTION:NOTES:END -->
