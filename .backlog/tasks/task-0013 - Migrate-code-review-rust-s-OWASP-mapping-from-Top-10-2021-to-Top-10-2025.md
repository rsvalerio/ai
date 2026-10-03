---
id: TASK-0013
title: 'Migrate code-review-rust''s OWASP mapping from Top 10:2021 to Top 10:2025'
status: Done
assignee: []
created_date: '2026-09-29 17:21'
updated_date: '2026-10-02 23:27'
labels:
  - rust
  - security
  - rules
dependencies: []
modified_files:
  - plugins/dev/skills/code-review-rust/references/owasp-2021.md
  - plugins/dev/skills/code-review-rust/references/rules/SEC.md
priority: medium
ordinal: 1000
dedup_key: 'followup:owasp-2025'
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**What**: owasp.org/Top10 now redirects to the published 2025 list (A01–A10:2025; A03 is now Software Supply Chain Failures). code-review-rust's references/owasp-2021.md and every SEC rule mapping still cite 2021 categories. The note in owasp-2021.md was updated on 2026-09-29 (TASK-0009) to say the migration is pending.

**How**: read the final 2025 list and its 2021→2025 mapping page. Rename or replace owasp-2021.md, remap each SEC rule's category, and check whether new categories (supply chain, and whatever absorbed SSRF) leave SEC rules without a home or leave categories without rules. Update the code-review-web skill too if it cites the same edition.

**Origin**: found during the TASK-0009 baseline refresh; publication date not yet verified.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Mapping file cites Top 10:2025, with the source URL and date checked
- [x] #2 Every SEC rule's OWASP category reference uses 2025 ids; no 2021 ids remain
- [x] #3 code-review-web checked for the same edition
- [x] #4 make validate-rules and ops verify pass

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Renamed code-review-rust references/owasp-2021.md to owasp-2025.md and remapped every SEC rule by CWE against top10.owasp.org/2025 (final 2025-12-24, checked 2026-10-03); updated SKILL.md, rules.md and the nats-security.md OWASP column. Memory safety and DoS rules have no 2025 category and cite CWEs; SSRF (A01) and update-signature checks (A08) noted as coverage gaps. code-review-web already cited 2025 but with 2021 numbering and a wrong CORS claim; owasp-2025.md and SEC-15 corrected. validate-rules and ops verify pass.
<!-- SECTION:NOTES:END -->
