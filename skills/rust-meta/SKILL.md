---
name: rust-meta
description: Processes external Rust content (URLs, articles, pastes), evaluates it against existing Rust skills and project agents, and integrates approved knowledge into the right files. Use to learn from external sources and keep Rust guidance current.
allowed-tools: Read Write Grep Glob Bash(find *) Bash(cat *) Bash(head *) Bash(tail *) Bash(wc *) Bash(ls *) Bash(tree *) Bash(backlog *)
license: Apache-2.0
---

# Rust Meta

Process content (paste, @ file, or URL), check whether knowledge/patterns already exist in Rust skills or project agents, and integrate new knowledge into the appropriate targets when it passes evaluation.

## Purpose

- **Input**: Raw text, URLs (via web search/fetch), or @ attachments
- **Extract**: Knowledge, patterns, tips, anti-patterns, performance/security advice, code examples, best practices, testing/architectural guidance
- **Clean**: Ignore navigation/ads/marketing; focus on technical substance
- **Evaluate**: Each piece against three criteria (see [evaluation criteria](references/evaluation-criteria.md))
- **Map**: To the right skill or agent (see [agent mapping](references/agent-mapping.md))
- **Integrate**: Only approved items; follow [integration workflow](references/integration-workflow.md)

## Process

1. **Survey** — Read existing Rust skills/agents to understand current scope and patterns
2. **Extract** — Identify discrete knowledge pieces from the source
3. **Evaluate** — Cross-reference per piece:
   - **Already expressed** → reject (cite the existing skill/rule)
   - **Similar but adds nuance** → flag as "Needs Clarification" + note target rule for potential enhancement
   - **Conflicts with existing guidance** → flag for user review (do not integrate)
   - **Complements existing** → approve + note integration point
   - **Fills gap** → approve
4. **Map** — Assign approved pieces to target skill/agent
5. **Validate** — Verify examples and claims, check Rust version compatibility
6. **Integrate** — Apply only approved items; document in report

## References

- [Evaluation criteria](references/evaluation-criteria.md) — Makes Sense, Still Valid, Worth Adding
- [Agent mapping](references/agent-mapping.md) — Which skill/agent handles which knowledge
- [Integration workflow](references/integration-workflow.md) — Pre/during/post integration steps
- [OpenAI agent metadata](assets/openai.yaml) — Optional agent configuration for compatible runtimes

## Output

See [report format](references/meta-report-format.md) for evaluation report format (not task files).

## Rules

- **Evaluation is the PRIMARY FUNCTION** — never skip, rush, or deprioritize; every piece of content must pass all three criteria before integration
- Be conservative: when in doubt, reject or flag
- Check Rust versions; do not assume current
- Maintain existing structure and style when integrating
