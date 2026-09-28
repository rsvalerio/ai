---
id: TASK-0007
title: 'SHA-pin this repo''s GitHub Actions'
status: Done
assignee: []
created_date: '2026-09-28 10:59'
updated_date: '2026-09-28 17:02'
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
- [x] #1 Every third-party action is pinned to a full SHA with a version comment, enforced by the shared lint once it exists

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Pinned actions/checkout v7.0.1, jdx/mise-action v4.3.0 (same SHAs as forge) and actions/setup-node v7.0.0 in ci.yml. forge's ci/lint.sh pinned-actions is repo-local, so scripts/validate-actions.py mirrors its regex and exemptions as `make validate-actions` (in make ci and ops verify); swap it for the shared lint once forge ships one consumers can call. Existing .github/dependabot.yml moves SHA + comment together.

Shared lint adopted: ops 0.75.0's `ops lint-actions` built-in (ops TASK-2328) replaces scripts/validate-actions.py in `ops verify`; it also rejects `secrets: inherit`. setup-ops is now SHA-pinned with a `# v0.5.0` comment (forge v1 = v0.5.0) so Dependabot moves it; CI installs ops 0.75.0.

<!-- SECTION:NOTES:END -->
