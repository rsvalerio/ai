---
name: code-review-run-wave
description: Pick one code-review wave, run it in an isolated git worktree, apply every member fix, run QA, merge it back, and close only fully completed waves
allowed-tools: Read Edit Write Grep Glob Bash(git status:*) Bash(git log:*) Bash(git diff:*) Bash(git rev-parse:*) Bash(git checkout:*) Bash(git branch:*) Bash(git worktree:*) Bash(git rebase:*) Bash(git merge:*) Bash(git add:*) Bash(git commit:*) Bash(git push:*) Bash(git pull:*) Bash(gh pr:*) Bash(ops --version) Bash(ops verify) Bash(ops backlog:*) Bash(ops lock:*) Bash(bash *commit-script-*.sh)
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

Member fixes **must** follow **code-review-rust** in **implementation guardrail** mode
(**code-review-web** / **code-review-lovable** for frontend) — without it a wave clears old findings and creates new
ones, repeating triage and review.

**Read only the rule files the wave needs.** Members are titled `<RULE-ID>: <Title>`, so
the wave names its own categories: read `references/rules/<PREFIX>.md` per distinct prefix,
usually one or two files. Never the scan checklist or `rules/index.md` — those find rules
from raw code, and a wave starts from IDs. Every runner pays this read, once per wave.

Unless the user explicitly asked for a formal review during this wave, do **not** create
new backlog tasks for issues you notice while fixing: treat `code-review-rust` rules as
acceptance criteria for the change itself, not as a trigger to file new tasks (see
guardrail mode in that skill).

### Isolation rules

These three are not optional — violating any one corrupts a concurrently running wave:

1. **Code edits happen in the wave worktree.** Never edit source files in the main
   checkout while a wave is claimed.
2. **Every `ops backlog` command runs from the main checkout.** Task files live inside the
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

Requires `ops` 0.74.0 or newer: the claim, the locks and the bookkeeping commit
are `ops` commands. Check `ops --version` first, and stop with a clear message if
it is older.

From the main checkout:

```bash
ops backlog wave list -s 'To Do' --plain
```

If the list is empty, stop and report "no open waves".

## Step 2 — Prepare the landing branch and claim one wave

**Standalone runs only:** before touching any branch, confirm the main checkout is
clean (`git status --short` empty) — uncommitted changes ride `git checkout` onto the
landing branch — and that it is on `main` or a `code-review/run-*` branch. On any
other branch, stop and report: creating the run branch there would build the run on
the wrong history.

- **On `main`:** if `code-review/run-$(date +%Y%m%d)` does not exist, create it — the
  wave lands on it and it ships to `main` as one PR (Step 8):

  ```bash
  git checkout -b code-review/run-$(date +%Y%m%d) main
  ```

  If it does exist, resolve its run state (below) and follow it.
- **On a `code-review/run-*` branch:** either a `code-review-run-waves` fan-out just
  created it (you are one of its runners) or a previous run left it behind. Resolve
  its run state (below) and follow it.

**A run branch's state** is decided by its PR, never by commit ancestry — under this
repo's squash merges a merged run branch stays outside `main`'s ancestry forever, so
`git log main..…` would flag it as resumable even after it fully landed:

```bash
gh pr view <branch> --json state --jq .state 2>/dev/null || echo NONE
```

- `OPEN` or `NONE` — an active or never-published run (a fan-out's fresh branch is
  `NONE`): use it — resume where relevant.
- `MERGED` — a completed run whose cleanup was skipped: delete it
  (`git branch -D <branch>` — the PR state is the proof it landed) and create a fresh
  branch for this run.
- `CLOSED` — closed without merging: stop and report; re-pushing the branch or
  re-running its waves is the user's call, not this skill's.

Record the exact branch name chosen; Step 8 pushes and PRs it.

Pick a wave from the list, read it, and enumerate its members:

```bash
ops backlog task view <waveTaskId> --plain
ops backlog wave members <waveTaskId> --plain
```

`wave members` prints the same row shape as `task list`, one member per line:

```text
To Do:
  [HIGH] TASK-0120 - ERR-5: unwrap in the request handler
  [MEDIUM] TASK-0121 - ERR-8: error loses the path
```

Take the task IDs from those rows. Do **not** try to read members out of
`task view` output — it renders no dependency block. A trailing
`Missing dependencies: <ids>` line means the wave names tasks that are no longer in
`tasks/`; note them in the final report and carry on with the rest.

**Claim the wave** (main checkout). One command creates the branch
`code-review/<waveTaskId>` and the worktree `../.wave-<waveTaskId>`, flips the wave
to `In Progress`, and records the branch and worktree on the task, so a parked wave
can be found later:

```bash
ops backlog wave claim <waveTaskId>
```

If the branch already exists, it refuses with nothing changed: the wave is already
claimed. Pick another, and never delete the branch to force the claim. Full rules,
including genuinely abandoned claims:
[Claiming a Wave](references/worktree-protocol.md#claiming-a-wave).

## Step 3 — Execute member tasks sequentially

**Sequential, not parallel.** Members of the same wave often touch overlapping files;
serialising avoids conflicts within the wave and makes each build/test cycle attributable
to one change. (Parallelism happens *between* waves, via worktrees — not within one.)

For each member task ID, in the order `wave members` returned them:

1. Read the task and flip it to `In Progress` (main checkout):

   ```bash
   ops backlog task view <memberId> --plain
   ops backlog task edit -s 'In Progress' <memberId>
   ```

2. Before and while applying the fix, apply the guardrail skill for the member's own
   domain: the skill holding `references/rules/<PREFIX>.md` — `ERR-5` → code-review-rust,
   `REACT-3` → code-review-web, `RLS-2` → code-review-lovable. Read once per category, nothing else (see Hard
   requirements). Apply the fix **inside the wave worktree**. Respect repo conventions
   (`CLAUDE.md`) and the task's acceptance criteria. Keep the change minimal — no
   drive-by refactors.

3. Flip the task to `Done` only when the implementation satisfies the whole task,
   including all acceptance criteria and definition-of-done items — and tick every
   one of them in the same call, so the closed task records what was satisfied:

   ```bash
   ops backlog task edit -s 'Done' \
     --check-ac <n> [--check-ac <n> ...] \
     [--check-dod <n> ...] \
     <memberId>
   ```

   The indexes are 1-based positions in *this* task's own lists, as
   `ops backlog task view <memberId> --plain` printed them — repeat the flag once per
   item, and pass `--check-dod` only for a task that has a Definition of Done section.
   Do not carry indexes over from another task: an index past the end of the list
   fails the whole call (`no acceptance criterion #3`). A task with an item left
   unchecked is not `Done` — see below.

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
`chore(backlog)` commit once the wave has landed — staged **by path**, never as
`git add .backlog`, because concurrent waves share that directory, and with stage,
verify, and commit held under the backlog lock, because they also share one index. See
[Task files are shared mutable state](references/worktree-protocol.md#task-files-are-shared-mutable-state)
and Step 8.

## Step 6 — Discharge every open thread

Before merging, list — for yourself, not for the report — everything you would
otherwise have written under "leftover concerns": dead code your fixes orphaned,
follow-ups you decided were out of scope, adjacent problems you noticed, doubts about
your own bookkeeping. Then discharge each one:

- **In scope and bounded** → fix it now, in this wave, and let it ride the same QA gates.
- **Anything else** → file a `Triage` task (from the main checkout):

  ```bash
  ops backlog task create "<short title>" \
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
  quoting. Run `ops backlog search "<keyword>" --plain` first and skip filing if an open
  task already covers it.

Filing is cheap and reversible; a concern that exists only in the final report is not
work anyone can pick up. Do not ask the user whether to file — file, then report what
you filed. The only things that may appear as bare prose in Step 9 are facts requiring
no action at all (e.g. "`ops verify` clean on first run").

## Step 7 — Merge the wave back, serialized

Only one wave may merge at a time. From the main checkout, land the wave as one command
that holds the merge lock for exactly rebase → integration verify → fast-forward:

```bash
ops lock code-review-merge --timeout 3600 -- bash -c '
  set -e
  git -C ../.wave-<waveTaskId> rebase <landing-branch> \
    || { git -C ../.wave-<waveTaskId> rebase --abort; exit 3; }
  (cd ../.wave-<waveTaskId> && ops verify)   # integration verify: the merged result
  git merge --ff-only code-review/<waveTaskId>
'
```

The **landing branch** is the one recorded in Step 2. Waves never land on `main` directly;
it ships to `main` as one PR (Step 8 here, or Step 5 of `code-review-run-waves`). Never
switch the main checkout to another branch while a wave is in flight — runners derive
their rebase target and merge destination from it.

`ops lock` releases the lock when the command exits, whatever the outcome, and passes the
exit code through. On a non-zero exit nothing landed. Fix it **outside** the lock, so no
other wave waits on your thinking, then run the locked command again:

- **Exit 3**: the rebase conflicted and was aborted. Resolve it in the worktree per
  [Handling a Rebase Conflict](references/worktree-protocol.md#handling-a-rebase-conflict).
  Never resolve by discarding the other wave's hunk.
- **Integration `ops verify` failed**: fix it in the worktree, rerun pre-merge
  `ops verify`, and **commit** the fix on the wave branch (Step 5): the locked command
  rebases, and a rebase refuses a dirty worktree. This is a normal outcome.
- **`--ff-only` refused**: another wave landed first; never fall back to a merge commit.
- **`timed out … waiting for lock`**: `ops lock status`; wait for a live holder,
  `ops lock break code-review-merge` a stale one.

## Step 8 — Close out or park

**Landed.** If every member task is `Done` and the merge succeeded, close the wave and
tear down (main checkout):

```bash
ops backlog task edit -s 'Done' <waveTaskId>
git worktree remove ../.wave-<waveTaskId>
git branch -d code-review/<waveTaskId>
```

Then commit the backlog task-file changes as their own `chore(backlog)` commit on the
landing branch, **naming only this wave's own tasks, under the backlog lock**:

```bash
ops lock code-review-backlog --timeout 600 -- \
  ops backlog commit <waveTaskId> <memberId>... <filedTriageId>... \
    -m "chore(backlog): close code-review wave <N>"
```

It commits only the listed tasks' changed files, and refuses an empty commit or any
other staged path. Never `git add .backlog`: concurrent waves' task edits share this
checkout. On a foreign staged path, abort and report; never unstage and retry. See
[Task files are shared mutable state](references/worktree-protocol.md#task-files-are-shared-mutable-state).

**Standalone runs only — open the run's PR.** A fan-out run does not: `code-review-run-waves`
PRs all its waves once every runner returns. Procedure (report body file, push, `gh pr
create` on the landing branch recorded in Step 2, and the one sanctioned `-D` afterwards):
[Opening the Run PR](references/worktree-protocol.md#opening-the-run-pr-standalone-runs-only).

**Parked.** If any member task is not `Done`, or the merge did not land, park the wave
(main checkout), naming the unfinished members and why the merge was not attempted or
failed:

```bash
ops backlog wave park <waveTaskId> --reason "<unfinished members; the failed step>" \
  [-s 'To Do']   # default In Progress; match the remaining work
```

It records the reason and the branch and worktree to resume from, and touches nothing in
git. **The worktree and branch stay in place**, which is what makes the work resumable.
Commit it with the same locked `ops backlog commit` as a landed wave
(`chore(backlog): park code-review wave <N>`), or the next run's clean-tree preflight
blocks.
Deferred work goes into the backlog as a `Triage` task (Step 6), never into prose.

Never `git worktree remove --force` or `git branch -D` to clear an obstacle: both
refusals guard unmerged work. Investigate what is uncommitted instead.

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
