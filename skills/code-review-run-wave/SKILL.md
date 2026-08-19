---
name: code-review-run-wave
description: Pick one code-review wave, run it in an isolated git worktree, apply every member fix, run QA, merge it back, and close only fully completed waves
allowed-tools: Bash, Read, Edit, Write, Grep, Glob
license: Apache-2.0
---

# Task

Claim a single `code-review-plan-waveN` parent task, apply every member fix **in an
isolated git worktree**, run the project's QA gates, land the wave on the run's
integration branch, and close out the wave only when every member task is actually
complete. The integration branch ships to `main` as one PR, opened in Step 8.

Waves run in isolation so several can run at once. The full mechanics — naming, claiming,
the merge lock, and recovery — are in
[Worktree Protocol](references/worktree-protocol.md). Read it before running this skill
for the first time; this file assumes it.

## Hard requirements

While implementing wave member fixes, you **must** read and follow the **code-review-rust**
skill in **implementation guardrail** mode: read `skills/code-review-rust/SKILL.md`
(especially Applicability) and the relevant sections of `skills/code-review-rust/references/rules.md`
and its scan checklist so fixes do not introduce new violations against those rules.
For frontend changes, use **code-review-web** the same way.
Fixing triaged backlog items without this guardrail often clears old findings but creates
new ones, repeating triage and review.

Unless the user explicitly asked for a formal review during this wave, do **not** create
new backlog tasks for issues you notice while fixing: treat `code-review-rust` rules as
acceptance criteria for the change itself, not as a trigger to file new tasks (see
guardrail mode in that skill).

### Isolation rules

These three are not optional — violating any one corrupts a concurrently running wave:

1. **Code edits happen in the wave worktree.** Never edit source files in the main
   checkout while a wave is claimed.
2. **Every `backlog` command runs from the main checkout.** Task files live inside the
   repo; editing them from a worktree puts them on the wave branch, where they collide
   with every other wave.
3. **The merge lock is held only across rebase → integration verify → merge.** Never
   across the member-fix phase.

### No leftovers

A wave run never ends with a prose list of "leftover concerns", "worth triaging", "if
you'd rather…", or "someone should look at this". Every open thread you surface has
exactly two legal dispositions:

1. **Do it now** — if it is inside the wave's scope and the fix is bounded, apply it in
   this run.
2. **File it** — otherwise create a backlog task in `Triage` so the next
   `code-review-triage` run picks it up (see Step 6).

Deciding you cannot fix something is fine. Leaving it only in the final report is not:
a report-only concern is invisible to the backlog and dies with the conversation. This
applies to concerns you raise about the wave's own side effects (commit shape, task
bookkeeping, mocks or variants your fix orphaned), not just to code findings — those
count as work discovered by the wave, and the exception above for "issues you notice
while fixing" does not cover them.

## Step 1 — List open waves

From the main checkout:

```bash
backlog task list -a code-review-wave -s 'To Do' --plain
```

If the list is empty, stop and report "no open waves".

## Step 2 — Prepare the landing branch and claim one wave

**Standalone runs only:** if the main checkout is on `main`, create the run integration
branch first — the wave lands on it and it ships to `main` as one PR (Step 8):

```bash
git checkout -b code-review/run-$(date +%Y%m%d)
```

If a `code-review/run-<date>` branch already exists (another standalone run today), use
a `-2` suffix. If the main checkout is already on a `code-review/run-*` branch, a
`code-review-run-waves` fan-out created it — use it and create nothing. Either way the
main checkout must be clean (`git status --short` empty) before you start.

Pick a wave from the list and view it:

```bash
backlog task view <waveTaskId> --plain
```

Extract the member task IDs from the `Dependencies:` line, e.g.:

```text
Dependencies: TASK-0120, TASK-0121, TASK-0122, TASK-0123, TASK-0127
```

Split on commas, trim whitespace.

**Claim the wave by creating its worktree.** Branch creation is the claim — it fails if
another runner already holds this wave:

```bash
git worktree add ../.wave-<waveTaskId> -b code-review/<waveTaskId>
```

If this fails with `fatal: a branch named 'code-review/<waveTaskId>' already exists`, the
wave is already claimed. Pick a different wave; if none remain, stop and report that the
wave is in flight elsewhere. Do **not** delete the branch to force the claim — see
Recovery in the [Worktree Protocol](references/worktree-protocol.md#recovery).

Only after the claim succeeds, flip the wave parent to `In Progress` (main checkout):

```bash
backlog task edit -s 'In Progress' <waveTaskId>
```

Also record the wave's branch on the task so a parked wave can be found later:

```bash
backlog task edit --append-notes 'Branch: code-review/<waveTaskId>' <waveTaskId>
```

## Step 3 — Execute member tasks sequentially

**Sequential, not parallel.** Members of the same wave often touch overlapping files;
serialising avoids conflicts within the wave and makes each build/test cycle attributable
to one change. (Parallelism happens *between* waves, via worktrees — not within one.)

For each member task ID, in the order they appear in `Dependencies:`:

1. Read the task and flip it to `In Progress` (main checkout):

   ```bash
   backlog task view <memberId> --plain
   backlog task edit -s 'In Progress' <memberId>
   ```

2. Before and while applying the fix, use **code-review-rust** as a guardrail: read
   applicable rule categories and the scan checklist in
   `skills/code-review-rust/references/rules.md` for the code you touch (errors, async,
   security, tests, NATS, etc.). Apply the fix described by the task **inside the wave
   worktree**. Respect repo conventions (`CLAUDE.md`) and the task's acceptance criteria.
   Keep the change minimal — no drive-by refactors.

3. Flip the task to `Done` only when the implementation satisfies the whole task,
   including all acceptance criteria and definition-of-done items. Use `--check-ac`
   / `--check-dod` where they map cleanly:

   ```bash
   backlog task edit -s 'Done' <memberId>
   ```

If a member task is infeasible, obsolete, deferred, only partially fixed, or has
leftover acceptance criteria, do **not** mark it `Done`. Append notes explaining the
state, leave it in `In Progress` when follow-up work remains in the current wave, or
move it back to `To Do` when it needs re-triage into a future dedicated wave. Flag it
as `✗` in the final report with the specific reason.

**Obsolete acceptance criteria.** If an AC is no longer literally satisfiable because
earlier work made the case it describes unrepresentable (e.g. it asks for a test
constructing a value that no longer compiles), that is not leftover work. Satisfy the
AC's intent with the closest still-meaningful check, record the substitution in the
task's notes, check the AC off, and close the task — mark it `~` in the report. Do not
carry it forward as a concern.

**Orphans created by your own fix.** When a fix leaves something dead — an error
variant with no remaining producer, a mock with no remaining user, a now-unreachable
branch — do not merely note it. Remove it in this wave if it is private to the crate
and the removal is mechanical; otherwise (public API, cross-crate blast radius) file a
`Triage` task per Step 6 before closing the member task.

## Step 4 — Pre-merge QA gate

Once every member task is either `Done` or explicitly left open with notes, run the QA
gate **inside the wave worktree**, so it sees this wave's changes and no other's:

```bash
cd ../.wave-<waveTaskId> && ops verify
```

This must pass cleanly. Fix root causes if it fails. Re-run until clean.

This gate authorises the merge attempt — it does not close the wave. A second, integration
run happens in Step 7 against the merged result.

## Step 5 — Commit the wave's code

After the pre-merge gate passes, invoke the **commit-script** skill from inside the wave
worktree, in `commit` mode and with a per-wave output path so concurrent waves cannot
overwrite each other:

```text
mode: commit
output path: commit-script-<waveTaskId>.sh
```

Pass the bare filename — commit-script places it inside the worktree's own git dir
(`git rev-parse --git-dir` resolves to `.git/worktrees/<name>` there), which is already
distinct per worktree, so concurrent waves cannot overwrite each other.

Never ask for `pr` mode here — this skill merges the wave branch itself in Step 7, onto
the landing branch, and the run's PR is opened from the integration branch in Step 8. A
per-wave PR would also break the fan-out, where one PR covers the whole run.

If the skill produces a script and there are changes to commit, run it from the worktree:

```bash
cd ../.wave-<waveTaskId> && bash "$(git rev-parse --git-dir)/commit-script-<waveTaskId>.sh"
```

Watch the output for warnings or errors (failed hooks, lint failures, rejected
commits, unstaged remnants). Fix the root cause of any warning/error reported,
re-stage, and re-run until the script completes cleanly. Do not bypass hooks
(`--no-verify`) or amend past commits to hide failures.

If there are no changes to commit, skip this step.

**Backlog files are not part of this commit.** Task-file changes live in the main
checkout (per the isolation rules), so the worktree contains only code and the wave branch
stays clean. Commit the backlog changes separately from the main checkout as a
`chore(backlog)` commit once the wave has landed.

## Step 6 — Discharge every open thread

Before merging, list — for yourself, not for the report — everything you would
otherwise have written under "leftover concerns": dead code your fixes orphaned,
follow-ups you decided were out of scope, adjacent problems you noticed, doubts about
your own bookkeeping. Then discharge each one:

- **In scope and bounded** → fix it now, in this wave, and let it ride the same QA gates.
- **Anything else** → file a `Triage` task (from the main checkout):

  ```bash
  backlog task create "<short title>" \
    -d "$(cat <<'EOF'
  **File**: `<path>:<line>`

  **What**: <what is wrong / what is left>

  **Why it matters**: <impact>

  **Origin**: discovered during <waveTaskId> while fixing <memberId>.
  EOF
  )" \
    -s "Triage" \
    -l "code-review-rust,<category>" \
    --priority <critical|high|medium|low> \
    --modified-file <path> \
    --ac "<acceptance criterion>" \
    --plain
  ```

  Pass one `--modified-file` per file the finding touches, repo-root-relative and without
  line numbers. Triage uses that field to compute wave file scope and merge order — a
  finding filed without it degrades the next wave's merge planning.

  Use a `"$(cat <<'EOF' … EOF)"` heredoc for multi-line values — not `$'…'` ANSI-C
  quoting. Run `backlog search "<keyword>" --plain` first and skip filing if an open
  task already covers it.

Filing is cheap and reversible; a concern that exists only in the final report is not
work anyone can pick up. Do not ask the user whether to file — file, then report what
you filed. The only things that may appear as bare prose in Step 9 are facts requiring
no action at all (e.g. "`ops verify` clean on first run").

## Step 7 — Merge the wave back, serialized

Only one wave may merge at a time. Acquire the merge lock, retrying until it is free:

```bash
mkdir .git/code-review-merge.lock
```

Holding the lock:

```bash
# 1. rebase the wave onto the landing branch, from the worktree
cd ../.wave-<waveTaskId> && git rebase <landing-branch>

# 2. integration verify — the merged result, not the isolated one
ops verify

# 3. fast-forward the landing branch, from the main checkout
git merge --ff-only code-review/<waveTaskId>
```

The **landing branch** is the `code-review/run-<date>` integration branch checked out in
the main checkout — created by `code-review-run-waves` for a fan-out, or by Step 2 for a
standalone run. Waves never land on `main` directly; the landing branch ships to `main`
as one PR (Step 8 here, or Step 5 of `code-review-run-waves`). Never switch the main
checkout to another branch while a wave is in flight — runners derive their rebase target
and merge destination from it.

Then release the lock — **always**, including on every failure path:

```bash
rmdir .git/code-review-merge.lock
```

If the rebase conflicts, resolve it in the worktree; you have both sides there. Never
resolve by discarding the other wave's hunk — that wave already merged and passed
integration verify, so overwriting it silently reverts completed work. If the resolution
is not obvious, `git rebase --abort` restores the branch untouched, and the wave parks
(Step 8).

If integration `ops verify` fails, fix it on the wave branch, re-verify, and retry. A
wave that passes pre-merge and fails integration is a normal outcome — it is exactly the
class of failure isolation cannot catch on its own.

If `git merge --ff-only` refuses, another wave landed while you held a stale rebase.
Re-run the rebase; do not fall back to a merge commit.

## Step 8 — Close out or park

**Landed.** If every member task is `Done` and the merge succeeded, close the wave and
tear down (main checkout):

```bash
backlog task edit -s 'Done' <waveTaskId>
git worktree remove ../.wave-<waveTaskId>
git branch -d code-review/<waveTaskId>
```

Then commit the backlog task-file changes as their own `chore(backlog)` commit on the
landing branch.

**Standalone runs only — open the run's PR.** A fan-out run does not do this;
`code-review-run-waves` opens one PR for all its waves after every runner has returned.
A standalone run owns the whole landing branch, so after the `chore(backlog)` commit:

```bash
git push -u origin code-review/run-<date>
gh pr create --base main --head code-review/run-<date> \
  --title "code-review run <date>: <waveTaskId>" \
  --body-file <report file>
```

The PR body carries the Step 9 report's substance (wave, member outcomes, verify
results, filed tasks). Do not merge the PR yourself unless the user asks — it is the
run's human review gate. After it merges (rebase merge preserves the conventional
commits): `git checkout main && git pull && git branch -d code-review/run-<date>`.

**Parked.** If any member task is not `Done`, or the merge did not land, leave the wave
parent non-done (`In Progress` or `To Do`, matching the remaining work) and append a note
listing the unfinished members and the reason the merge was not attempted or failed.
**Leave the worktree and branch in place** — that is what makes the work resumable.
Do not promise deferred PRs or future work in prose; remaining work goes into the backlog
as a `Triage` task (Step 6), which is the only sanctioned way to defer anything.

Never use `git worktree remove --force` or `git branch -D` to clear an obstacle. Both
refusals exist to stop you deleting unmerged work; investigate what is uncommitted
instead.

## Step 9 — Report

Print a concise summary:

- wave task ID that was picked and its title, and its branch name
- member task IDs, each marked ✓ (Done), ✗ (left open, with reason), or ~ (no-op / already satisfied, AC substituted, and therefore Done)
- pre-merge `ops verify` result and integration `ops verify` result, separately (pass/fail, and what was fixed if initial runs failed)
- commit-script outcome: script generated? ran cleanly? any warnings/errors fixed before it succeeded
- merge outcome: landed, or parked — and if parked, the branch and worktree path to resume from
- for a standalone run: the run PR's URL and branch; under a fan-out, note that
  `code-review-run-waves` opens the PR
- **discharged threads**: for each item from Step 6, one line — either "fixed in-wave: …"
  or "filed TASK-XXXX (Triage): …". If nothing came up, say "none". Never restate an
  item here as an unresolved concern or a question to the user; if you are writing
  "worth triaging", "if you'd rather…", or "someone should", go back to Step 6 and
  discharge it first.
- whether any member needed significant `code-review-rust` rule consultation (guardrail);
  keep this brief — not a full audit

## Concurrency

Several waves can run at once, each in its own worktree, coordinated by the rules above.
`code-review-run-waves` automates that fan-out.

Safe to run concurrently with a wave:

- other waves, each holding its own claim branch and worktree
- `code-review-rust` / `code-review-web` reviews (read-only on code; each finding is its
  own task file)

Not safe:

- two runners on the same wave — prevented by the claim branch
- `code-review-triage` while waves are running; it mutates task status in bulk and would
  race with member status flips. Run triage to completion first
- editing source in the main checkout while any wave is claimed
- two waves merging at once — prevented by the merge lock

See [Worktree Protocol](references/worktree-protocol.md) for the invariants and recovery
procedures.

## References

- [Worktree Protocol](references/worktree-protocol.md) — naming, claiming, the merge lock, two-stage verification, and recovery procedures
