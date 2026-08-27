# Rust Meta Evaluation — "Rust Streams vs Iterators" (article paste)

**Date**: 2026-08-27
**Source**: User-pasted article — "The moment I discovered Rust Streams, iterators suddenly felt ancient."
**Toolchain used for validation**: rustc 1.98.0, futures 0.3.34, tokio 1.x (`full`), tokio-stream (`io-util`), async-stream

## Executive Summary

| Metric | Count |
|---|---|
| Pieces extracted | 9 |
| Approved | 2 (both as *corrections*, not as stated) |
| Rejected | 6 |
| Already expressed | 1 |
| Needs clarification | 0 |

**Overall assessment**: **Low source quality; high gap value.** The article's central thesis is factually
wrong, both of its code examples fail to compile, its marquee example does not do what it claims, and its
benchmark is not reproducible. Nothing in it was integrated as written.

Its one genuine contribution is negative space: `code-review-rust` had **no `Stream` guidance at all** —
zero occurrences of `Stream`/`StreamExt` across every rule file, despite 12 ASYNC rules and a NATS section.
That gap is real and is now filled with verified content. The article earned two new rules by being wrong
about them in an instructive way.

## Validation performed

Every claim below was checked against a live toolchain rather than assessed by eye.

| Claim | Method | Result |
|---|---|---|
| Streams are push-based | Read `futures_core::Stream` trait source | **False** — doc reads "Attempt to **pull** out the next value… registering the current task for wakeup" |
| `stream::iter(n).map(..).sum().await` | `cargo build` | **E0599** — `futures::StreamExt` has no `sum` |
| `BufReader::lines()` + `lines.next().await` | `cargo build` | **E0599** — `tokio::io::Lines` is not a `Stream` |
| "This one stays alive. It waits naturally." | Ran corrected version against a file appended to mid-read | **False** — exited at EOF in **253.6µs**, never saw the appended line |
| Iterator over 1M i32 ≈ 26 ms | Benchmarked map+sum over 1M i32 | **Implausible** — 0.50 ms release, 12.9 ms debug |
| `AsyncIterator` in std | `cargo build` against `std::async_iter::AsyncIterator` | **E0658** — still nightly-only at 1.98 |

## Detailed Results

### P1 — "Streams flip the pipeline; data pushes itself at you" · REJECTED

- **Criterion failed**: Makes Sense (technically incorrect)
- The article's organising metaphor ("Notice the arrow direction. Data comes at you instead of you going
  after it") is wrong. `Stream::poll_next` is a pull, structurally identical to `Iterator::next`; the only
  difference is that it may return `Poll::Pending` and register a waker. Nothing is pushed. The genuinely
  push-shaped abstractions are `Sink`, `tokio::sync::broadcast`, and callback registration.
- **Disposition**: not integrated as stated; the *correction* is integrated (see ASYNC-13) because this
  misconception is common enough to be worth a scan signal.

### P2 — "`Stream` is the async analogue of `Iterator`; use it for values arriving over time" · APPROVED

- **Criteria**: Makes Sense ✓ · Still Valid ✓ · Worth Adding ✓ (fills a total gap)
- The article's correct kernel, buried under P1's wrong framing.
- **Already expressed**: nothing. `grep -ri stream references/` returned only NATS streams, stdout/stderr
  streams, and a passing GATs mention of lending iterators.
- **Target**: `rules-core.md` → **ASYNC-13** (new)
- **Modifications**: substantial. Rewritten around pull semantics, selection by *readiness rather than
  finiteness*, `impl Stream` returns (async counterpart of API-3), `async_stream::stream!`, adapter
  laziness, backpressure-by-construction, and three verified footguns (the `Unpin` requirement, the
  `futures`/`tokio_stream` `StreamExt` collision, the missing `sum`).

### P3 — "Iterators for finite collections, Streams for infinite" · REJECTED

- **Criterion failed**: Makes Sense (false dichotomy)
- Iterators are routinely infinite (`std::iter::repeat`, `successors`, `cycle`); streams are routinely
  finite. Finiteness is orthogonal — the axis is whether producing the next item requires awaiting.
- **Disposition**: corrected inline in ASYNC-13.

### P4 — `sum_stream` code example · REJECTED

- **Criterion failed**: Makes Sense (does not compile)
- `futures::StreamExt` exposes no `sum`. Correct spelling is
  `.fold(0, |a, n| async move { a + n }).await`. Note the two `StreamExt` traits differ here:
  `tokio_stream`'s `fold` takes a *sync* closure, `futures`' takes an async one — a trap worth recording,
  and now recorded.

### P5 — "Real Problem: Handling Logs in Real Time" · REJECTED (most significant error)

- **Criterion failed**: Makes Sense (the example does not do what the prose claims)
- Two defects. The code does not compile (`tokio::io::Lines` is not a `Stream`; it has an inherent
  `next_line()`). And once corrected, it still **does not tail** — it terminated at EOF in 253.6µs and
  never observed a line appended one second later. Async means the *thread* is not blocked during an
  in-flight read; it does not convert EOF into "wait for more data". The article's entire motivating
  narrative rests on a behaviour that does not exist.
- **Disposition**: inverted into **ASYNC-14** (new) as a defect to flag, with the measurement recorded and
  the three real strategies named (offset-tracking re-poll with rotation handling, `notify`, log transport).

### P6 — Benchmark: iterator 26 ms / stream 33 ms / multi-threaded 18 ms · REJECTED

- **Criterion failed**: Still Valid (technical validation) — no methodology, no code, not reproducible.
- Measured locally: 1M i32 map+sum runs in **0.50 ms** release, **12.9 ms** debug. The quoted 26 ms is ~50×
  the release figure and 2× the debug figure, which points at an unoptimised or otherwise flawed harness.
  More importantly, "multi-threaded streams beat iterators, 18 ms vs 26 ms" is meaningless for a workload
  that is sub-millisecond when compiled with optimisations.
- No performance claim from this article was integrated.

### P7 — "Async overhead only matters for purely CPU-bound tasks" · ALREADY EXPRESSED

- **ASYNC-7** already states this with more precision: "use sync code when async adds no value… An
  `async fn` that never yields is just overhead." No addition warranted.

### P8 — "Streams shine when concurrency or I/O latency is involved" · REJECTED (too generic)

- **Criterion failed**: Worth Adding. True but content-free at this altitude; the actionable form is
  already split across ASYNC-5, ASYNC-7 and CONC-3.

### P9 — Serial `while let Some(x) = lines.next().await` shown without comment · APPROVED (as enhancement)

- The article presents the serial stream loop as the destination, never noting that per-item async work
  inside it runs strictly one at a time. **ASYNC-5** covered this for futures (`join_all`/`FuturesUnordered`)
  but not for streams.
- **Target**: `rules-core.md` → **ASYNC-5** (enhanced, not a new rule, per the integration workflow's
  "append to an existing rule rather than creating a new one")
- **Modifications**: added `buffered` / `buffer_unordered` / `for_each_concurrent`, with the note that the
  concurrency limit doubles as the bound preventing unbounded fan-out (CONC-3).

## Summary

### Approved (2)

| Piece | Target | Form |
|---|---|---|
| P2 — Stream as async Iterator | `rules-core.md` ASYNC-13 (new) | Rewritten; article's framing inverted |
| P5 — async ≠ blocking at EOF | `rules-core.md` ASYNC-14 (new) | Inverted into a defect to flag |
| P9 — serial work in stream loops | `rules-core.md` ASYNC-5 (enhanced) | Appended to existing rule |

### Rejected (6)

| Piece | Criterion failed | Reason |
|---|---|---|
| P1 — streams are push-based | Makes Sense | Contradicted by the trait definition |
| P3 — finite vs infinite axis | Makes Sense | False dichotomy |
| P4 — `sum_stream` example | Makes Sense | E0599, does not compile |
| P5 — tailing example *as written* | Makes Sense | Does not compile; corrected version does not tail |
| P6 — benchmark figures | Still Valid | Not reproducible; off by ~50× |
| P8 — "streams shine with I/O" | Worth Adding | Too generic |

### Already expressed (1)

- P7 → **ASYNC-7**

### Needs clarification (0)

## Updated files

| File | Change |
|---|---|
| `skills/code-review-rust/references/rules-core.md` | **+ASYNC-13** (Stream vs Iterator, pull semantics, footguns); **+ASYNC-14** (async ≠ waits at EOF; `Lines` is not a `Stream`); **ASYNC-5** enhanced with stream concurrency |
| `skills/code-review-rust/references/anti-patterns.md` | +3 async anti-patterns: async-mistaken-for-waits-at-EOF, serial work in stream loops, `Stream` treated as push-based |
| `skills/code-review-rust/SKILL.md` | +3 scan-checklist rows: EOF-follow loops (ASYNC-14), serial stream loops (ASYNC-5/13), dual `StreamExt` imports (ASYNC-13) |

All rule text references only APIs confirmed to compile on rustc 1.98.0.
