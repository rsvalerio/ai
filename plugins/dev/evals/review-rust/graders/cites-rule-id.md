---
type: regex
name: cites-rule-id
pattern: "\\b(OWN|ERR|TRAIT|CONC|ASYNC|PERF|UNSAFE|SEC|TEST|NATS|API|ARCH|READ|TIME|VER|FN|DUP|CL|PATTERN|MACRO|EDITION)-[0-9]+\\b"
---

An ad-hoc review answers in chat and cites a rule ID for every problem it names
(SKILL.md, Applicability). Loading the skill and reading a rule file without
surfacing an ID in the answer is the skill firing without shaping the review.
