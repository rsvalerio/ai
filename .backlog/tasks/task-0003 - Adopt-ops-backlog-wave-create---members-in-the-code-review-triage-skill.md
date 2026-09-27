---
id: TASK-0003
title: 'Adopt ops backlog wave create --members in the code-review-triage skill'
status: Done
assignee: []
created_date: '2026-09-26 22:00'
updated_date: '2026-09-27 20:54'
labels:
  - skills-integration
  - waves
dependencies: []
modified_files:
  - skills/code-review-triage/SKILL.md
priority: low
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**Skill**: `code-review-triage` (`skills/code-review-triage/SKILL.md`)

**What**: `ops backlog wave create <title> --members <ids>`, added in rsvalerio/ops PR #70 (ops TASK-2296), creates the wave parent (marker label, dependencies) and links every member (parent_task_id, status To Do) in one validated step. The code-review-triage skill still issues one `task create` plus one `task edit` per member.

**Why it matters**: until the skill switches, the N+1-write failure mode that ops TASK-2296 removed (a member missing its parent link or status flip) can still happen in practice.

**Prerequisite**: an ops release that includes PR #70. Closely related to TASK-0002, which switches the same skills to the other new ops commands; they can land together.

**Origin**: moved from rsvalerio/ops TASK-2307 (discovered during ops TASK-2305 while fixing TASK-2296).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 code-review-triage creates each wave with ops backlog wave create --members (falling back to task create/edit only for an ops binary without it)

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Delivered in PR #20 (commit 96faa26): code-review-triage creates each wave with `ops backlog wave create <title> --members … --modified-file …`.
AC substitution: no fallback to task create/edit was kept. Instead the skill requires ops >= 0.72.0 (which ships `wave create`) and stops with a clear message on an older binary, so the "ops without wave create" case cannot occur. One code path instead of two.
<!-- SECTION:NOTES:END -->
