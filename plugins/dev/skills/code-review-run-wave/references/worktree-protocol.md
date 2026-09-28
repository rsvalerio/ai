# Worktree Protocol

Mechanics for running code-review waves in parallel without corrupting each other.
`code-review-run-wave` and `code-review-run-waves` both follow this protocol; it is the
single source of truth for worktree naming, claiming, merging, and recovery.

## Why Isolation Is Required

Waves are grouped semantically, not spatially. Two of the grouping axes in
`code-review-triage` are *by concern* (`error handling`, `test coverage`, a shared root
cause), so two waves routinely touch the same files. Running them in one checkout breaks
in four ways:

| Shared resource | Failure when two waves run in one checkout |
|---|---|
| Working tree | `ops verify` builds the other wave's half-finished edits; failures are attributed to the wrong wave |
| Git index | Interleaved `git add` / `git commit` produce commits containing the other wave's files |
| Commit script path | Both runs write the same file and overwrite each other |
| Wave selection | Two runners pick the same wave and apply every fix twice |
| Backlog task files | Every wave edits them in the *same* main checkout, so a blanket `git add .backlog` commits the others' in-flight edits |

A worktree per wave gives each wave its own working tree, its own index, and its own
pre-merge build. Merges are then serialized so only one wave mutates the landing branch
at a time.

## Naming

| Thing | Pattern | Example |
|---|---|---|
| Wave branch | `code-review/<waveTaskId>` | `code-review/TASK-0119` |
| Landing branch | `code-review/run-<YYYYMMDD>`, checked out in the main checkout — created by `code-review-run-waves` for a fan-out, or by the standalone runner itself | `code-review/run-20260819` |
| Worktree path | `../.wave-<waveTaskId>` (sibling of the repo, not inside it) | `../.wave-TASK-0119` |
| Commit script | `<git-dir>/commit-script-<waveTaskId>.sh` (the worktree's own git dir) | `.git/worktrees/.wave-TASK-0119/commit-script-TASK-0119.sh` |
| Merge lock | `ops lock code-review-merge` | — |
| Backlog lock | `ops lock code-review-backlog` | — |

Both locks are `ops lock` named locks. They are stored under the common git dir, so
every worktree of the repository shares them. They are kernel `flock` locks: a runner
that dies, even by `SIGKILL`, releases its lock with it, so no lock can outlive its
holder. `ops lock status` shows each holder's PID, worktree, command, age and
whether it is still alive.

**Requires ops 0.72.0 or newer.** Check `ops --version` before claiming anything.

The worktree must be a **sibling** of the repository, never a subdirectory of it.
A worktree nested inside the main checkout shows up as untracked files there and gets
swept into commits.

## Claiming a Wave

Creating the wave branch **is** the claim, and `ops backlog wave claim` does it in one
step, from the main checkout:

```bash
ops backlog wave claim <waveTaskId>
```

It creates `code-review/<waveTaskId>` and the worktree `../.wave-<waveTaskId>`
(`git worktree add -b`), then flips the wave to `In Progress` and records
`Branch:` and `Worktree:` notes on it. If the branch already exists, it refuses
and changes nothing. If the status edit fails after the worktree exists, it
removes the worktree and branch again (unforced), so a failed claim never
leaves a task marked in progress by a run that never started.

Treat a refusal because the branch exists as **"this wave is already claimed"**:
do not delete the branch to force the claim. Pick a different wave, or if no
other wave is open, stop and report that the wave is in flight elsewhere. See
[Recovery](#recovery) for genuinely abandoned claims.

## The Main-Checkout Rule

**Code edits happen in the worktree. Every `ops backlog` command runs from the main
checkout.**

`ops backlog` stores tasks as files inside the repository. A worktree holds a *separate copy*
of those files, so task-status edits made from a worktree would ride the wave branch and
collide with every other wave's task edits on merge.

| Action | Where it runs |
|---|---|
| `ops backlog task view` / `edit` / `create` / `list` / `search`, `ops backlog wave …` | main checkout |
| Reading and editing source files | wave worktree |
| `ops verify` (pre-merge) | wave worktree |
| `commit-script` and the generated script | wave worktree |
| `ops verify` (integration), merge, `chore(backlog)` commit | main checkout |

The useful side effect: the wave branch contains only code, and backlog task files are
committed separately from the main checkout. Code commits and bookkeeping commits can no
longer end up mixed in one blob.

### Task files are shared mutable state

The rule above is what keeps *code* isolated. It does the opposite for task files: it
routes every concurrent wave's `ops backlog task edit` into the one main checkout, so at any
moment its `.backlog/tasks/` holds a mix of edits belonging to every wave in flight.

Run literally, `git add .backlog` therefore stages all of them. Nothing is lost — the file
contents are exactly what each wave wrote — but three things go wrong:

- the bookkeeping commit no longer describes the wave whose message it carries
- git attributes another wave's task edits to the wrong wave, permanently
- the wave that *owned* those edits later finds nothing to commit and silently skips its
  own bookkeeping commit

**Stage bookkeeping by task, never by directory.** A wave knows exactly which task files
are its own: its parent, its members, and any `Triage` task it filed. Name those task ids
to `ops backlog commit`, which resolves each id to its file:

```bash
ops lock code-review-backlog --timeout 600 -- \
  ops backlog commit <waveTaskId> <memberId>... <filedTriageId>... \
    -m "chore(backlog): close code-review wave <N>"
```

`ops backlog commit` does the three things the bookkeeping step exists for:

- **It refuses when any other path is staged**, before touching anything. A foreign
  staged path is another writer's work. Abort and report; do not unstage the extras
  and retry.
- **It commits only the listed tasks' files that actually changed.** A member task file
  the wave left unchanged contributes nothing. It uses `git commit --only`, so it never
  takes another wave's staged files.
- **It refuses to make an empty commit.** If none of the tasks changed, it exits non-zero
  and commits nothing. That means this wave edited no task files of its own. Check that
  against what the wave actually did, and say so in the report rather than committing
  nothing in silence.

The backlog lock around it keeps two waves' bookkeeping from interleaving in the one
shared index: without it, another wave's staged files can make this commit refuse. The
lock is held only for that one command, never across the member-fix phase. It is a
distinct lock from the merge lock, and no runner holds both at once: bookkeeping happens
after the wave has landed.

Other waves' modified task files are left unstaged in the working tree on purpose. They
are not yours to commit, and their own runners will.

## Merging

Merges are serialized through the `code-review-merge` lock. Land the wave as one
command, run from the main checkout, that holds the lock for exactly rebase →
integration verify → fast-forward:

```bash
ops lock code-review-merge --timeout 3600 -- bash -c '
  set -e
  # 1. rebase the wave branch onto the landing branch, in the worktree.
  #    A conflict aborts the rebase and exits 3; resolve it outside the lock.
  git -C ../.wave-<waveTaskId> rebase <landing-branch> \
    || { git -C ../.wave-<waveTaskId> rebase --abort; exit 3; }
  # 2. integration verify: the merged result, not the isolated result
  (cd ../.wave-<waveTaskId> && ops verify)
  # 3. fast-forward the landing branch, in the main checkout
  git merge --ff-only code-review/<waveTaskId>
'
```

`ops lock` releases the lock when the command exits, on success, on failure and on a
signal alike. There is nothing to release by hand. It passes the command's exit code
through unchanged. A non-zero exit means nothing landed:

| Exit | Meaning | What to do, outside the lock |
|------|---------|------------------------------|
| 3 | The rebase conflicted and was aborted | [Handling a Rebase Conflict](#handling-a-rebase-conflict), then run the locked command again |
| other, during `ops verify` | Integration verify failed | Fix it on the wave branch, rerun pre-merge `ops verify`, then run the locked command again |
| other, from `git merge --ff-only` | The landing branch moved under you | Run the locked command again: its rebase picks up the new base |
| 1, with `ops: error: timed out after …s waiting for lock code-review-merge, held by pid …` | Another wave held the lock for the whole `--timeout`. The command never ran | `ops lock status`. A live holder is a merge in progress, so wait and retry. A dead one reports stale: `ops lock break code-review-merge`, then retry |

Doing the fixing *outside* the lock is deliberate: a runner thinking through a
conflict or a failing test would otherwise block every other wave's merge.

The **landing branch** is the `code-review/run-<YYYYMMDD>` integration branch checked
out in the main checkout — created by `code-review-run-waves` for a fan-out, or by a
standalone `code-review-run-wave` run before it claims its wave. Waves never land on
`main` directly; the landing branch ships to `main` as one PR, opened by whichever
skill owns the run once all its waves have landed. Never switch the main checkout away
from the landing branch while waves are in flight — every runner derives its rebase
target and merge destination from it.

`--ff-only` is deliberate. After a successful rebase the merge must be a fast-forward;
if git refuses, the landing branch moved under you. Re-run the locked command rather than
falling back to a merge commit.

### Two Verifies, Two Different Jobs

- **Pre-merge `ops verify`** runs in the worktree on the wave's changes alone. It proves
  the wave is internally correct and gates the merge attempt.
- **Integration `ops verify`** runs after the rebase, on the wave's changes combined with
  everything already on the base branch. It catches the failures isolation cannot:
  a wave that renames a function another wave started calling, two waves adding the same
  helper, a trait impl that only conflicts once both halves are present.

A wave that passes pre-merge and fails integration is a normal outcome, not a bug in the
protocol. Fix it on the wave branch, re-verify, retry the merge.

## Handling a Rebase Conflict

Expected whenever two waves touched the same file. The conflict surfaces as:

```text
CONFLICT (content): Merge conflict in <path>
error: could not apply <sha>... <subject>
```

The locked merge command has already aborted that rebase and released the lock. Redo
the rebase in the worktree, outside the lock, and resolve it there: you have both
sides and the wave's full context.

```bash
cd ../.wave-<waveTaskId> && git rebase <landing-branch>   # resolve, git add, git rebase --continue
ops verify                                                 # pre-merge verify on the resolved branch
```

Then run the locked merge command again. Its rebase is a no-op unless another wave
landed in the meantime. If the resolution is not obvious, `git rebase --abort` restores
the branch exactly as it was, and the wave's commits are not lost. Then either retry
after the conflicting wave settles, or park the wave (below) and report it.

Do not resolve a conflict by discarding the other wave's hunk. The other wave already
merged and passed integration verify; overwriting it silently reverts completed work.

## Teardown

Only after the merge has landed:

```bash
git worktree remove ../.wave-<waveTaskId>
git branch -d code-review/<waveTaskId>
```

`git worktree remove` refuses when the worktree has modified or untracked files:

```text
fatal: '../.wave-<id>' contains modified or untracked files, use --force to delete it
```

That refusal is a feature — it is the protocol's last guard against deleting unmerged
work. **Never reach for `--force` to get past it.** Investigate what is uncommitted
first; it is usually a fix that was applied but never committed. Likewise `git branch -d`
(lowercase) refuses to delete an unmerged branch, where `-D` would discard it silently.

A wave that did not merge keeps its worktree and branch on purpose. Leaving it in place is
what makes the work resumable. The landing branch also outlives the run: it stays until
its PR merges. This repo squashes PRs to `main`, so the squash commit shares no ancestry
with the landing branch — `git branch -d` will refuse, and `-D` is correct there because
the merged PR is the proof the work landed (`git checkout main && git pull && git branch
-D <landing-branch>`). The `-D` ban in the invariants covers branches that might carry
unmerged work, not a landing branch whose PR has merged.

## Opening the Run PR (standalone runs only)

A fan-out run never does this: `code-review-run-waves` opens one PR covering all its
waves once every runner has returned. A standalone run owns the whole landing branch, so
it publishes its own.

After the `chore(backlog)` commit, write the report's substance — wave, member outcomes,
both `ops verify` results, filed `Triage` tasks — to a body file first, then push and PR
the **recorded landing branch**, the exact name resolved when the run started:

```bash
git push -u origin <landing-branch>
gh pr create --base main --head <landing-branch> \
  --title "code-review run: <waveTaskId>" \
  --body-file <report file>
```

Append the PR URL to the report once it is open. Do not merge the PR yourself unless the
user asks — it is the run's human review gate. Cleaning up the landing branch after its
PR merges is the one sanctioned `-D`; see [Teardown](#teardown).

## Recovery

**Parking a wave.** When the merge did not land or members remain open, record it from
the main checkout:

```bash
ops backlog wave park <waveTaskId> --reason "<why: unfinished members, or the failed step>" \
  [-s 'To Do']   # default status: In Progress
```

It sets the status, appends `Parked: <reason>` with the branch and worktree to resume
from, and touches nothing in git.

**A parked wave (merge failed, worktree still present).** The branch holds the committed
fixes and the worktree holds any uncommitted remainder. Resume by re-entering the
worktree, finishing the work, and running the locked merge command again. Nothing needs
to be recreated.

**A stale worktree whose directory was deleted manually.** Git still lists it. Clear the
bookkeeping, then re-claim normally:

```bash
git worktree prune
```

**An abandoned claim branch (no worktree, no runner).** Confirm all three before touching
it: `git worktree list` does not show it, the wave task is not `In Progress` under an
active run, and the branch has no commits you need (`git log <landing-branch>..code-review/<id>`).
Only then delete the branch to release the claim. If the branch *does* carry commits, it
is parked work, not an abandoned claim — resume it instead.

**A lock that seems stuck.** It cannot outlive its holder: `ops lock` is a kernel
`flock`, so a killed runner releases it. `ops lock status` names the holder:

- **Alive**: a merge or bookkeeping commit is genuinely running. Wait.
- **Stale** (dead holder): only the record remains. `ops lock break <name>` clears
  it. It refuses while the holder is alive, so it cannot break a live merge.

A killed runner can still leave its worktree mid-rebase. Before retrying that wave,
check `git status` in its worktree, and finish or `git rebase --abort` there.

**A wave whose branch no longer rebases cleanly after repeated attempts.** Stop retrying.
Leave it parked, file a `Triage` task describing the conflict and which wave it collides
with, and report it. A wave that fights the base branch usually means the grouping put
genuinely coupled work in two different waves — that is triage feedback, not a merge
problem to brute-force.

## Invariants

1. One wave, one branch, one worktree. Never two runners on one wave.
2. Claim before mutating any task state.
3. All `ops backlog` commands from the main checkout; all code edits in the worktree.
4. The merge lock is held across rebase → integration verify → merge, as one
   `ops lock` command, and nothing else. Conflicts and failures are fixed outside it.
5. A wave closes `Done` only when every member is `Done` **and** the merge landed.
6. Never `--force` a worktree removal or `-D` a wave branch to clear an obstacle.
7. A failed wave never blocks another wave — it parks and the others carry on.
