# rust-meta Evaluation — 2026-08-25 (Chrono / date & time)

**Source**: pasted excerpt, "#12. Chrono — Date and Time Handling" — an entry from a numbered crate-tour series. Motivating example of hand-rolled date rollover, followed by a two-line Chrono replacement.

## Executive Summary

| | Count |
|---|---|
| Pieces extracted | 5 |
| Approved (integrated) | 3 — P2, P4, P5 |
| Rejected | 2 — P1, P3 |
| Needs clarification | 0 |
| Derived corrections integrated | 3 — TIME-4--6 |
| Rules added in total | 6 |

Rust version compatibility: no rule here depends on an unstable feature or a language feature above the 1.87 ingestion baseline. Crate MSRVs are not all under it, though: `chrono` 0.4.45 needs 1.62 and `jiff` 0.2.35 needs 1.70, but **`time` 0.3.55 declares `rust-version = 1.88.0`** — one release above the baseline. That does not invalidate TIME-1, which recommends `time` only for the UTC-only, low-dependency case, but the MSRV is now stated in the rule so the recommendation cannot silently push a project's toolchain forward. A project pinned to 1.87 takes `time` 0.3.45 (MSRV 1.83, released 2026-01-13), the last release under the baseline. Separately: the 1.87 baseline in [evaluation-criteria.md](../skills/rust-meta/references/evaluation-criteria.md) was last reviewed 2026-03-13 and is due a bump — that is a policy call for the maintainer, not something this ingestion changed.

**Overall assessment.** A weak source with a real gap behind it. The article is beginner-level ("don't hand-roll calendars, use a crate") and its two substantive claims were already thin; more importantly, **its own worked example is an anti-pattern** — `Local::now() + chrono::Duration::days(7)` picks the environment-dependent clock and then does fixed-offset arithmetic where the reader plainly means "a week later on the calendar". The two diverge by an hour across a DST transition, which is precisely the class of bug the article promises the crate removes.

The gap it exposed is genuine: `code-review-rust` had **no date/time rules at all** — a grep for `chrono`, `SystemTime`, `Instant`, and `timezone` across every rules file returned only incidental hits (`tokio::time::sleep` under CONC-5, timestamp nondeterminism under TEST-30). Every application in scope for this skill handles expiries, schedules, and log timestamps.

So the integration is mostly *derived* rather than *transcribed*: the article supplied the topic and one approvable rule (TIME-1); of the remaining five, TIME-2 and TIME-3 come from correcting its worked example and TIME-4--6 from closing the domain it opened. That is the honest accounting — this was a prompt, not a teacher.

## Verification performed

| Crate | Latest stable | Last release | MSRV | Verified claim |
|---|---|---|---|---|
| `chrono` | 0.4.45 | 2026-06-04 | 1.62.0 | maintained; `TimeDelta`/`Days`/`Months`, `checked_add_days`, `to_rfc3339`, `chrono::serde::ts_*` |
| `jiff` | 0.2.35 | 2026-07-25 | 1.70 | maintained; **still pre-1.0** — the rule was corrected mid-integration from a drafted "1.x" claim |
| `time` | 0.3.55 | 2026-08-01 | **1.88.0** | maintained; `now_local()` returns `Err` when the offset is indeterminate (multi-threaded). **Above the 1.87 baseline** — see the summary above; 0.3.45 (MSRV 1.83) is the last release under it |

Other facts checked before they were asserted in a rule: `chrono::Duration` → `TimeDelta` rename landed in 0.4.35 with the old name kept as an alias (hence the `std::time::Duration` name collision); RUSTSEC-2020-0159 (`localtime_r` unsoundness) fixed in 0.4.20; `TimeDelta::days` and `DateTime + TimeDelta` panic on out-of-range, `try_days` / `checked_add_signed` / `checked_add_days` return `Option`; `Months` addition saturates to the last valid day of the target month; `LocalResult` is returned by `from_local_datetime` because DST makes some local times ambiguous or nonexistent; `DateTime`'s `Display` impl is space-separated, not RFC 3339.

## Detailed Results

### P1 — "Working with dates and times is more complex than it seems (time zones, formatting, parsing, durations)"

- **Status**: Rejected
- **Reasoning**: Makes Sense — fails. Generic motivation with no actionable content; nothing a reviewer can check a diff against.
- **Target**: none

### P2 — "Don't hand-roll calendar arithmetic; month lengths and leap years are error-prone"

- **Status**: Approved
- **Reasoning**: Worth Adding — fills a gap. No existing rule covers date arithmetic. Actionable as a scan signal (`is_leap_year` helpers, manual day rollover, `secs / 86_400`).
- **Rust Version**: version-independent
- **Already Expressed**: nothing
- **Target**: rules-core.md → new `## Date & Time` section, **TIME-1**
- **Modifications**: the source's own leap-year rule is **wrong** — `year % 4 == 0` marks 1900 as a leap year. Integrated with the correct Gregorian rule stated inline, since a rule that reproduces the article's simplification would teach the bug it is meant to catch. Extended with crate arbitration (`chrono` / `jiff` / `time`) and a "don't mix two of them" caveat, which the single-crate source does not raise.

### P3 — "Chrono supports time zones, parsing, formatting, duration arithmetic, local and UTC"

- **Status**: Rejected as written
- **Reasoning**: Worth Adding — fails. A feature list, not guidance; it names no decision a reviewer makes. The *choice* between `chrono`, `jiff`, and `time` is the reviewable part, and that was folded into TIME-1 instead.
- **Target**: none (absorbed into TIME-1)

### P4 — Example: `let now: DateTime<Local> = Local::now();`

- **Status**: Approved as a **counter-example**
- **Reasoning**: Makes Sense — the source presents this as the recommended pattern, and for anything but immediate display it is a defect. `Local` depends on `TZ` and the host tzdb, so persisted or logged local timestamps mean different instants on different hosts and are not comparable across them.
- **Target**: rules-core.md → **TIME-2**
- **Integration Point**: linked to UNSAFE-8 (runtime `set_var("TZ", …)` racing threads that read local time) and to RUSTSEC-2020-0159 for pinned `chrono` < 0.4.20 in `Cargo.lock`.

### P5 — Example: `now + chrono::Duration::days(7)` as "one week later"

- **Status**: Approved as a **counter-example**
- **Reasoning**: Makes Sense — the source conflates a fixed 604 800-second offset with a calendar week. On a `DateTime<Local>` crossing a DST boundary the wall-clock time shifts by an hour; `Days::new(7)` via `checked_add_days` is the calendar-correct form. The source also uses the pre-0.4.35 type name and the panicking constructor.
- **Target**: rules-core.md → **TIME-3**
- **Modifications**: added the `TimeDelta` rename and its `std::time::Duration` name collision; the panic-vs-`Option` split (`try_days`, `checked_add_signed`, `checked_add_days`) and its SEC-33 remote-panic consequence when the operand is untrusted; `Months` end-of-month saturation.

### Derived — TIME-4, TIME-5, TIME-6 (not in the source)

Three rules follow from claims the source makes but does not qualify, and were added to make the new section coherent rather than a stub:

- **TIME-4** — the source advertises Chrono for "calculations like durations". For *elapsed* time it is the wrong tool: NTP adjustment can make a `Utc::now()` delta negative. Monotonic `Instant` for measurement, `DateTime<Utc>` for anything that outlives the process.
- **TIME-5** — the source prints with `{}` and never mentions boundaries. `NaiveDateTime` carries no offset; `Display` is not RFC 3339; a bare `i64` timestamp field is the seconds-vs-milliseconds bug. Also flags `.unwrap()` on `LocalResult`.
- **TIME-6** — clock reads buried in business logic are untestable at exactly the boundaries this domain gets wrong (month rollover, expiry ±1s, leap day, DST). Inject the instant; note that `tokio::time::pause()` (TEST-13) does **not** affect `Utc::now()`, which is the trap for anyone who assumes async time control covers wall-clock reads.

## Summary

### Approved and integrated (6)

| Piece | Target |
|---|---|
| No hand-rolled calendar arithmetic + crate choice | TIME-1 (`rules-core.md`) |
| UTC for storage/compare/log, `Local` at display only | TIME-2 |
| Elapsed-time vs calendar arithmetic; panic-free constructors | TIME-3 |
| Monotonic clock for measurement | TIME-4 (derived) |
| Unambiguous timestamps at boundaries | TIME-5 (derived) |
| Injectable clock for testability | TIME-6 (derived) |

### Rejected (2)

| Piece | Reason |
|---|---|
| P1 — "Dates are complex" preamble | Too generic — no reviewable content (Makes Sense) |
| P3 — Chrono feature list | Not actionable; the reviewable part (crate choice) absorbed into TIME-1 (Worth Adding) |

The article's manual-rollover code sample is not counted here: it was never a candidate for integration as reference material (its leap-year rule is wrong — see P2), and it survives only as the anti-pattern TIME-1 describes.

### Needs clarification (0)

None.

## Updated files

| File | Change |
|---|---|
| `skills/code-review-rust/references/rules-core.md` | New `## Date & Time (typical severity: Medium--High)` section with TIME-1--6, placed after Advanced Patterns |
| `skills/code-review-rust/references/rules.md` | `TIME` added to the Idioms & correctness prefix list and domain description |
| `skills/code-review-rust/references/anti-patterns.md` | New `## Date & Time` section — hand-rolled calendar math, naive/local timestamps crossing a boundary, wall clock as a stopwatch |
| `skills/code-review-rust/SKILL.md` | Four scan-checklist rows (TIME-1, TIME-2/5, TIME-4, TIME-6) and `TIME` added to the core-rules reference line |

## Follow-ups to watch

- `jiff` is pre-1.0 and moving; re-check TIME-1's characterisation of it at the next ingestion, and promote it above `chrono` for new code if it reaches 1.0 with the zoned-arithmetic API intact.
- The `time` crate raises its MSRV freely (1.83 → 1.88 across 0.3.45–0.3.55 in seven months). Re-check the figure in TIME-1 rather than trusting it; it is the one crate of the three that will drift.
- The 1.87 ingestion baseline is five months past its last review. Bumping it would settle the `time` question by absorbing it.
