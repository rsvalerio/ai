---
id: TASK-0021
title: 'rust-make-clippy-pedantic: foundation waivers are ignored by the survey and leave --apply with no defined outcome'
status: Done
assignee: []
created_date: '2026-10-03 09:23'
updated_date: '2026-10-03 10:56'
labels:
  - rust
  - dogfood
dependencies: []
modified_files:
  - plugins/dev/skills/rust-make-clippy-pedantic/SKILL.md
  - plugins/dev/skills/rust-make-clippy-pedantic/references/apply-config.md
priority: high
ordinal: 1000
dedup_key: 'followup:ped-waivers'
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**What**: dbsec waives every missing foundation lint under `[foundation.waivers]` in `.ops.toml`, with counts and a tracking task. The survey still passed all of them as flags and filed 200 tasks for work the repository already tracks in one. Under `--apply`, `ops init --rust --check` reported only `waived` lines, so apply-config.md's rules write nothing — but Step 7 has no such outcome: its verification expects the configured run to reproduce the pedantic finding set, and a run that reproduces the empty baseline reads as "the policy is inert".

**How**: read the check's `waived` lines before the sweep. Decide whether waived lints are surveyed at all (or filed as one summary task per waiver), report them either way, and give Step 7 an explicit "nothing to write: all drift is waived" result with its own verification.

**Origin: TASK-0011 dogfood run on dbsec, 2026-10-03 (branch dogfood/task-0011 there).**
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 SKILL.md and apply-config.md say how waived lints are surveyed, filed and reported, and Step 7 defines the all-waived outcome
- [x] #2 ops verify passes

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Fixed on fix/rust-make-dogfood-followups. Step 3 saves 'ops init --rust --check' to scratch before the sweep. Decision: a waived lint is not surveyed (no flag; a waived clippy.toml key keeps the repository's value), nothing is filed for it, and every waiver is reported verbatim in a new Step 6 section. Rationale: the sweep enables exactly what --apply writes, and --apply never overrides a waiver. The lint-flags script now takes the check output and skips waived lints; run against dbsec's real check output it leaves 7 of 19 flags. Step 7 gained a 'nothing to write' result (no drift line for clippy.toml, lint tables or member opt-in) verified by the tree check alone, with no rerun. apply-config.md has a new Waivers section. Not re-run end to end on dbsec.
<!-- SECTION:NOTES:END -->
