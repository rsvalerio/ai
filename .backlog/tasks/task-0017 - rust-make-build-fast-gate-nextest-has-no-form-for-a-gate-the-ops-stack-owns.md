---
id: TASK-0017
title: 'rust-make-build-fast: gate-nextest has no form for a gate the ops stack owns'
status: Done
assignee: []
created_date: '2026-10-03 09:23'
updated_date: '2026-10-03 10:58'
labels:
  - rust
  - dogfood
dependencies: []
modified_files:
  - plugins/dev/skills/rust-make-build-fast/references/apply-templates.md
priority: medium
ordinal: 1000
dedup_key: 'followup:bf-gate-nextest-stack-gate'
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**What**: the gate-nextest template edits a `[commands.<gate>] commands = [...]` list. dbsec's `qa` is the stack's composite, extended with `[extend.qa]`, so there is no list in `.ops.toml` to edit. Swapping `test` for `next` forced replacing `[extend.qa]` with a full `[commands.qa]` redefinition, which apply-templates.md says the gate templates never do ("never restate the stack's list"), and which stops following the stack if it later adds a step.

**How**: decide the form for a stack-owned gate (redefinition with a comment saying why, an override of the `test` step, or manual) and write it into the template with the same explain-based check gate-staged has.

**Origin: TASK-0011 dogfood run on dbsec, 2026-10-03 (branch dogfood/task-0011 there).**
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 apply-templates.md says what gate-nextest writes when the gate is defined by the stack and only extended in .ops.toml
- [x] #2 ops verify passes

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Fixed on fix/rust-make-dogfood-followups. Decision: redefinition, kept as small as it can be. For a gate whose composite has origin.source 'stack' in ops explain, gate-nextest writes a [commands.<gate>] holding only the stack's own list with the swap applied, and leaves [extend.<gate>] untouched (checked on a scratch crate: an extension applies to a redefined gate the same way, so the extra steps keep their place). A mandatory comment says why it is a redefinition, which ops version the list came from, and that it no longer follows the stack. Explain-based before/after checks; a failed check makes the task manual. Rejected: overriding [commands.test] to run nextest (changes what 'ops test' means everywhere and restates next's args) and leaving it manual (ops's own repo and the dbsec run both redefine qa). The exception is named in the 'never restate the stack's list' rule and in TEST-1.
<!-- SECTION:NOTES:END -->
