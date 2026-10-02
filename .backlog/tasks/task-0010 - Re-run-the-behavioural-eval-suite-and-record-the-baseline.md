---
id: TASK-0010
title: 'Re-run the behavioural eval suite and record the baseline'
status: Done
assignee: []
created_date: '2026-09-29 13:35'
updated_date: '2026-09-29 18:13'
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
- [x] #1 make eval run on the current Claude Code and model; versions noted
- [x] #2 Per-case with/without/delta recorded in implementation notes
- [x] #3 Any regressed case filed as a separate task

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Run 2026-09-29, Claude Code 2.1.284, default model, make eval grants (Write Edit WebSearch WebFetch), 3+3 runs per case.
- guardrail-rust: with 1.00 / without 0.00, delta +1.00 ($1.14)
- review-rust: with 0.00 / without 0.00, delta 0.00 ($0.42): loads-rust-skill and reads-rule-tiers fail in both arms
- review-web: with 0.50 / without 0.50, delta 0.00 ($0.41): only no-rust-skill passes
- product research-no-profile (earlier today, during TASK-0012): with 1.00 / without 0.20, delta +0.80
review-rust/review-web are identical to the 2026-09-27 run on 2.1.283, so this predates PR #26 and the version bump. Filed as TASK-0014 with the traced cause.
<!-- SECTION:NOTES:END -->
