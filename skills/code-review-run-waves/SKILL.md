---
name: code-review-run-waves
description: Run every open code-review wave concurrently, each in its own git worktree, land them one at a time through the merge lock, and report which waves closed and which parked
allowed-tools: Bash, Read, Edit, Write, Grep, Glob
license: Apache-2.0
---

# Task

Run all open `code-review-plan-waveN` waves in parallel — one isolated git worktree each —
and land them onto the base branch one at a time. This is the fan-out wrapper around
**code-review-run-wave**; that skill remains the authority on how a single wave executes.

This skill has a **hard dependency on the code-review-run-wave skill**: install it too,
and read its `references/worktree-protocol.md` before running this. Every isolation,
claiming, merging, and recovery rule there applies unchanged here.

## Purpose

- Start every open wave concurrently instead of one at a time
- Keep each wave's edits, build, and index isolated from the others
- Serialise the merges so the base branch is only ever mutated by one wave
- Report per-wave outcomes, including which waves parked and how to resume them

## Preconditions

Check all three before starting. Stop and report if any fails:

1. **The base branch is clean.** `git status --short` in the main checkout is empty.
   Waves rebase onto this branch; uncommitted work there will be swept into a wave's
   integration verify or block the rebase.
2. **No triage is running.** `code-review-triage` mutates task state in bulk and races
   with member status flips. Run it to completion first.
3. **No stale locks or worktrees.** `git worktree list` shows only the main checkout, or
   only worktrees you intend to resume, and `.git/code-review-merge.lock` does not exist.
   Clear genuinely stale state per the Recovery section of
   `skills/code-review-run-wave/references/worktree-protocol.md` — never by force-removing
   worktrees or deleting branches that carry commits.

## Step 1 — Enumerate open waves

```bash
backlog task list -a code-review-wave -s 'To Do' --plain
```

If the list is empty, stop and report "no open waves".

For each wave, read its recorded file scope and overlap notes:

```bash
backlog task view <waveTaskId> --json
```

`code-review-triage` stamps each wave with one `--modified-file` per file in its scope and
an `Overlaps:` note. If a wave predates that and carries no scope, treat its overlap as
unknown and place it last in the merge order.

## Step 2 — Plan the merge order

Rank waves by how many other waves they share files with, fewest first. Waves that overlap
nothing rebase cleanly and should land while the others are still working; heavily
overlapping waves land last, when the base branch has stopped moving under them.

Print the plan **before** starting anything: the wave list, each wave's file count, the
overlap pairs, and the intended merge order. The user should be able to see what is about
to run in parallel without reading task files.

This order is advisory. Waves merge through a lock regardless, so a wave that finishes
early may land out of order — that is correct behaviour, not a violation.

## Step 3 — Fan out

Start one **code-review-run-wave** runner per wave, concurrently. Each runner executes that
skill end to end for its own wave: claim → fix members → pre-merge verify → commit →
discharge → merge → close.

Launch runners as parallel subagents where the platform supports it, or as separate CLI
invocations otherwise. Each runner needs only its wave task ID; it derives its branch,
worktree path, and commit-script path from that ID per the protocol.

Rules for the fan-out:

- **Cap concurrency at 4 waves.** Each worktree is a full checkout and each pre-merge
  `ops verify` is a full build; beyond four the machine thrashes and wall-clock gets worse,
  not better. Queue the rest and start them as slots free.
- **Never assign two runners to one wave.** The claim branch enforces this, but do not rely
  on it — hand each runner a distinct wave ID.
- **A failed wave never blocks the others.** If a runner parks its wave, the remaining
  runners continue. Collect the failure and report it; do not abort the fan-out.
- **Do not merge on a runner's behalf.** Each runner performs its own Step 7 merge under
  the shared lock. Centralising merges here would duplicate the protocol and lose the
  runner's context for conflict resolution.

## Step 4 — Wait for every runner

Wait for all runners to return before doing anything else. A runner still in flight owns a
worktree, may hold the merge lock, and has task state half-written — reporting or cleaning
up around it produces a wrong summary and can destroy work.

If a runner appears stuck, inspect rather than kill it: `git worktree list` shows whether
its worktree still exists, and `.git/code-review-merge.lock` shows whether a merge is in
progress.

## Step 5 — Verify the landed result

After every runner has returned, run the QA gate once on the base branch in the main
checkout:

```bash
ops verify
```

Each wave already ran its own integration verify before its fast-forward, so this is a
final confirmation that the fully combined result is good. If it fails, the failure belongs
to the combination of waves rather than to any single one: fix it on the base branch, or
file a `Triage` task describing it, following the **No leftovers** contract in
`code-review-run-wave`.

Then commit the accumulated backlog task-file changes from the main checkout as one
`chore(backlog)` commit.

## Step 6 — Confirm teardown

For every wave that landed, its runner should have removed the worktree and deleted the
branch. Confirm:

```bash
git worktree list
git branch --list 'code-review/*'
```

Anything left belongs to a **parked** wave and stays. Do not clean it up — the worktree and
branch are what make that wave resumable. Never force-remove a worktree or `-D` a wave
branch to tidy the output.

## Step 7 — Report

Print one table plus the follow-ups:

- per wave: task ID, title, ✓ landed / ✗ parked / ~ nothing to do, member counts
  (`✓`/`✗`/`~` as defined in `code-review-run-wave`), and pre-merge + integration verify
  results
- merge order as actually executed, and any wave that had to resolve a rebase conflict
- final base-branch `ops verify` result
- for each parked wave: the reason, its branch, its worktree path, and the next action to
  resume it
- every `Triage` task filed by any runner, by ID

The same **No leftovers** rule applies to this report: an open thread is either fixed or
filed as a task. Nothing leaves this skill as prose advice.

## Concurrency

This skill *is* the concurrency layer — it should not itself be run twice at once. A second
invocation would enumerate the same waves and race for the same claim branches; the claims
would mostly fail, but the two runs would still fight over the merge lock and produce two
contradictory reports.

Safe alongside it: nothing that writes task state. `code-review-triage` in particular must
finish before this starts.

## References

Both live in the **code-review-run-wave** skill, which must be installed alongside this one:

- `skills/code-review-run-wave/SKILL.md` — the per-wave skill this fans out to
- `skills/code-review-run-wave/references/worktree-protocol.md` — naming, claiming, the merge lock, two-stage verification, and recovery
