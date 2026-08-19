---
name: code-review-run-waves
description: Run every open code-review wave concurrently, each in its own git worktree, land them one at a time through the merge lock onto a per-run integration branch, open a single PR to main, and report which waves closed and which parked
allowed-tools: Bash, Read, Edit, Write, Grep, Glob
license: Apache-2.0
---

# Task

Run all open `code-review-plan-waveN` waves in parallel — one isolated git worktree each —
and land them one at a time onto a per-run integration branch, then deliver the whole run
to `main` as a single PR. This is the fan-out wrapper around
**code-review-run-wave**; that skill remains the authority on how a single wave executes.

This skill has a **hard dependency on the code-review-run-wave skill**: install it too,
and read its `references/worktree-protocol.md` before running this. Every isolation,
claiming, merging, and recovery rule there applies unchanged here.

## Purpose

- Start every open wave concurrently instead of one at a time
- Keep each wave's edits, build, and index isolated from the others
- Serialise the merges so the integration branch is only ever mutated by one wave
- Deliver the run to `main` as one PR, giving the combined result a human review gate
- Report per-wave outcomes, including which waves parked and how to resume them

## Preconditions

Check all three before starting. Stop and report if any fails:

1. **`main` is clean and checked out.** `git status --short` in the main checkout is
   empty. The integration branch is created from `main` and the main checkout stays on
   it for the whole run; uncommitted work there will be swept into a wave's integration
   verify or block the rebase.
2. **No triage is running.** `code-review-triage` mutates task state in bulk and races
   with member status flips. Run it to completion first.
3. **No stale locks or worktrees.** `git worktree list` shows only the main checkout, or
   only worktrees you intend to resume, and `.git/code-review-merge.lock` does not exist.
   Clear genuinely stale state per the Recovery section of
   `skills/code-review-run-wave/references/worktree-protocol.md` — never by force-removing
   worktrees or deleting branches that carry commits.

## Step 0 — Prepare the run integration branch

Waves land on an integration branch, not `main`, so the whole run can be reviewed and
merged as one PR. The main checkout must already be clean and on `main` or a
`code-review/run-*` branch (Preconditions). Resolve which run branch this run uses:

- **On a `code-review/run-*` branch:** a previous run left it behind (parked waves
  keep it alive). Resolve that branch's run state (below) and follow it.
- **On `main`:** if `code-review/run-$(date +%Y%m%d)` does not exist, create it:

  ```bash
  git checkout -b code-review/run-$(date +%Y%m%d) main
  ```

  If it does exist, resolve its run state (below) and follow it.

**A run branch's state** is decided by its PR, never by commit ancestry — under this
repo's squash merges a merged run branch stays outside `main`'s ancestry forever, so
`git log main..…` would flag it as resumable even after it fully landed:

```bash
gh pr view <branch> --json state --jq .state 2>/dev/null || echo NONE
```

- `OPEN` — an active run: **resume** it. Newly landed waves push onto the same PR.
- `NONE` — a run that parked before publishing (Step 5 never ran): **resume** it; its
  previously landed waves must stay under this branch, not be stranded on a new one.
- `MERGED` — a completed run whose cleanup was skipped: delete the branch
  (`git branch -D <branch>` — the PR state is the proof it landed) and create a fresh
  one; the freed name needs no suffix.
- `CLOSED` — closed without merging: stop and report; re-pushing the branch or
  re-running its waves is the user's call, not this skill's.

Record the exact branch name chosen — Step 5 pushes and PRs it. Runners derive their
landing target from whatever the main checkout has checked out, per the Worktree
Protocol — the PR to `main` is opened only after the run's waves have landed and the
combined result has passed `ops verify`.

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
overlapping waves land last, when the integration branch has stopped moving under them.

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
- **Never switch the main checkout's branch mid-run.** Runners derive their landing
  branch from whatever the main checkout has checked out — the Step 0 integration
  branch. Checking out something else redirects or breaks every subsequent merge.

## Step 4 — Wait for every runner

Wait for all runners to return before doing anything else. A runner still in flight owns a
worktree, may hold the merge lock, and has task state half-written — reporting or cleaning
up around it produces a wrong summary and can destroy work.

If a runner appears stuck, inspect rather than kill it: `git worktree list` shows whether
its worktree still exists, and `.git/code-review-merge.lock` shows whether a merge is in
progress.

## Step 5 — Verify the run and open the PR

After every runner has returned, run the QA gate once on the integration branch in the
main checkout:

```bash
ops verify
```

Each wave already ran its own integration verify before its fast-forward, so this is a
final confirmation that the fully combined result is good. If it fails, the failure belongs
to the combination of waves rather than to any single one: fix it on the integration
branch and re-run. **If it cannot be fixed in this run, stop before the push** — file a
`Triage` task describing it (the **No leftovers** contract in `code-review-run-wave`),
leave the integration branch unpushed, and report. Never push or open a PR for a result
that failed verification.

Parked waves do not block the PR — they are simply not in it. The report and the PR body
must state which waves landed and which parked.

Then commit the accumulated backlog task-file changes from the main checkout as one
`chore(backlog)` commit — it rides the PR, so task-status flips are reviewed alongside
the code they describe.

Then write the run report — the substance of Step 7: the wave table, the merge order as
executed, verify results, links to any `Triage` tasks filed, landed vs parked — to a
body file. Push the **recorded landing branch** (Step 0) and open the
run's single PR:

```bash
git push -u origin <landing-branch>
gh pr create --base main --head <landing-branch> \
  --title "code-review run <date>: <N> waves" \
  --body-file <report file>
```

Once the PR is open, append its URL to the report. Do not merge the PR yourself unless
the user asks — the PR is the run's human review gate.

After the PR merges, clean up. This repo squashes PRs to `main`, so the squash commit
shares no ancestry with the landing branch: `git branch -d` will refuse, and `-D` is
correct here because the merged PR is the proof the work landed:

```bash
git checkout main && git pull && git branch -D <landing-branch>
```

GitHub deletes the remote branch on merge, so nothing else remains. Squash also means
the run lands as one commit on `main` — the per-wave conventional commits are preserved
in the PR, not in `main`'s history.

## Step 6 — Confirm teardown

For every wave that landed, its runner should have removed the worktree and deleted the
branch. Confirm:

```bash
git worktree list
git branch --list 'code-review/*'
```

Anything left besides the run's own integration branch belongs to a **parked** wave and
stays. Do not clean it up — the worktree and branch are what make that wave resumable.
Never force-remove a worktree or `-D` a wave branch to tidy the output. The integration
branch itself stays until its PR merges (see Step 5 for the post-merge cleanup).

## Step 7 — Report

Print one table plus the follow-ups:

- per wave: task ID, title, ✓ landed / ✗ parked / ~ nothing to do, member counts
  (`✓`/`✗`/`~` as defined in `code-review-run-wave`), and pre-merge + integration verify
  results
- merge order as actually executed, and any wave that had to resolve a rebase conflict
- final integration-branch `ops verify` result
- the PR: URL, branch name, and a reminder that merging it is the run's human gate
  (post-merge cleanup in Step 5)
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
