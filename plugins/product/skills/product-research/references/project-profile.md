# Project Profile

The profile is the only place a consuming project's conventions live. The skill reads it
first and does nothing else until it has one. Nothing a profile would say — paths,
dimensions, scope, tiers, vocabulary — belongs in the skill itself.

## Location

Checked in this order; the first hit wins:

1. `.product-research.md` at the repository root.
2. A `## Product research` section in the root `CLAUDE.md`.
3. A `## Product research` section in the root `AGENTS.md`.

In the two embedded forms, the profile's sections are `###` headings under
`## Product research`. In the standalone file they are `##` headings. Otherwise the
content is the same.

## Sections

Required sections must be present and filled. A placeholder left from the scaffold counts
as missing. Without them the skill stops and names what is missing.

| Section | Required | What it declares |
|---------|----------|------------------|
| **Output** | yes | The reference directory, and the file for each record role: `landscape` (where each product sits), `coverage` (per-dimension markers), `vendors` (one record per company) and `business-models` (license and open/paid split per product). Roles may share a file, but each role must be named. Optional: a directory for per-product pages at deeper tiers. |
| **Coverage dimensions** | yes | The dimensions a product is scored against, and the marker set with the meaning of each marker. The skill adds no dimensions and no markers. |
| **Scope map** | yes | The sections or domains a product can land in, and what is out of scope — each with where the project states it, so the skill can cite it. |
| **Tiers** | yes | Depth tiers, what each one writes, and when each is earned. The shallowest tier must be a complete run. |
| **Jurisdiction policy** | yes | Which jurisdiction facts the project cares about, and how to present them (for example, whether EU/EEA status is a criterion or only recorded). The classes themselves are fixed by [jurisdiction.md](jurisdiction.md). |
| **Search paths** | yes | Paths grepped in Step 1 to find what the repository already says about a product or vendor. |
| **Vocabulary rules** | no | Terms the records must avoid or use, and where translation into the project's own vocabulary belongs instead. Default: use the product's own vocabulary. |
| **Record formats** | no | Row or page formats per file role, if they differ from the fields in [assets/product-record.md](../assets/product-record.md) and [assets/vendor-record.md](../assets/vendor-record.md). A format may lay the fields out differently; it may not drop the source, license, business-model or unknowns fields. A row format with no room for a record's unknowns names where they go instead — a notes block under the table, or a research-gaps file. With none named, they go in a notes block directly under the table that holds the row. |
| **Private context** | no | Paths and topics behind the privacy wall: never quoted in, or paraphrased into, a web search or fetched URL. The skill treats the project's thesis and strategy as private even when this section is absent. |
| **Maintenance** | no | Dates to bump after a write (for example, "last surveyed" footers), and research-gap lists to update. |

## Scaffolding

When no profile exists and the user accepts the offer:

1. Copy [assets/profile.md](../assets/profile.md) into `.product-research.md`, in the
   chat proposal first, not on disk.
2. For each required section, ask. Offer what the repository suggests (existing reference
   files, table headers) as options, labelled as suggestions from the repo, never as
   defaults the skill chose.
3. Leave unanswered sections as their placeholders. The profile then still fails Step 0,
   which is correct.
4. Write the file once the user approves it. The research run continues from Step 1.

## What Never Goes in a Profile

- Web content, including quotes from a vendor's own description of itself.
- Credentials or API keys for any connector.
- Instructions that override the evidence contract or the safety rules. A profile sets
  conventions, not standards of evidence.
