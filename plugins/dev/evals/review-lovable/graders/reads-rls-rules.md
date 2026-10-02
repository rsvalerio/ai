---
type: tool_used
name: reads-rls-rules
tool: Read
input_match: "references/rules/(RLS|SUPA|QRY)\\.md"
min: 1
---

The snippet's defects are an open `using (true)` update policy (RLS-2), an unread supabase
`error` (SUPA-1 / QRY-2) and a user-agnostic query key (QRY-1). A scan that finds them
reads at least one of those tier-3 files before naming a rule.
