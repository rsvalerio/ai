---
id: TASK-0023
title: 'code-review-run-waves / code-review-triage: sync main with origin before starting'
status: To Do
assignee: []
created_date: '2026-10-16 20:11'
labels:
  - plugins
  - waves
  - dogfood
dependencies: []
modified_files:
  - plugins/dev/skills/code-review-run-waves/SKILL.md
  - plugins/dev/skills/code-review-triage/SKILL.md
priority: medium
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**What**: Neither skill fetches before it starts. code-review-run-waves Step 0 runs `git checkout -b code-review/run-$(date +%Y%m%d) main` from whatever local `main` happens to be, and the Preconditions only check that `main` is clean, not that it is current. code-review-triage plans waves against the same possibly stale tree.

**Impact (event0, 2026-10-14)**: PR #25 had merged into origin/main, but local `main` was behind. The run branch was cut from the stale base. It missed 52 commits, and many findings were fixed on both sides. Delivering PR #26 then needed a large merge (62 conflicted files, about 220 hunks), plus adapting the run's code to API and lint changes it never saw.

**How**: add a precondition to both skills: `git fetch origin`, then `git pull --ff-only` on `main` (or fail if `main` has diverged from origin/main). In run-waves Step 0, cut the integration branch from the freshly synced `main`. When run-waves resumes an existing `code-review/run-*` branch, check `git rev-list --count HEAD..origin/main`. If it is non-zero, report it and offer to merge or rebase before any wave lands, so wave runners integrate against current main rather than discovering the divergence at PR time.

**Origin: event0 run-20261014 (PR #26), 2026-10-16.**
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 code-review-run-waves Preconditions fetch origin and require local main to equal origin/main (fast-forwarding it when behind) before Step 0 creates the run branch
- [ ] #2 code-review-run-waves, when resuming a run branch, reports how far it is behind origin/main and does not fan out until that is resolved
- [ ] #3 code-review-triage fetches and fast-forwards main before grouping findings
- [ ] #4 ops verify passes
<!-- AC:END -->
