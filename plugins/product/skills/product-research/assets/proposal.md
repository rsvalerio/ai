# Proposal: <Product> (<ingest | update>)

<!--
Shape of the Step 4 chat proposal. Nothing is written until the user approves; the
proposal ends by asking which edits to apply. Section names are fixed; content follows the
profile and the rubric files.
-->

## Analysis Boundary

- **Target** — product, the vendor behind it, and what was deliberately left out (sibling
  products, out-of-scope parts).
- **As of** — `<YYYY-MM-DD>`; every fact below was checked on or before this date.
- **Refs read** — repository @ tag (commit) for each component.
- **Not researched** — anything skipped, and why (no clone permission, paywalled, etc.).

## Tier

`<tier from the profile>` — <the one sentence that justifies it>.

## Product Record

Fields from [product-record.md](product-record.md), with `[S<n>]` source ids.

## License and Business Model

One row per component: component, license class and SPDX id @ ref, availability, first paid
plan. Then the pattern, self-hostability grade, license history and forks or rebuilds.

## Vendor Record

Fields from [vendor-record.md](vendor-record.md). Say plainly which jurisdiction class the
entity and its parent fall in, and any extraterritorial reach.

## Facts / Judgements / Unknowns

- **Facts** — each with its source ids.
- **Judgements** — each with a confidence (`high` / `medium` / `low`) and the facts it
  rests on. Coverage markers go here.
- **Unknowns** — each with *Settle by: <check>*.

## Counter-Review

What was tried to falsify the favourable judgements, and what changed as a result.
Relicense, acquisition and fork searches: what was searched, and what was found.

## Does This Change a Conclusion?

Whether the record changes anything the reference folder already concludes. Usually no.
An exception is flagged, not smoothed over.

## Proposed Edits

Per file (by profile role): the exact rows or sections to add or change, including where
each record's unknowns are written. Then, separately,
**edits not asked for**, such as neighbouring records and research gaps, each as a
proposal only.

## Source Register

```text
[S1] <title> — <URL> — <ref or n/a> — checked <YYYY-MM-DD> — L<1-4>
```
