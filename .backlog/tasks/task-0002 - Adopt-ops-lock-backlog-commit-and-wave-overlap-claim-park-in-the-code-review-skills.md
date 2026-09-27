---
id: TASK-0002
title: 'Adopt ops lock, backlog commit and wave overlap/claim/park in the code-review skills'
status: Done
assignee: []
created_date: '2026-09-26 20:01'
updated_date: '2026-09-27 20:54'
labels:
  - skills-integration
  - waves
dependencies: []
modified_files:
  - skills/code-review-run-wave/SKILL.md
  - skills/code-review-run-wave/references/worktree-protocol.md
  - skills/code-review-run-waves/SKILL.md
  - skills/code-review-triage/SKILL.md
priority: medium
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**Skills**: `code-review-run-wave`, `code-review-run-waves`, `code-review-triage`

**What**: rsvalerio/ops TASK-2281/2285/2286/2289 added `ops lock`, `ops backlog commit`, `ops backlog wave overlap` and `ops backlog wave claim/park`, but the skills still run the shell those commands were meant to replace: `mkdir .git/code-review-merge.lock` plus a trap, the ~30-line backlog-lock/stage/diff/commit script, hand-computed Overlaps notes in triage, and `git worktree add -b` plus a separate status edit for claims.

**Why it matters**: until the skills switch, a killed runner still leaves a merge-lock directory behind with no owner info, and triage still does set arithmetic by hand.

**Prerequisite**: an ops release that ships these commands. The ops binary installed on 2026-09-26 still lacks `wave overlap`/`claim`/`park`. If ops TASK-2296 (`wave create --members`) lands, triage can also use it in place of one create plus N edits.

**Origin**: moved from rsvalerio/ops TASK-2295 (discovered during ops TASK-2291 while fixing TASK-2281). The ops-side reference is `docs/backlog.md`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 code-review-run-wave(s) serialize merges and backlog commits with ops lock and ops backlog commit
- [x] #2 code-review-triage computes wave overlap with ops backlog wave overlap --json
- [x] #3 code-review-run-wave claims/parks with ops backlog wave claim/park

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Delivered in PR #20 (commit 96faa26, refactor(code-review-waves)!):
- AC1: merges run as one `ops lock code-review-merge --timeout 3600 -- …` command (rebase, integration verify, ff-merge; conflicts fixed outside the lock); bookkeeping is `ops lock code-review-backlog -- ops backlog commit …`. run-waves checks `ops lock status`.
- AC2: triage and run-waves plan the merge order with `ops backlog wave overlap --json`.
- AC3: run-wave claims with `ops backlog wave claim` and parks with `ops backlog wave park --reason`.
Requires ops >= 0.72.0, checked in each skill's preflight.
<!-- SECTION:NOTES:END -->
