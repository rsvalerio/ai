# Evaluation Output Conventions

Conventions for the rust-meta skill.

> **Note**: rust-meta produces evaluation files (not finding files like code-review-rust). It does not use finding ID prefixes or the backlog task file layout.

## Evaluation file format

Write an evaluation file (e.g., `reports/rust-meta-evaluation-YYYY-MM-DD.md`) with:

- **Executive Summary**: Total extracted, approved/rejected/needs clarification counts, Rust version compatibility, overall assessment
- **Detailed Results** (per piece): Source, Extracted Content, Evaluation, Status, Reasoning, Rust Version, Already Expressed, Target(s), Integration Point, Modifications
- **Summary**: Approved (list with targets), Rejected (list with reasons), Needs Clarification (list with questions)
- **Updated files**: Modified skill files, additions/enhancements summary

## Relationship to code-review-rust

rust-meta integrates knowledge into code-review-rust. For skill mapping and rule numbering, see [agent-mapping.md](agent-mapping.md).
