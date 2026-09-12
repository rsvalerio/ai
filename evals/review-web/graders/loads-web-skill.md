---
type: tool_used
name: loads-web-skill
tool: Skill
input_match: code-review-web
---

A React/TypeScript review request must load `code-review-web`, not the Rust
skill. This case is also the false-positive guard for `code-review-rust`.
