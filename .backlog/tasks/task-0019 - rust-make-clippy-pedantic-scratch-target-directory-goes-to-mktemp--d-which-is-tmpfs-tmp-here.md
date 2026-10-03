---
id: TASK-0019
title: 'rust-make-clippy-pedantic: scratch target directory goes to mktemp -d, which is tmpfs /tmp here'
status: To Do
assignee: []
created_date: '2026-10-03 09:23'
labels:
  - rust
  - dogfood
dependencies: []
modified_files:
  - plugins/dev/skills/rust-make-clippy-pedantic/SKILL.md
priority: medium
ordinal: 1000
dedup_key: 'followup:ped-scratch-tmpfs'
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**What**: Step 2 sets `SCRATCH=$(mktemp -d)` and builds into `$SCRATCH/target`. On this machine that is a 16 GB tmpfs. rust-make-build-fast forbids exactly this (ENV-1, measurement.md: never under /tmp, check `targetDir.tmpfs`). The dbsec lint target was 785 MB so nothing failed, but a larger workspace fills the tmpfs and cargo exits 101 with no compile error.

**How**: put the scratch target under `${XDG_CACHE_HOME:-$HOME/.cache}` as build-fast does, check it with `ops about machine --json`, and delete it at the end; the skill currently never says to remove the scratch directory.

**Origin: TASK-0011 dogfood run on dbsec, 2026-10-03 (branch dogfood/task-0011 there).**
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 SKILL.md Step 2 places the scratch target on real disk, verifies it is not tmpfs, and says when it is deleted
- [ ] #2 ops verify passes
<!-- AC:END -->
