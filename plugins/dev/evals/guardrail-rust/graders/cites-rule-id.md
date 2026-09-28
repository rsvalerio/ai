---
type: regex
name: cites-rule-id
pattern: "\\b(OWN|ERR|TRAIT|CONC|ASYNC|PERF|UNSAFE|SEC|TEST|NATS|API|ARCH|READ|TIME|VER|FN|DUP|CL|PATTERN|MACRO|EDITION)-[0-9]+\\b"
---

The doc's verification step expects the answer to name at least one rule ID
(e.g. ERR-5, UNSAFE-1) — loading the skill without surfacing a rule is a
half-working guardrail.
