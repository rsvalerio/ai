---
id: TASK-0022
title: 'rust-make-clippy-pedantic: task fields the run cannot fill — lint group, effort class, help text'
status: Done
assignee: []
created_date: '2026-10-03 09:23'
updated_date: '2026-10-03 11:01'
labels:
  - rust
  - dogfood
dependencies: []
modified_files:
  - plugins/dev/skills/rust-make-clippy-pedantic/SKILL.md
  - plugins/dev/skills/rust-make-clippy-pedantic/references/lint-catalog.md
priority: medium
ordinal: 1000
dedup_key: 'followup:ped-unfillable-fields'
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**What**: three fields had no source on the dbsec run. (1) The task label and severity need the lint's group, but lint-catalog.md has no lint-to-group mapping and the v2 row carries none, so pedantic versus nursery was decided from memory. (2) Twelve of the 37 lints that fired in production code are in no effort class (`use_self`, `future_not_send`, `significant_drop_tightening`, `too_long_first_doc_paragraph`, …); the catalog defaults only *named* lints to Class J, so the estimate guessed. (3) The task template's Fix sketch asks for "the clippy help text", which the normalized row does not include.

**How**: add a default class for an uncatalogued group lint, a way to resolve the group (a row field, or `cargo clippy --explain`), and either a `help` field in the row or a template that does not ask for it.

**Origin: TASK-0011 dogfood run on dbsec, 2026-10-03 (branch dogfood/task-0011 there).**
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 lint-catalog.md defines the group lookup and a default effort class, and the SKILL.md task template only asks for fields the row provides
- [x] #2 ops verify passes

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Fixed on fix/rust-make-dogfood-followups. (1) Group: lint-catalog.md has a 'Lint groups' section that builds $SCRATCH/lint-groups.json from 'clippy-driver -W help' of the installed toolchain (822 lints on clippy 1.98 here, each in exactly one group); 'cargo clippy --explain' turned out not to print the group. (2) Effort: a 'Default class by group' table (style/complexity/perf/pedantic M; nursery, correctness, suspicious, restriction J), and the report lists every lint classed by default. The four lints the task names were placed: use_self M, too_long_first_doc_paragraph D, significant_drop_tightening and future_not_send J. The defaults are my judgement. (3) The task template's Fix sketch no longer asks for help text; a non-negotiable says every field comes from the row, the group lookup or the catalog, and points at 'cargo clippy --explain'. No ops change.
<!-- SECTION:NOTES:END -->
