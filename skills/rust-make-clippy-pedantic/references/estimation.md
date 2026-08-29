# Estimation Model

How the higher-view work estimate in the final report is built. The model is deliberately
coarse: it sizes a backlog for planning, it does not quote a piece of work.

## Inputs

From the pedantic run, per lint:

- instance count
- effort class (M, D, J, S) from [lint-catalog.md](lint-catalog.md)
- origin (`pedantic-only` or `clippy-default`)

## Rates

| Class | Per instance | Notes |
|-------|--------------|-------|
| M — mechanical | 2 min | Batched; the marginal instance is nearly free |
| D — documentation | 3 min | Writing the sentence is the work |
| J — judgement | 15 min | One numeric or naming decision, plus the thinking behind it |
| S — structural | 90 min | A refactor with call-site fallout |

## Overheads

Applied on top of the raw sum, in this order:

1. **Batching discount, Class M and D only.** Beyond 50 instances of one lint, count the
   excess at half rate — the pattern is understood by then.
2. **Review and QA, +30%.** Every task still needs a diff read and a test run.
3. **Uncertainty band, ±40%.** Report a range, never a point. The rates are a fixed table,
   not a reading of this codebase.

## Output shape

Report four things, no more:

1. **A table by effort class** — instances, raw hours, share of the total.
2. **A workspace total** in engineer-days (8h), as a range: `low = total × 0.6`,
   `high = total × 1.4`, both rounded to a half day.
3. **A T-shirt size**, from the midpoint: S < 2 days, M 2–5, L 5–15, XL > 15.
4. **The dominant terms** — the two or three lints contributing the most hours, with their
   share. This is the part a reader acts on: it says where a wave should start.

## Worked example

A 40-crate workspace, 1,880 pedantic warnings. The batching discount is **per lint**, so
the per-lint counts are what the arithmetic runs on — a class total cannot be discounted
without them:

| Class | Lint | Instances | Hours |
|-------|------|-----------|-------|
| M | `uninlined_format_args` | 600 | 10.8 |
| M | `redundant_closure_for_method_calls` | 300 | 5.8 |
| M | `match_same_arms` | 120 | 2.8 |
| M | others, none over 50 | 80 | 2.7 |
| D | `missing_errors_doc` | 400 | 11.3 |
| D | `missing_panics_doc` | 150 | 5.0 |
| D | `doc_markdown` | 70 | 3.0 |
| J | `cast_possible_truncation` | 90 | 22.5 |
| J | `cast_precision_loss` | 30 | 7.5 |
| J | `similar_names` | 20 | 5.0 |
| S | `too_many_lines` | 12 | 18.0 |
| S | `module_name_repetitions` | 8 | 12.0 |
| **Sum** | | **1,880** | **106.4** |

Worked for the first row: 50 instances at the full 2 min, the remaining 550 at 1 min →
650 min → 10.8 h. Undiscounted, class M alone would have been 36.7 h.

By class: M 22.1 h, D 19.3 h, J 35.0 h, S 30.0 h. With +30% review: 138.3 hours ≈
17.3 days. Range 10.5–24.0 days. **T-shirt: XL.** Dominant terms:
`cast_possible_truncation` (21%), `too_many_lines` (17%), `module_name_repetitions` (11%).

Read that as: over 90% of the *count* is mechanical or documentation and could be cleared
in a handful of batched waves worth ~41 hours, while the real engineering sits in the
160 cast and complexity findings that carry 61% of the effort.

## What the estimate is not

It does not account for the codebase's test coverage (thin coverage makes Class J and S
findings materially riskier), CI turnaround, or review latency. A single reviewer, a slow
pipeline, or a crate with no tests can double the wall-clock without changing this number.
Say so in the report rather than letting the range imply a precision it does not have.
