---
id: TASK-0012
title: 'product-research: unknowns get dropped when the profile''s record format has no room for them'
status: To Do
assignee: []
created_date: '2026-09-29 17:02'
labels:
  - product
  - product-research
  - dogfood
dependencies: []
modified_files:
  - plugins/product/skills/product-research/SKILL.md
  - plugins/product/skills/product-research/references/project-profile.md
  - plugins/product/skills/product-research/assets/profile.md
  - plugins/product/skills/product-research/references/evidence-contract.md
priority: medium
ordinal: 1000
dedup_key: 'followup:pr-unknowns-dropped'
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**What**: in the first real run (valycorp/valysec#1, Tailscale, 2026-09-29), four unknowns only appear in the PR body: whether Tailscale US Inc. is DPF-certified, whether it is a subsidiary of Tailscale Inc., governing law in Enterprise contracts, and PAM's license and plan. business-models.md records the PAM one with its Settle by. The three vendor unknowns are in no file, because valysec's vendors.md is a one-row-per-vendor table with nowhere to put them.

**Why it matters**: evidence-contract.md says 'An unknown stays an unknown in the written record. It is not rounded to the product's favour and not silently dropped.' Once the PR merges, the only trace is a closed PR's description. The next run will see a finished vendor row and won't know those checks are still owed. The Parent field (vendor-record.md) is the same: the row lists two entities and never states the relationship is unverified.

**Cause**: project-profile.md's Record formats rule says a format 'may not drop the source, license or business-model fields'. Unknowns are not in that protected list. Step 5 also treats 'a new research gap' as an edit the user did not ask for, so it gets proposed and not written.

**Fix direction**: add Unknowns to the fields a format may not drop. When a row format has no room, the unknowns go to a named place the profile provides: a research-gaps list, or a notes block under the table. assets/profile.md's scaffold asks for that place. Step 5 writes the unknowns attached to an approved record as part of that record, so they are not treated as an unrequested extra edit.

**Also seen in the same run (minor, fold in if cheap)**: coverage markers are judgements, but the written coverage.md carries no confidence for them. Only the proposal did. The 'proprietary' licence for the coordination server and the Apple/Windows GUIs cites the vendor statement and the GitHub org search. The contract also asks for a package-registry search, and the record doesn't mention one.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 project-profile.md: Unknowns are a field a record format may not drop
- [ ] #2 The profile schema and assets/profile.md name where unknowns go when a row format has no room
- [ ] #3 SKILL.md Step 5 writes a record's unknowns with the record, not as an unrequested edit
- [ ] #4 The research-no-profile eval still passes; ops verify passes
<!-- AC:END -->
