---
id: TASK-0017
title: 'rust-make-build-fast: gate-nextest has no form for a gate the ops stack owns'
status: To Do
assignee: []
created_date: '2026-10-03 09:23'
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
- [ ] #1 apply-templates.md says what gate-nextest writes when the gate is defined by the stack and only extended in .ops.toml
- [ ] #2 ops verify passes
<!-- AC:END -->
