---
id: TASK-0016
title: 'Add a code-review-rust SEC rule for verifying downloaded updates and plugins (OWASP A08:2025, CWE-494)'
status: Done
assignee: []
created_date: '2026-10-03 09:10'
updated_date: '2026-10-03 09:13'
labels:
  - rust
  - security
  - rules
dependencies: []
modified_files:
  - plugins/dev/skills/code-review-rust/references/rules/SEC.md
  - plugins/dev/skills/code-review-rust/references/rules/index.md
  - plugins/dev/skills/code-review-rust/references/scan-checklist.md
  - plugins/dev/skills/code-review-rust/references/owasp-2025.md
priority: medium
ordinal: 1000
dedup_key: 'followup:sec-rule-update-integrity'
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**What**: A08:2025 Software or Data Integrity Failures covers downloading code without an integrity check (CWE-494) and missing signature verification (CWE-345, CWE-353). code-review-rust has no SEC rule for it; A08 is reached only through SEC-11 (deserialized input) and SEC-37 (fuzzing). references/owasp-2025.md records the gap.

**How**: write a SEC rule for code or data fetched at runtime and then executed, loaded or trusted — self-update binaries, plugins and dynamic libraries, WASM modules, downloaded config or models, build.rs downloads: verify a signature or pinned digest before use, against a key or hash shipped with the binary rather than fetched alongside the artifact, and fail closed on mismatch. Decide whether build.rs downloads belong here or under the dependency rules (SEC-27, SEC-28). Add the rule to rules/SEC.md and rules/index.md, add a signal row to scan-checklist.md, and replace the gap note in owasp-2025.md with the new rule id under A08.

**Origin**: found during TASK-0013 (OWASP 2021 to 2025 migration).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 SEC rule for update and plugin integrity in rules/SEC.md with a matching line in rules/index.md
- [x] #2 scan-checklist.md has a signal that reaches the rule
- [x] #3 owasp-2025.md lists the rule under A08 and the gap note is removed
- [x] #4 make validate-rules and ops verify pass

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added SEC-44 (verify run-time fetched code and trusted data) to the Dependencies section of rules/SEC.md with its index line, a scan-checklist signal row, and the rule id under A08 in owasp-2025.md; the coverage-gap note is removed. build.rs downloads are covered by SEC-44 with a cross-reference to SEC-27. SEC.md size label updated to 34 KB in index.md and SKILL.md. ops verify passes.
<!-- SECTION:NOTES:END -->
