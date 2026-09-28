---
id: TASK-0008
title: 'Derive the build-fast and clippy-pedantic apply templates from the shared Rust foundation'
status: Done
assignee: []
created_date: '2026-09-28 10:59'
updated_date: '2026-09-28 15:39'
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
- [x] #1 The templates reference or are generated from the shared foundation; no divergent copy remains

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Per forge TASK-0025's decision, the foundation templates live in ops (ops TASK-2330): derive apply-config.md and apply-templates.md from ops's embedded templates rather than a forge copy.

Blocked 2026-09-28: ops TASK-2330 (embedded foundation templates) is still in Triage and ops 0.72.0 embeds none (`ops init` writes only .ops.toml). Nothing to derive from yet; revisit once ops ships the templates and the scaffold/drift command, then replace apply-config.md and apply-templates.md with references to it and raise the ops floor.

Unblocked by ops v0.74.0 (ops TASK-2330, PR #78: `ops init --rust` / `--check`). rust-make-clippy-pedantic: apply-config.md no longer carries the lint tables or clippy.toml; the foundation is rendered with `ops init --rust` into a scratch crate (never the repo, since the scaffold also writes rustfmt.toml/deny.toml/nextest.toml), missing files/tables are written from the render, existing ones get only what `ops init --rust --check` reports as drift (clippy.toml:*, Cargo.toml:[workspace.]lints.*, <member>/Cargo.toml:lints.workspace); msrv stays the repo's own value. Owner decisions 2026-09-28: the sweep's -W flags are derived from the rendered lint tables (script in lint-catalog.md), so the sweep now also covers the foundation's named restriction lints; `-W clippy::cargo` and its multiple_crate_versions suppression were dropped to match the foundation. rust-make-build-fast: nextest-leak-timeout takes its value from the render and writes only leak-timeout per --check drift; gate templates already edit relative to ops stack built-ins, and the test profile is a rule the foundation deliberately does not template. ops floor raised to 0.74.0 in every skill preflight, README, AGENTS.md and ci.yml setup-ops.

<!-- SECTION:NOTES:END -->
