---
id: TASK-0014
title: 'review-rust and review-web evals never trigger their skill on a pasted-snippet review'
status: To Do
assignee: []
created_date: '2026-09-29 18:13'
labels:
  - evals
  - skill-trigger
dependencies: []
modified_files:
  - plugins/dev/skills/code-review-rust/SKILL.md
  - plugins/dev/skills/code-review-web/SKILL.md
  - plugins/dev/evals/review-rust/prompt.md
  - plugins/dev/evals/review-web/prompt.md
priority: medium
ordinal: 1000
dedup_key: 'followup:review-evals-no-trigger'
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**What**: in every recorded dev eval run (2026-09-27 on Claude Code 2.1.283; 2026-09-29 on 2.1.284) review-rust scores with 0.00 / without 0.00 and review-web with 0.50 / without 0.50 (its only pass is the no-rust-skill grader, which the baseline also passes). guardrail-rust passes at +1.00 in both runs.

**Cause (verified 2026-09-29 with --keep-temp)**: the with-plugin session lists dev:code-review-rust in its skills. The model answers the pasted snippet in one turn, and correctly at that (SQL injection, unwrap, &String), with no Skill call. The descriptions frame the skills as an 'implementation guardrail' or 'a formal review that files one backlog task per finding', and a chat 'what is wrong with this function' fits neither. guardrail-rust passes because its prompt asks for the repo's rules.

**Not caused by** PR #26: the scores are identical to the run before it.

**Decision needed**: (a) widen the two descriptions so an ad-hoc review of pasted Rust/React code loads the skill (the description is what auto-load keys on), then re-measure; or (b) accept that snippet review is best-effort, as AGENTS.md already says, and re-point the two cases at a prompt that names a file in a sandbox repo. Either way a case that scores the same in both arms is carrying no signal and should not stay as is.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Decision (a) or (b) recorded in the notes
- [ ] #2 review-rust and review-web show a positive with/without delta, or are replaced by cases that do
- [ ] #3 make eval results recorded in the notes
<!-- AC:END -->
