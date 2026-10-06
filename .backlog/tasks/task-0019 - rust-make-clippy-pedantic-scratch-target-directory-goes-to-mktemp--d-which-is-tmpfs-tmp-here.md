---
id: TASK-0019
title: 'rust-make-clippy-pedantic: scratch target directory goes to mktemp -d, which is tmpfs /tmp here'
status: Done
assignee: []
created_date: '2026-10-03 09:23'
updated_date: '2026-10-03 10:59'
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
- [x] #1 SKILL.md Step 2 places the scratch target on real disk, verifies it is not tmpfs, and says when it is deleted
- [x] #2 ops verify passes

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Fixed on fix/rust-make-dogfood-followups. Step 2 creates the scratch directory under ${XDG_CACHE_HOME:-$HOME/.cache}/rust-make-clippy-pedantic, checks targetDir.tmpfs with 'ops about machine --json' before the first build (confirmed it reports correctly for a target path that does not exist yet), stops if it is tmpfs, and deletes the directory at the end of the run: after the Step 6 report, after Step 7's verification under --apply, or after an error is reported. allowed-tools gained 'ops about machine' and 'rm -rf'. The scan-signal table moved to estimation.md to pay for the added text under the 5,000-token limit.
<!-- SECTION:NOTES:END -->
