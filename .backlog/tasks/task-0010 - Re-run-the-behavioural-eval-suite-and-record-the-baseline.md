---
id: TASK-0010
title: 'Re-run the behavioural eval suite and record the baseline'
status: To Do
assignee: []
created_date: '2026-09-29 13:35'
labels:
  - evals
dependencies: []
modified_files: []
priority: low
ordinal: 1000
dedup_key: 'followup:eval-rerun'
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**What**: the last recorded make eval runs date from 2026-09-28 (product research-no-profile: with 1.00 / without 0.20). Evals are deliberately not in CI, so a skill that stops loading after a Claude Code or model bump goes unnoticed until someone runs them.

**How**: run make eval (it grants Write, Edit, WebSearch, WebFetch) and note each case's with/without scores and delta in this task's notes. A case whose delta collapses gets its own task.

**Origin**: 'what next' review, 2026-09-29.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 make eval run on the current Claude Code and model; versions noted
- [ ] #2 Per-case with/without/delta recorded in implementation notes
- [ ] #3 Any regressed case filed as a separate task
<!-- AC:END -->
