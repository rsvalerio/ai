---
type: tool_used
name: reads-rule-tiers
tool: Read
input_match: "references/rules/[A-Z][A-Z0-9]*\\.md"
min: 1
---

Tier 3 is the scan's authoritative read: full rule text comes from
`references/rules/<CATEGORY>.md` before any finding is filed.

`input_match` is an unanchored `RegExp` against the serialized tool input, so a bare
`references/rules` would also match `references/rules/index.md` — the tier-2 file a scan
is now told to skip — and the grader would pass without any tier-3 read at all. Category
files are upper-case and `index.md` is not, so `[A-Z][A-Z0-9]*` separates them without
needing lookahead.
