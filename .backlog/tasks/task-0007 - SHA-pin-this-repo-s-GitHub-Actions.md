---
id: TASK-0007
title: 'SHA-pin this repo''s GitHub Actions'
status: Triage
assignee: []
created_date: '2026-09-28 10:59'
labels:
  - ci
  - security
dependencies: []
modified_files: []
priority: low
ordinal: 1000
dedup_key: 'ops-align:ai-pin-actions'
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**What**: ci.yml uses tag refs (`@v7`, `@v4`), unlike forge README rule 6 which the owner's other repos follow.

**Origin**: ops-alignment survey of forge, ops and ai, 2026-09-28.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Every third-party action is pinned to a full SHA with a version comment, enforced by the shared lint once it exists
<!-- AC:END -->
