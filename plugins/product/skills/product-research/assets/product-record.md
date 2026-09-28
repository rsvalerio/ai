# Product Record

<!--
The fields a product record carries. The profile's record formats decide the layout
(table rows, a page, several files by role); they may not drop the source, license or
business-model fields. Vendor facts do not go here: see vendor-record.md.
-->

## Identity

- **Product** — name as the vendor uses it; link to its docs.
- **Vendor** — name only; everything about the company lives in the vendor record.
- **Scope placement** — section from the profile's scope map, with the marker the profile
  uses and one line of reasoning.

## Coverage

One entry per profile dimension:

| Dimension | Marker | Evidence | Confidence |
|-----------|--------|----------|------------|
| `<from profile>` | `<from profile>` | `[S<n>]` or *unknown — settle by …* | high / medium / low |

A one-line justification for every marker that is neither the full nor the absent one.

## License

| Component | Class | SPDX | Ref (tag @ commit) | Source |
|-----------|-------|------|--------------------|--------|

- **History** — changes with dates and the last ref under the old license, or "no change
  found in <refs>, checked <date>".

## Business Model

| Component | Availability | First paid plan | Source |
|-----------|--------------|-----------------|--------|

- **Pattern** — named pattern, or "none fits" with a description.
- **Self-hostable** — grade, naming the component that limits it.
- **Forks / rebuilds** — name, repository, license @ ref, governance, component replaced.
- **Pricing checked** — `<YYYY-MM-DD>`, pricing page URL.

## Unknowns

Each with *Settle by: <check>*.

## Sources

`[S<n>]` entries in the evidence contract's source-record format, or URL + date inline
where the profile's format has no room for ids.
