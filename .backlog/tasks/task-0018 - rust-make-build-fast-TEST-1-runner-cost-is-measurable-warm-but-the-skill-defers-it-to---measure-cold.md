---
id: TASK-0018
title: 'rust-make-build-fast: TEST-1 runner cost is measurable warm, but the skill defers it to --measure-cold'
status: Done
assignee: []
created_date: '2026-10-03 09:23'
updated_date: '2026-10-03 10:59'
labels:
  - rust
  - dogfood
dependencies: []
modified_files:
  - plugins/dev/skills/rust-make-build-fast/references/checks.md
  - plugins/dev/skills/rust-make-build-fast/references/measurement.md
priority: medium
ordinal: 1000
dedup_key: 'followup:bf-test1-warm-measure'
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**What**: checks.md gives TEST-1's default-mode cost as unmeasured and puts the runner comparison under `--measure-cold`. With the test binaries already built it needs no cold build: on dbsec, three runs of each runner took under a minute in total (cargo test 9.5s, nextest 6.9s median). Left unmeasured, the task got the placeholder medium priority where the measured cost made it low, and Step 9's compare-against-recorded-cost had nothing to compare with after `--apply`.

**How**: when `--no-run` shows both runners' binaries are up to date, time the suite under each in default mode (median of three, per the noise rule) and keep `--measure-cold` for the case where a build is needed.

**Origin: TASK-0011 dogfood run on dbsec, 2026-10-03 (branch dogfood/task-0011 there).**
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 TEST-1 in checks.md and the probe table in measurement.md describe the warm runner timing and when it applies
- [x] #2 ops verify passes

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Fixed on fix/rust-make-dogfood-followups. measurement.md gained a 'Runner comparison' default-mode probe: it runs only when nextest is installed, the warm build covered the test targets (--all-targets, the gate step's features, no PROF-2 divergence), and --no-run under each runner compiles nothing. It times the gate's test step against next (+ test-doc when the template adds it), median of three, or a single run per side above 60s. TEST-1's default-mode cost is now the difference of the medians; inside the noise band nothing is filed. --measure-cold keeps the case where the binaries need a build. SKILL.md Step 4 points at it and allowed-tools gained 'cargo test'. The conditions and the 60s cut-off are my choices, not from the dbsec run.
<!-- SECTION:NOTES:END -->
