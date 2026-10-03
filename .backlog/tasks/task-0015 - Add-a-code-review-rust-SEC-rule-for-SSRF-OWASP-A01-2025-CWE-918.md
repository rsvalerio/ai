---
id: TASK-0015
title: 'Add a code-review-rust SEC rule for SSRF (OWASP A01:2025, CWE-918)'
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
dedup_key: 'followup:sec-rule-ssrf'
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**What**: OWASP Top 10:2025 folds SSRF (CWE-918) into A01 Broken Access Control, and code-review-rust has no dedicated SEC rule for it. references/owasp-2025.md records the gap and tells reviewers to file SSRF under SEC-11 (generic input validation) with the CWE named.

**How**: write a SEC rule for outbound requests built from untrusted input (reqwest, hyper, ureq and similar): allowlist scheme and host, resolve then check the address against private, loopback, link-local and cloud-metadata ranges, pin the resolved address for the connection so a DNS rebind cannot swap it, and re-validate on every redirect or disable redirects. Add the rule to rules/SEC.md and rules/index.md, add a signal row to scan-checklist.md, and replace the gap note in owasp-2025.md with the new rule id under A01.

**Origin**: found during TASK-0013 (OWASP 2021 to 2025 migration).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 SEC rule for SSRF in rules/SEC.md with a matching line in rules/index.md
- [x] #2 scan-checklist.md has a signal that reaches the rule
- [x] #3 owasp-2025.md lists the rule under A01 and the SSRF gap note is removed
- [x] #4 make validate-rules and ops verify pass

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added SEC-43 (SSRF) to the Input Validation section of rules/SEC.md with its index line, a scan-checklist signal row for HTTP client requests to an input-derived URL or host, and the rule id under A01 in owasp-2025.md; the SSRF gap note is removed. ops verify passes.
<!-- SECTION:NOTES:END -->
