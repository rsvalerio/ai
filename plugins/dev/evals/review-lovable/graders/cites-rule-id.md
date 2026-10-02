---
type: regex
name: cites-rule-id
pattern: "\\b(RLS|SUPA|AUTH|EDGE|QRY|FORM|UI|LOV)-[0-9]+\\b"
---

An ad-hoc review answers in chat and cites a rule ID for every problem it names
(SKILL.md, Applicability). The snippet's defects are lovable-layer ones (RLS-2,
SUPA-1 / QRY-2, QRY-1), so a stack-blind answer that cites only `code-review-web`
IDs, or none, is the overlay not shaping the review.
