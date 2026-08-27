# Rust Meta Evaluation — "Error Handling in Async Rust" (article paste)

**Date**: 2026-08-27
**Source**: User-pasted article — "Error handling is critical in any language. But in async Rust… 10 best practices."
**Toolchain used for validation**: rustc 1.98.0, tokio 1.53.1 (`full`), anyhow 1.0.104, thiserror 2.0.20, futures 0.3.34, tokio-util 0.7

## Executive Summary

| Metric | Count |
|---|---|
| Pieces extracted | 10 |
| Approved | 5 (2 new rules, 3 rule enhancements) |
| Rejected — already expressed | 4 |
| Rejected — too generic | 1 |
| Needs clarification | 0 |

**Overall assessment**: **Sound but shallow source; two genuine gaps found.** Unlike the previous streams
article, every code sample intended as compilable code does compile, and nothing in it is outright false.
(The exception is the section 9 snippet, which is illustrative pseudocode — a module-scope `if let` over an
undefined `MyError` — and is excluded from that count; see P9.) That is also its limitation:
sections 1--3 and 9--10 are a restatement of ERR-1/ERR-3/ERR-4/READ-8, which `code-review-rust` already
covers in more depth than the article does.

The value is concentrated in sections 4--7, where the article correctly identifies four topics the rules
had **no coverage of at all** — detached-task failure, the nested `timeout` result, per-channel failure
shapes, and signal handling — and then states each one loosely enough that the precise version had to be
established by running code rather than by quoting the source. Two of the article's own examples contain
defects worth recording as scan signals: its `AppError` enum duplicates the source into the display
message, and its `shutdown_signal()` misses SIGTERM, which is the signal that actually ends the process in
every containerised deployment.

## Validation performed

Every behavioural claim below was executed, not assessed by eye.

| Claim | Method | Result |
|---|---|---|
| The six compilable article code samples build | `cargo build` (crates substituted for `reqwest`/`sqlx`) | **Pass** — correct as written; the section 9 snippet is pseudocode and was not counted |
| "Unawaited tasks may panic silently" | Spawned a panicking task, dropped the handle | **Half true** — default hook *does* print `thread 'tokio-rt-worker' panicked at …` to stderr; but nothing propagates and the process **exits 0** |
| Does that hold under `panic = "abort"`? | Same binary with `panic = "abort"` in `[profile.dev]` | **No** — process dies at the panic; the `JoinHandle` never resolves and no line after `h.await` runs. CONC-13 is scoped to unwinding builds |
| `JoinError` == panic | `h.await` on a panicked task vs. an `abort()`ed one | **False** — `is_panic()=true/is_cancelled()=false` vs. `is_panic()=false/is_cancelled()=true`; the article's `"Task panicked: {:?}"` mislabels every cancellation |
| `timeout` returns `Result<Result<T,E>, Elapsed>` | Compiled the article's match arms | **True** |
| "Receive errors happen if the sender disappears" | Typed `rx.recv().await` on `tokio::sync::mpsc` | **False for mpsc** — returns `Option<T>`, not `Result`; `None` is normal termination |
| `broadcast` overflow behaviour | capacity 4, 10 sends, then `recv()` | `Err(Lagged(6))` then resumes at message 6 — **silent loss of 6 messages, reported once** |
| `ctrl_c()` covers shutdown | Sent SIGTERM to a process awaiting only `ctrl_c()` | **Died immediately** — the line after the await never ran |
| SIGTERM + `CancellationToken` + bounded drain | Same process with a `select!` over `ctrl_c()`/`SignalKind::terminate()` | Cleanup ran, workers observed cancellation, exit 0 |
| Is a dropped `ctrl_c()` future harmless? | SIGTERM won the `select!`, then sent SIGINT during the drain | **No** — silently swallowed: tokio's process-wide SIGINT handler stays installed, so the signal is neither observed nor fatal and the drain ran to completion |
| Holding both `Signal` streams through the drain | Same, with `SignalKind::interrupt()` installed at startup | Second interrupt observed — "Ctrl-C again to force quit" becomes implementable |
| Can force-abort bound the drain? | `abort()` on a started `spawn_blocking` task; `JoinSet::shutdown()` with one in the set | **No** — abort returned in ~1.5µs and did nothing: closure ran to completion and `await` gave `Ok(value)`, not a `JoinError`. `shutdown()` waited 2.7s vs ~0.5ms for an async task |
| `Runtime::shutdown_timeout` as the blocking-work bound | 1s timeout against a 10s blocking task, process kept alive afterwards | Bounds the **wait**, not the work: returned in 1.0005s, but the abandoned closure ran to completion 2s later and wrote its output file. Not terminated, thread not killed; takes `self`, so needs an owned runtime (`Runtime::new()` or `runtime::Builder`), not `#[tokio::main]` |
| `mpsc` `close()` vs. dropped receiver | `rx.close()` with sender and receiver both alive | `send` → `Err(SendError)`; `recv` drained the buffered values then returned `None` while the sender was still alive |
| `#[error("…: {0}")]` alongside `#[from]` | Printed via anyhow `{}`, `{:#}`, `{:?}` | **Duplicates** — `{:#}` → `io failed: no such file: no such file`; `{:?}` repeats it under `Caused by:` |

## Detailed Results

### P1 — "The basics still apply: return `Result`, propagate with `?`" · REJECTED

- **Criterion failed**: Worth Adding (duplicate)
- **Already expressed**: ERR-1 (propagate with `?`; handle or propagate, never both).
- The `async` framing adds nothing — `?` in an `async fn` desugars identically.

### P2 — "Use context-rich errors (`anyhow::Context`)" · REJECTED

- **Criterion failed**: Worth Adding (duplicate)
- **Already expressed**: ERR-4 (`.with_context()`), and ERR-13/ERR-14 cover the two concrete cases the
  article gestures at (filesystem paths, deserialization field paths) with far more specificity.
- Example verified to compile; `Context` applies to `Result<T, io::Error>` from `tokio::fs` as claimed.

### P3 — "Prefer `thiserror` for custom errors" · REJECTED as stated · one *correction* APPROVED

- **Criterion failed** (as stated): Worth Adding — **already expressed** in ERR-3 (choose by caller intent:
  `thiserror` when callers match, `anyhow` when they propagate), ERR-2, ERR-10.
- **However**: the article's own `AppError` example demonstrates a defect. `#[error("Request failed: {0}")]`
  on a variant carrying `#[from] reqwest::Error` sets the *message* and the *source* to the same value, so
  every chain-walking printer emits it twice (verified above). This is a common, silent quality bug in
  otherwise-correct error enums and had no coverage.
- **Target**: `rules-core.md` → **ERR-9** (enhanced)
- **Integration point**: appended to the existing one-line `Error::source()` rule, which is where the
  source-chain contract already lives.

### P4 — "Watch for task panics; always `.await` the `JoinHandle`" · APPROVED (with corrections)

- **Criteria**: Makes Sense ✓ · Still Valid ✓ · Worth Adding ✓ (fills a gap)
- **Already expressed**: partially — CONC-6 recommends `JoinSet` for task groups and mentions orphaned
  tasks "silently leak resources or panic", but nothing covered `JoinHandle`/`JoinError` semantics: no
  guidance existed on what a dropped handle costs, or on distinguishing panic from cancellation.
- **Corrections applied before integration**:
  1. "Panic silently" is imprecise — the default hook prints to stderr. The *real* defect is that the
     failure leaves the program's control flow entirely and **the process still exits 0**, so a dead
     background reconciler reads as a healthy service.
  2. The article's handler labels every `JoinError` a panic. `is_panic()` / `is_cancelled()` /
     `into_panic()` + `resume_unwind` added; cancellation during shutdown is the expected path and must
     not be logged as an error.
  3. Added the legitimate-detached-task carve-out so the rule does not read as "never drop a handle".
  4. **After review**: scoped the whole rule to `panic = "unwind"`. Under `panic = "abort"` there is no
     unwind for tokio to catch, so the first task panic kills the process before any `JoinError` exists —
     the opposite failure mode (loud crash, no supervision possible) rather than the silent one.
- **Rust version**: tokio 1.x, no MSRV concern.
- **Target**: `rules-core.md` → **CONC-13** (new; CONC previously ended at 12)
- **Integration point**: after CONC-12, adjacent to CONC-6 which it cross-references.

### P5 — "`timeout` returns `Result<Result<T, E>, Elapsed>` — two layers" · APPROVED (extended)

- **Criteria**: Makes Sense ✓ · Still Valid ✓ · Worth Adding ✓ (complements ASYNC-6)
- **Already expressed**: ASYNC-6 mandates timeouts + retries + backoff but says nothing about the return
  shape or what a timeout *means* to the operation underneath.
- **Extended beyond the source**: the article stops at "you need two layers of handling". Two consequences
  matter more than the syntax and were added: a bare `Elapsed` propagated to a caller identifies no
  deadline (map it into a domain variant per ERR-2/ERR-4); and a timeout **cancels at an await point
  without rolling back** — partial writes stand, post-await cleanup never runs — so a timed-out call is an
  *unknown outcome*, and retrying it (as ASYNC-6 instructs) requires idempotency.
- **Target**: `rules-core.md` → **ASYNC-6** (enhanced, two sub-bullets)

### P6 — "Channel errors are real too" · APPROVED (substantially corrected)

- **Criteria**: Makes Sense ✗ as stated (one claim is wrong) · Still Valid ✓ · Worth Adding ✓
- The article's framing — "send errors happen if the receiver disappears, receive errors if the sender
  disappears, always handle them" — is **wrong for the channel it demonstrates**: `tokio::sync::mpsc`'s
  `recv()` returns `Option<T>`, not `Result`, and `None` is ordinary termination, not an error.
- **What is genuinely missing from the rules**: the failure shapes differ per channel and only one of them
  is dangerous. `broadcast::error::RecvError::Lagged(n)` is silent data loss *reported as a recoverable
  error* — `recv()` keeps working afterwards from the oldest retained message — so the common `?` or
  log-and-continue handling drops `n` messages while the consumer reports healthy. Nothing in
  `code-review-rust` mentioned `Lagged`.
- **Also added**: `SendError<T>` carries the unsent value back, so a failed send can be re-routed or
  counted rather than dropped — the article's `if let Err(_e)` discards it.
- **Target**: `rules-core.md` → **CONC-8** (enhanced with a per-operation failure-shape table beneath the
  existing channel-selection table)

### P7 — "Graceful shutdowns matter" · APPROVED (the article's example is the anti-pattern)

- **Criteria**: Makes Sense ✓ (topic) · Still Valid ✓ · Worth Adding ✓ (fills a gap)
- **Already expressed**: nothing. CONC-4 shows a `select!` shutdown arm and NATS-7 says to `drain()`, but
  no rule said where the shutdown signal comes from.
- **The article's `shutdown_signal()` is the defect, not the fix.** `ctrl_c()` listens for SIGINT only;
  Kubernetes, Docker, and systemd stop processes with SIGTERM, whose default disposition is immediate
  death. Verified: the process exited before the line after the await, so no cleanup ran. **Corrected
  after review**: an earlier draft added that the orchestrator "SIGKILLs it after the grace period
  regardless". That misstates the sequence — an untrapped SIGTERM is already fatal, so there is no
  process left to kill. SIGKILL arrives only when the process is *still alive* at the end of the
  grace period, which is the slow-drain failure mode, not the unhandled-signal one.
- **Extended with three requirements the article omits**, each now a separate finding: propagate the
  signal to running tasks cooperatively (`CancellationToken` / `watch`), bound the drain with a
  timeout sized below the platform grace period, and release externals explicitly. Windows counterparts
  noted; `.expect()` on handler registration flagged per ERR-5.
- **Correction applied after review**: an earlier draft of the third requirement claimed `Drop` does not
  run for aborted tasks. That is false — abort drops the future at its current await point, and `Drop`
  runs for owned locals *and* task-local values (verified: both guards fired, tokio 1.53). The accurate
  statement is narrower: `Drop` is synchronous and cannot await, so cleanup that is itself an async
  operation — a NATS `drain()`, a graceful close, a flush that round-trips — does not happen on abort, and
  neither does code positioned after the await the task was parked on. The claim that `thread_local!`
  destructors never run for unjoined threads was dropped from this rule; only the platform-specific and
  process-exit caveats belong here, and CONC-11 already owns the `thread_local!` lifecycle.
- **Target**: `rules-core.md` → **CONC-14** (new)

### P8 — "Handling many futures together (`FuturesUnordered`), inspect each result" · REJECTED

- **Criterion failed**: Worth Adding (already expressed + too generic)
- **Already expressed**: ASYNC-5 owns `join_all`/`FuturesUnordered` versus serial `.await`, and CONC-6 owns
  tracking spawned task outcomes. "Never just await on multiple futures without checking outcomes" adds no
  actionable detail beyond those.
- The example compiles and is idiomatic; it simply restates ASYNC-5's recommendation.

### P9 — "Use `tracing`, not `println!`" · REJECTED

- **Criterion failed**: Worth Adding (duplicate)
- **Already expressed**: READ-8 (prefer `tracing` over `log` for service code; `println!`/`eprintln!` in
  non-binary non-test code is a finding), with the library/binary distinction the article lacks.
- Note the article's snippet is illustrative pseudocode — the trailing `if let` sits at module scope and
  `MyError` is undefined — but the guidance itself is correct.

### P10 — "Best practices summary" + "Final thoughts" · REJECTED

- **Criterion failed**: Makes Sense (too generic) — a recap of P1--P9 plus closing prose. No new content.

## Summary

### Approved (5)

| # | Content | Target | Type |
|---|---|---|---|
| P3 | Source duplicated into `#[error]` message when the field is `#[from]`/`#[source]` | `rules-core.md` → ERR-9 | enhancement |
| P4 | Detached-task failure: dropped `JoinHandle`, exit 0, `JoinError` ≠ panic | `rules-core.md` → CONC-13 | **new rule** |
| P5 | Nested `timeout` result; `Elapsed` mapping; cancel-without-rollback | `rules-core.md` → ASYNC-6 | enhancement |
| P6 | Per-channel failure shapes; `broadcast` `Lagged` as silent data loss | `rules-core.md` → CONC-8 | enhancement |
| P7 | Shutdown must handle SIGTERM; propagate, bound the drain, release externals | `rules-core.md` → CONC-14 | **new rule** |

### Rejected (5, plus P3's stated form — P3 counts as approved above via its correction)

| # | Content | Reason |
|---|---|---|
| P1 | `Result` + `?` in async | Already expressed — ERR-1 |
| P2 | `anyhow::Context` for context-rich errors | Already expressed — ERR-4, ERR-13, ERR-14 |
| P3 | `thiserror` for custom error types (*as stated*) | Already expressed — ERR-3, ERR-2, ERR-10 |
| P8 | `FuturesUnordered`, inspect each result | Already expressed — ASYNC-5, CONC-6; too generic |
| P9 | `tracing` over `println!` | Already expressed — READ-8 |
| P10 | Best-practices recap | Too generic; no new content |

### Needs clarification (0)

None. Every claim resolved to true, false, or already-covered under execution.

## Updated files

| File | Change |
|---|---|
| `skills/code-review-rust/references/rules-core.md` | **New**: CONC-13 (detached task failure), CONC-14 (shutdown signals). **Enhanced**: ERR-9 (source/message duplication), ASYNC-6 (nested timeout result, cancel semantics), CONC-8 (per-channel failure-shape table, `Lagged`) |
| `skills/code-review-rust/references/anti-patterns.md` | 4 entries added to *Async & Concurrency* / *Error Handling*: fire-and-forget `spawn`, Ctrl-C-only shutdown, swallowed `Lagged`, duplicated source in message |
| `skills/code-review-rust/SKILL.md` | 5 rows added to the scan-signal table (CONC-13/6, CONC-14, CONC-8, ASYNC-6, ERR-9) |

Rule numbering after this pass: `ERR` → 14, `CONC` → 14, `ASYNC` → 14. No IDs reused; no retired IDs touched.
