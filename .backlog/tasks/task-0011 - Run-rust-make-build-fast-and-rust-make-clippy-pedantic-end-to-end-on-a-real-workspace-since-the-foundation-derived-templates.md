---
id: TASK-0011
title: 'Run rust-make-build-fast and rust-make-clippy-pedantic end to end on a real workspace since the foundation-derived templates'
status: Done
assignee: []
created_date: '2026-09-29 13:35'
updated_date: '2026-10-03 09:23'
labels:
  - rust
  - build-performance
  - dogfood
dependencies: []
modified_files:
  - plugins/dev/skills/rust-make-build-fast/SKILL.md
  - plugins/dev/skills/rust-make-clippy-pedantic/SKILL.md
priority: medium
ordinal: 1000
dedup_key: 'followup:rust-skills-dogfood'
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**What**: TASK-0008 moved both skills' --apply templates onto the ops Rust foundation (ops init --rust rendered into scratch, ops init --rust --check for drift). Neither skill has been run end to end since.

**How**: run each skill on event0 or dbsec, first survey-only, then --apply on a scratch branch. Check that filed tasks carry measured cost, date and machine load (build-fast) or the pedantic label with aggregation over 20 (clippy-pedantic), and that --apply writes only what ops init --rust --check reports missing.

**Origin**: 'what next' review, 2026-09-29.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 rust-make-build-fast run survey-only and with --apply on a real workspace; findings reviewed
- [x] #2 rust-make-clippy-pedantic run survey-only and with --apply on a real workspace; findings reviewed
- [x] #3 Any skill defect found is filed as its own task here

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Run on dbsec at 5899d6b, 2026-10-03, on branch dogfood/task-0011 there (two local commits, not pushed; main untouched). build-fast: survey filed one finding (BF-TEST-1, dbsec TASK-1141); --apply swapped test for next in qa, ops qa passed, nextest 6.9s vs cargo test 9.5s. clippy-pedantic: 1,027 warnings, 654 in test code dropped, 200 tasks filed (3 aggregates), refiling printed Exists for all 200; --apply wrote nothing because every missing lint is waived in dbsec. Defects filed: TASK-0017 to TASK-0022.
<!-- SECTION:NOTES:END -->
