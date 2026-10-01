---
name: code-review-triage
description: Triage backlog tasks in Triage status, group them semantically, record each wave's file scope, create a code-review-plan-waveN parent task, and flip grouped tasks to To Do
allowed-tools: Read Grep Glob Bash(ops --version) Bash(ops backlog:*)
license: Apache-2.0
---

# Task

Review all backlog tasks currently in `Triage`, group them by semantic relatedness, and
materialise each group as a `code-review-plan-waveN` parent task carrying a recorded file
scope so waves can later be run in parallel and merged in a sensible order.

## Step 1 — Gather triage tasks

Requires `ops` 0.74.0 or newer (`ops --version`), for `wave create` and `wave overlap`.
Stop with a clear message if it is older.

```bash
ops backlog task list --status='Triage' --plain
```

For each task ID returned, read the full task body so grouping is based on content, not
just titles:

```bash
ops backlog task view <taskid> --plain
```

If a task references code paths, optionally Read/Grep those files to confirm scope overlap
between tasks.

## Step 2 — Determine the next wave number

Check existing wave tasks so N is monotonically increasing:

```bash
ops backlog wave list --plain
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
   `code-review-web` / `code-review-lovable` carries one `--modified-file` entry per file; read them from
   `ops backlog task view <taskid> --json` (`.task.modifiedFiles`).
2. Fall back to parsing the `**File**: \`<path>:<line>\`` line in the task description for
   older tasks filed before that field existed. Strip the `:<line>` suffix.

Normalise every path to repo-root-relative, without line numbers, and deduplicate.

## Step 5 — Create each wave in one step

For each group:

```bash
ops backlog wave create 'code-review-plan-waveN' \
  --members TASK-0001,TASK-0002,TASK-0003 \
  -d 'code-review-plan-waveN' \
  --modified-file crates/foo/src/lib.rs \
  --modified-file crates/foo/src/error.rs
```

Use the literal wave number for `N` (e.g. `wave0`, `wave1`). One command does what used to
be a create plus one edit per member:

- creates the parent in `To Do`, labelled `code-review-wave`. That label is what makes
  the task a wave, and what `ops backlog wave list` finds
- makes the parent depend on every member, and sets each member's `parent_task_id`,
  so `ops backlog wave members` sees the membership from both sides
- flips every member to `To Do`
- records the group's full file scope, one `--modified-file` per path from Step 4

It refuses, writing nothing, when any member is missing, is already in a wave, or is
itself a wave. Fix the grouping and rerun rather than working around it.

Do **not** put anything in `assignee`. It used to carry the `code-review-wave`
marker; that moved to the label, and the field is now free for a real person.

Keep the description short. The grouping rationale goes in the task body via `--plan` if
useful.

Tasks that were **not** grouped stay in `Triage`, untouched. Do not move them to `To Do`:
a task in `To Do` with no wave parent belongs to no wave, will never be picked up by
`code-review-run-wave`, and is effectively lost. Leaving it in `Triage` guarantees the next
triage run reconsiders it.

## Step 6 — Record overlaps and the merge order

Once every new wave exists, compute overlap against **every** open wave, the new ones
and those already in flight:

```bash
ops backlog wave overlap --json
```

For each open wave it reports the file scope, the paths shared with each other open wave,
and a suggested merge order: fewest shared paths first, ties by task id. Record each new
wave's overlap set in its notes, so a runner can see it without recomputing:

```bash
ops backlog task edit --append-notes 'Overlaps: TASK-0119 (crates/foo/src/lib.rs)' <waveTaskId>
```

If a wave overlaps nothing, record `Overlaps: none`.

## Step 7 — Report

Print a concise summary:

- wave number(s) created
- for each wave: the parent task ID, a one-line rationale, the member task IDs, and the
  number of files in its scope
- the **suggested merge order** from `ops backlog wave overlap`: least-overlapping wave
  first, so the waves most likely to rebase cleanly land while the others are still
  running. For each wave, list which other waves it shares files with
- any tasks left in `Triage` because they did not fit a group, and why

The merge order is advisory. `code-review-run-wave` serialises merges through a lock
regardless of the order waves are started in; this hint only reduces how often a wave has
to resolve a conflict.

## Concurrency

Triage is a **single-writer** step. It mutates status and the wave link across many tasks
at once, so it must not run alongside anything else that writes task state:

- Do not run two triage passes concurrently.
- Do not run triage while any wave is in progress — `code-review-run-wave` flips member
  task status as it works, and the two would race.

Run triage to completion first, then start waves. `code-review-rust` / `code-review-web` /
`code-review-lovable` reviews are safe to run concurrently with each other (each finding is its own new task
file), but finish them before triaging so the wave captures everything.

## References

- `skills/code-review-run-wave/references/worktree-protocol.md` — how waves created here are later isolated, merged, and recovered (part of the **code-review-run-wave** skill)
