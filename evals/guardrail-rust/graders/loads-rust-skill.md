---
type: tool_used
name: loads-rust-skill
tool: Skill
input_match: code-review-rust
---

This is the verification prompt from `docs/implementation-guardrail.md` — the
guardrail path the docs commit to, distinct from a formal review request.
A description edit that narrows `code-review-rust` to review-only shows up here
first.

Note the scope: the doc is explicit that auto-load is best-effort and that a
consumer's `CLAUDE.md` / `AGENTS.md` directive is the real contract. This case
covers the hint, not the directive.
