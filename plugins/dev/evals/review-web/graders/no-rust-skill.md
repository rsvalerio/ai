---
type: tool_used
name: no-rust-skill
tool: Skill
input_match: code-review-rust
min: 0
max: 0
arm: both
---

The web case is the false-positive guard for `code-review-rust`. Asserting that
`code-review-web` loaded does not assert that the Rust skill stayed out — a run that
loads both would score a clean 1.00. This is the half that fails when a description edit
makes the Rust skill over-trigger on React code.
