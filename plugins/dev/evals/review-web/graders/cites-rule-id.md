---
type: regex
name: cites-rule-id
pattern: "\\b(REACT|TS|ASYNC|PERF|A11Y|SEC|TEST|RT|API|ARCH|READ|FN|DUP|CL)-[0-9]+\\b"
---

An ad-hoc review answers in chat and cites a rule ID for every problem it names
(SKILL.md, Applicability). Loading the skill and reading a rule file without
surfacing an ID in the answer is the skill firing without shaping the review.
