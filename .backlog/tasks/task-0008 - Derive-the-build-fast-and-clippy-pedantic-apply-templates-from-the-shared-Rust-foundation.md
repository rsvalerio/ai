---
id: TASK-0008
title: 'Derive the build-fast and clippy-pedantic apply templates from the shared Rust foundation'
status: Triage
assignee: []
created_date: '2026-09-28 10:59'
updated_date: '2026-09-28 13:52'
labels:
  - ops-alignment
dependencies: []
modified_files: []
priority: low
ordinal: 1000
dedup_key: 'ops-align:ai-foundation-templates'
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**What**: rust-make-build-fast (apply-templates.md: gate-nextest, gate-staged, nextest.toml, test profile) and rust-make-clippy-pedantic (apply-config.md: clippy.toml keys, `[workspace.lints]`) carry their own copies of the foundation config.

**Why it matters**: one source per practice; see forge TASK-0025 and forge TASK-0028.

**Origin**: ops-alignment survey of forge, ops and ai, 2026-09-28.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The templates reference or are generated from the shared foundation; no divergent copy remains
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Per forge TASK-0025's decision, the foundation templates live in ops (ops TASK-2330): derive apply-config.md and apply-templates.md from ops's embedded templates rather than a forge copy.
<!-- SECTION:NOTES:END -->
