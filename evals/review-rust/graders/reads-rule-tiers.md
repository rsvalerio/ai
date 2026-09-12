---
type: tool_used
name: reads-rule-tiers
tool: Read
input_match: references/rules
min: 1
---

The three-tier rule load is the point of the skill: after the scan checklist
narrows to rule IDs, the full text must come from `references/rules/<CAT>.md`.
A run that files findings without opening a rule file is reviewing from memory.
