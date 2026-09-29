---
id: TASK-0011
title: 'Run rust-make-build-fast and rust-make-clippy-pedantic end to end on a real workspace since the foundation-derived templates'
status: To Do
assignee: []
created_date: '2026-09-29 13:35'
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
- [ ] #1 rust-make-build-fast run survey-only and with --apply on a real workspace; findings reviewed
- [ ] #2 rust-make-clippy-pedantic run survey-only and with --apply on a real workspace; findings reviewed
- [ ] #3 Any skill defect found is filed as its own task here
<!-- AC:END -->
