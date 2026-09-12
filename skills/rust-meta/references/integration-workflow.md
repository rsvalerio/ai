# Integration Workflow

Steps for integrating approved items into code-review-rust. This file defines **how** to integrate; see [evaluation-criteria](evaluation-criteria.md) for **what** to evaluate before integration.

## Pre

- Read the target file in code-review-rust (start with `references/rules.md`, then open the relevant `references/rules/<PREFIX>.md` file)
- Identify section or location for the new content
- Match existing formatting and style
- Understand current knowledge to avoid duplication or conflict

## During

- Insert logically; follow existing structure
- Maintain tone and style; add cross-references if needed
- Preserve structure; enhance existing text if complementary rather than adding redundant blocks
- One change per approved piece; group only when clearly one topic

### Categorization

When integrating, route content to the correct detailed rule file in code-review-rust:

- **Anti-patterns** (what to avoid, common mistakes) → `references/rules/{OWN,ERR,CONC,ASYNC,UNSAFE}.md`, or `references/anti-patterns.md` if cross-cutting
- **Best practices** (idiomatic patterns, recommended approaches) → the matching category file under `references/rules/` (`OWN`, `ERR`, `TRAIT`, `PERF`, `FN`, `READ`, `ARCH`, `API`, …)
- **Security** (vulnerabilities, insecure patterns, crypto) → `references/rules/SEC.md`
- **Code quality** (complexity, readability, architecture, API design) → `references/rules/{FN,READ,ARCH,API,CL}.md`
- **Testing** (test patterns, coverage, flakiness) → `references/rules/TEST.md`
- **NATS-specific** → `references/rules/NATS.md`

Every rule added, removed, or renumbered in a `references/rules/<PREFIX>.md` file must also be
reflected as a one-line entry in `references/rules/index.md`, and any new observable signal
in `references/scan-checklist.md`. A rule that exists only in the category file is invisible
to a scan.

### Merging Strategy

- **Pre-merge**: identify the exact insertion point; check that no adjacent content already expresses the same idea; verify the new content uses the correct rule prefix convention
- **Merge**: insert at the correct location; if enhancing an existing rule, append to it rather than creating a new rule; update cross-references if the new content changes boundaries
- **Post-merge**: verify file structure is intact; check that rule numbering is still sequential; confirm cross-references still resolve

## Validation

- Code examples: verify they compile when possible (review non-trivial examples for syntax correctness)
- Performance claims: verify with benchmarks or credible sources; flag unverified quantitative claims
- Version claims: cross-check against [Rust release notes](https://releases.rs/)

## Post

- Only approved items are integrated; rejected items appear in evaluation only
- "Needs Clarification" items are flagged for user review; do not integrate until clarified
- Verify the file structure is intact and links/refs still valid
- Document which files were modified and a short summary of additions/enhancements

> **Note**: rust-meta integrates knowledge into code-review-rust and produces evaluation files — it does not write finding files or use the backlog task layout. The code-review-rust skill produces its own findings after knowledge is integrated.
