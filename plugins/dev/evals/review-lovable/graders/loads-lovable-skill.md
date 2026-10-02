---
type: tool_used
name: loads-lovable-skill
tool: Skill
input_match: code-review-lovable
---

A review request that carries Supabase migrations and supabase-js calls must load
`code-review-lovable`. `code-review-web` may load alongside it, because the skill is an
overlay, so this case does not assert that the web skill stayed out.
