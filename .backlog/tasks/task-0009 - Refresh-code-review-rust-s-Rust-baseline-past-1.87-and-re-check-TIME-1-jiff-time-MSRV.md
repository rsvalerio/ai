---
id: TASK-0009
title: 'Refresh code-review-rust''s Rust baseline past 1.87 and re-check TIME-1 (jiff, time MSRV)'
status: Done
assignee: []
created_date: '2026-09-29 13:35'
updated_date: '2026-09-29 17:21'
labels:
  - rust
  - rules
  - rust-meta
dependencies: []
modified_files:
  - plugins/dev/skills/code-review-rust/references/rules/index.md
  - plugins/dev/skills/code-review-rust/references/scan-checklist.md
priority: medium
ordinal: 1000
dedup_key: 'followup:rust-baseline-refresh'
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**What**: code-review-rust's ingestion baseline is still Rust 1.87. The follow-ups in reports/rust-meta-evaluation-2026-08-25-chrono.md are coming due: (1) the baseline was already five months since its last review in August; (2) TIME-1 quotes an MSRV for the `time` crate, which drifts (1.83 → 1.88 over 0.3.45–0.3.55); (3) `jiff` should be promoted above `chrono` for new code if it has reached 1.0 with its zoned-arithmetic API intact.

**How**: run rust-meta over the Rust release notes since 1.87 and over the current jiff and time releases, and fold the approved changes into the rule category files, rules/index.md and (if a signal changes) scan-checklist.md.

**Origin**: 'what next' review, 2026-09-29.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Baseline bumped to the current stable Rust, with a rust-meta evaluation report under reports/
- [x] #2 TIME-1 re-checked: time MSRV figure current, jiff's position decided against its 1.0 status
- [x] #3 make validate-rules and ops verify pass

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Report: reports/rust-meta-evaluation-2026-09-29-baseline-1.98.md. Baseline 1.98+ (1.98.1 current stable). 7 corrections (TEST-29 import path E0432, VER-9 dates, PERF-8 hasher, let-chains edition, async-std discontinued, OWASP note, TIME-1 wording), 17 additions incl. new VER-10..14; every API compile-verified on rustc 1.98. jiff still 0.2.37: promotion not triggered. OWASP 2025 migration split out as TASK-0013. 7 items left as Needs Clarification in the report.
<!-- SECTION:NOTES:END -->
