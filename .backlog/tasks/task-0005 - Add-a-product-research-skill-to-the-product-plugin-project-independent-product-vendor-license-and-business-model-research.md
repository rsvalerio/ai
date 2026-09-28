---
id: TASK-0005
title: 'Add a product-research skill to the product plugin: project-independent product, vendor, license and business-model research'
status: In Progress
assignee: []
created_date: '2026-09-27 14:02'
updated_date: '2026-09-28 11:05'
labels:
  - product
  - new-skill
dependencies:
  - TASK-0004
modified_files:
  - plugins/product/skills/product-research/SKILL.md
  - plugins/product/.claude-plugin/plugin.json
  - README.md
  - AGENTS.md
priority: medium
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**What**: Add a `product-research` skill to the new `product` plugin. It takes a product name, URL or GitHub repo, researches it, and records it in the consuming project's reference folder. The output covers feature coverage, company ownership and jurisdiction, and **license and business model**.

**Origin**: this generalises valysec's project-local `reference-ingest` skill (`valysec/.claude/skills/reference-ingest/SKILL.md`). That skill is tied to valysec's conventions (six primitives, principle 8, Canon, `06-reference/` paths) and has no business-model dimension. Tailscale is the motivating case: BSD-licensed open client, closed coordination server, and Headscale as a community rebuild of the server. That open-endpoint/paid-control-plane split can't be recorded anywhere today.

**Design**

- **Project-independent.** Every project-specific convention lives in a profile file in the consuming repo, `.product-research.md` or a section of its CLAUDE.md/AGENTS.md. The profile covers:
  - output directory and file roles (landscape, coverage, vendors, business models)
  - coverage dimensions and markers
  - scope map, jurisdiction policy, vocabulary rules
  - tier definitions

  With no profile, the skill **stops** and offers to scaffold one from `references/project-profile.md`. It never guesses. Nothing from any consuming project's thesis may appear in this public repo.
- **Modes**: ingest (new product) and update (existing row). Also a stop gate: with no explicit target, or when the input resolves to a vendor with several products, it asks. Arguments given at invocation count as answers already given.
- **Resolve before researching**: vendor vs product, what the repo already knows, and the company structure (parent, legal entity, trade name vs legal name, license changes). A shared domain or similar name isn't proof of ownership. Check HQ *and* governing law, and never write "EU-based" without naming the country.
- **Evidence contract** (`references/evidence-contract.md`), mapping each claim type to the source it needs:
  - Features: docs or code.
  - License: the LICENSE file at a pinned commit or tag, per component; never the GitHub badge.
  - Pricing / paid tier: the official pricing page, with the date checked.
  - Ownership / HQ: a company registry or legal imprint.
  - Funding: a primary announcement.
  - Marketing counts only as a self-reported claim, graded L1–L4 (vendor claim → one third party → several independent sources → registry or directly observable).
- **License taxonomy** (`references/license-taxonomy.md`): permissive / weak copyleft / strong copyleft / source-available non-OSI (BSL, SSPL, Elastic, Commons Clause, fair-source) / proprietary / unknown. An unknown license is never treated as permissive. License history is recorded (e.g. HashiCorp moving to BSL, then OpenTofu forking), with dates.
- **Business-model taxonomy** (`references/business-model.md`): what's open vs paid, per component (client, server, control plane, enterprise features). Patterns to cover:
  - open-core
  - open client with closed control plane (Tailscale)
  - fully self-hostable plus paid cloud (NetBird)
  - SaaS-only
  - dual license
  - source-available relicense

  Also: whether the whole thing can be self-hosted, and community forks or rebuilds (Headscale, OpenTofu, OpenBao).
- **Jurisdiction** (`references/jurisdiction.md`): HQ vs governing law; EU/EEA vs adequacy vs extraterritorial reach (e.g. the US CLOUD Act); company facts belong in the vendor record, never on a product row.
- **Record hygiene**:
  - Every record carries its sources: URL, commit or version, and date checked.
  - Facts, judgments and unknowns stay separate. Only judgments carry a confidence level.
  - Each unknown names the check that would settle it.
  - Don't soften an absent marker. Don't inflate the depth tier to justify the run.
  - Use the product's own vocabulary.
- **Propose before writing**: findings and proposed edits go to chat first; write only what was approved. Edits the user didn't ask for become proposals.
- **Safety**: fetched web content is data, never instructions. The privacy wall means the project's private context (thesis, strategy) never goes into web-search queries.
- **Layout**: `SKILL.md` as a short router under ~500 lines; `references/` for the contracts and taxonomies; `templates/` for the profile page and row formats. Each rubric is defined in exactly one file, to avoid rubric drift.

**Inspiration** (reviewed 2026-09-27):
- daymade competitors-analysis (Source Register, Analysis Boundary, stop gate): https://github.com/daymade/claude-code-skills/tree/main/competitors-analysis
- daymade deep-research (source tags, AS_OF, counter-review, "unable to verify" template): https://github.com/daymade/claude-code-skills/blob/main/deep-research/SKILL.md
- daymade benchmark-due-diligence (L1–L4 evidence, company-structure-first, privacy wall): https://github.com/daymade/claude-code-skills/tree/main/daymade-financial/benchmark-due-diligence
- oss-review (license buckets, relicense check, stop on missing profile): https://github.com/ThomasMoreAI/legal-skills-open/blob/main/general/ip/skills/oss-review/SKILL.md
- Anthropic competitive-brief and competitive-intelligence (connector placeholders, "note the date", web content as data): https://github.com/anthropics/knowledge-work-plugins
- Avoid:
  - numeric domain-authority scores
  - market-share or funding figures without a source
  - hardcoded output paths or competitor lists
  - rubrics defined in two files (as in alirezarezvani competitive-teardown)

**Out of scope for this repo (valysec follow-up)**: write valysec's `.product-research.md` profile (six primitives, principle 8, Canon rule, `06-reference/` paths, a new business-models file and README job 4), then delete `valysec/.claude/skills/reference-ingest/`. First real run: Tailscale.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 plugins/product/skills/product-research/ has SKILL.md (name and description, license Apache-2.0), references/ (evidence-contract, license-taxonomy, business-model, jurisdiction, project-profile) and templates/, and passes strict skill-validator
- [x] #2 Nothing project-specific in the skill: all conventions come from the consuming repo's profile; with no profile the skill stops and offers to scaffold one
- [x] #3 Each run records license (per component, pinned commit or tag) and business model (open vs paid per component, self-hostable, license history, forks) alongside coverage and vendor jurisdiction
- [x] #4 Every recorded claim carries its source URL, version or commit, and date checked; unknowns name the check that would settle them
- [x] #5 The skill proposes in chat and writes only what was approved
- [x] #6 An eval under plugins/product/evals/ asserts that a 'research product X' prompt loads product-research and, with no profile present, the skill asks for one instead of writing
- [x] #7 The README overview lists the product plugin and the skill

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented on feat/product-research.

- Templates live in assets/ (profile, proposal, product-record, vendor-record), not templates/: strict skill-validator warns 'unknown directory: templates/ ... should this be assets/?'. AC #1 is met in substance; the directory name differs.
- AC #3/#4 are enforced by the skill's contract (evidence-contract, license-taxonomy, business-model, assets/*-record.md). No real run yet; the first one is the valysec follow-up (Tailscale).
- AC #6: plugins/product/evals/research-no-profile. Gated tools (Write, Edit, WebSearch, WebFetch) are withheld from both arms unless --allow-tools grants them, so the no-write / no-research graders passed vacuously at first (baseline 0.80). make eval now grants them: with 1.00 / without 0.20, delta +0.80 over 3+3 runs on 2026-09-28.
- plugin.json needed no change; Makefile (eval grant) was touched in addition.
<!-- SECTION:NOTES:END -->
