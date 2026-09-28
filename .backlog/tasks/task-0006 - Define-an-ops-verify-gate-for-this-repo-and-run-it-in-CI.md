---
id: TASK-0006
title: 'Define an ops verify gate for this repo and run it in CI'
status: Triage
assignee: []
created_date: '2026-09-28 10:59'
labels:
  - ci
  - ops-alignment
dependencies: []
modified_files: []
priority: medium
ordinal: 1000
dedup_key: 'ops-align:ai-ops-verify'
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**What**: the dev skills assume every repo exposes `ops verify` as its QA gate, but this repo's `.ops.toml` has only `[backlog]`; CI runs `make check-tools`/`fmt-check`/`lint-check`/`validate` directly.

**Why it matters**: the repo should follow the convention its skills impose; CI can then use forge TASK-0023 + `ops verify`.

**Origin**: ops-alignment survey of forge, ops and ai, 2026-09-28.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `.ops.toml` defines `verify` over the make targets
- [ ] #2 CI runs `ops verify` via forge setup-ops
<!-- AC:END -->
