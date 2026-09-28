---
id: TASK-0006
title: 'Define an ops verify gate for this repo and run it in CI'
status: Done
assignee: []
created_date: '2026-09-28 10:59'
updated_date: '2026-09-28 14:27'
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
- [x] #1 `.ops.toml` defines `verify` over the make targets
- [x] #2 CI runs `ops verify` via forge setup-ops

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
`.ops.toml` defines verify = check-tools, validate (skills), validate-marketplace, validate-rules, validate-actions, fmt-check, lint-check, each a make target (stdout redirected to stderr, since ops shows only a failing step's stderr). ci.yml's Lint/Validate/Marketplace jobs are replaced by one 'ops verify' job using rsvalerio/forge/actions/setup-ops pinned to forge main c6d281a (setup-ops is not yet in forge v1; move to @v1 once released), ops 0.72.0. Follow-up for the owner: the main-protection ruleset still requires Lint and Validate; replace them with 'ops verify'.
<!-- SECTION:NOTES:END -->
