---
name: code-review-triage
description: Triage backlog tasks in Triage status, group them semantically, record each wave's file scope, create a code-review-plan-waveN parent task, and flip grouped tasks to To Do
allowed-tools: Bash, Read, Grep, Glob
license: Apache-2.0
---

# Task

Review all backlog tasks currently in `Triage`, group them by semantic relatedness, and
materialise each group as a `code-review-plan-waveN` parent task carrying a recorded file
scope so waves can later be run in parallel and merged in a sensible order.

## Step 1 — Gather triage tasks

```bash
backlog task list --status='Triage' --plain
```

For each task ID returned, read the full task body so grouping is based on content, not
just titles:

```bash
backlog task view <taskid> --plain
```

If a task references code paths, optionally Read/Grep those files to confirm scope overlap
between tasks.

## Step 2 — Determine the next wave number

Check existing wave tasks so N is monotonically increasing:

```bash
backlog task list --plain | grep -i 'code-review-plan-wave'
```

Pick `N = (highest existing wave number) + 1`. If none exist, start at `0`.

## Step 3 — Group semantically

Group by **what the tasks are about**, not where they live. Good grouping axes:

- same crate / module / subsystem
- same concern (error handling, logging, test coverage, a specific refactor)
- tasks that must land together to be coherent
- tasks that share a root cause

A task belongs in exactly one group. Do not force-group unrelated tasks just to empty the
triage list — leftovers stay in `Triage` for a later wave.

Grouping stays semantic even though waves run in parallel. Two of the axes above are *by
concern* rather than by location, so waves are frequently semantically disjoint but
spatially overlapping. That is fine: `code-review-run-wave` isolates each wave in its own
git worktree, so overlap costs a merge, not correctness. Never split a coherent group just
to reduce file overlap — a wave whose members must land together is worth more than an
easy merge.

## Step 4 — Compute each group's file scope

For each group, build the union of the files its members touch:

1. Prefer the machine-readable field. Each finding filed by `code-review-rust` /
   `code-review-web` carries one `--modified-file` entry per file; read them from
   `backlog task view <taskid> --json`.
2. Fall back to parsing the `**File**: \`<path>:<line>\`` line in the task description for
   older tasks filed before that field existed. Strip the `:<line>` suffix.

Normalise every path to repo-root-relative, without line numbers, and deduplicate.

Then compute the pairwise overlap between each new group and **every other open wave**
(any `code-review-plan-wave*` task not `Done`), so merge order accounts for waves already
in flight:

```bash
backlog task list -a code-review-wave --plain
```

This produces, per group, the set of other waves it shares at least one file with.

## Step 5 — Create the wave parent task

For each group, create one parent with `--depends-on` pointing at every member and one
`--modified-file` per file in the group's scope:

```bash
backlog task create 'code-review-plan-waveN' \
  -d 'code-review-plan-waveN' \
  -s 'To Do' \
  -l code-review-wave \
  -a code-review-wave \
  --depends-on TASK001,TASK002,TASK003 \
  --modified-file crates/foo/src/lib.rs \
  --modified-file crates/foo/src/error.rs
```

Use the literal wave number for `N` (e.g. `wave0`, `wave1`). Every wave parent must carry:

- label `code-review-wave` (via `-l code-review-wave` on create, or `--add-label code-review-wave` via `backlog task edit` for backfills)
- assignee `code-review-wave` — **hardcoded, no `N` suffix** — so waves can be filtered via `backlog task list -a code-review-wave`
- the group's full file scope as repeated `--modified-file` flags

Record the overlap set in the task notes so a runner can see it without recomputing:

```bash
backlog task edit --append-notes 'Overlaps: TASK-0119 (crates/foo/src/lib.rs)' <waveTaskId>
```

If a group overlaps nothing, record `Overlaps: none`.

Keep the description short — the grouping rationale goes in the task body via `--plan` or
`--ac` if useful.

## Step 6 — Flip grouped tasks to `To Do` and link them to their wave

For every task that ended up **inside a group**:

```bash
backlog task edit -s 'To Do' <taskid>
backlog task edit -a <wave-task-id-here> <taskid>
```

The assignee is the wave's task ID, which is how membership is discoverable from the child
side (the wave parent's `Dependencies:` line is the other direction).

Tasks that were **not** grouped stay in `Triage`, untouched. Do not move them to `To Do`:
a task in `To Do` with no wave parent belongs to no wave, will never be picked up by
`code-review-run-wave`, and is effectively lost. Leaving it in `Triage` guarantees the next
triage run reconsiders it.

## Step 7 — Report

Print a concise summary:

- wave number(s) created
- for each wave: the parent task ID, a one-line rationale, the member task IDs, and the
  number of files in its scope
- the **suggested merge order** — least-overlapping wave first, so the waves most likely
  to rebase cleanly land while the others are still running — and, for each wave, which
  other waves it shares files with
- any tasks left in `Triage` because they did not fit a group, and why

The merge order is advisory. `code-review-run-wave` serialises merges through a lock
regardless of the order waves are started in; this hint only reduces how often a wave has
to resolve a conflict.

## Concurrency

Triage is a **single-writer** step. It mutates status and assignee across many tasks at
once, so it must not run alongside anything else that writes task state:

- Do not run two triage passes concurrently.
- Do not run triage while any wave is in progress — `code-review-run-wave` flips member
  task status as it works, and the two would race.

Run triage to completion first, then start waves. `code-review-rust` / `code-review-web`
reviews are safe to run concurrently with each other (each finding is its own new task
file), but finish them before triaging so the wave captures everything.

## References

- `skills/code-review-run-wave/references/worktree-protocol.md` — how waves created here are later isolated, merged, and recovered (part of the **code-review-run-wave** skill)
