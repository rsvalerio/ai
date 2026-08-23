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
| Merge lock | `.git/code-review-merge.lock` (a directory) | — |

The worktree must be a **sibling** of the repository, never a subdirectory of it.
A worktree nested inside the main checkout shows up as untracked files there and gets
swept into commits.

## Claiming a Wave

Creating the wave branch **is** the claim. `git worktree add -b` fails if the branch
already exists, so the claim is exclusive without a separate lock file:

```bash
git worktree add ../.wave-<waveTaskId> -b code-review/<waveTaskId>
```

A second runner attempting the same wave gets:

```text
fatal: a branch named 'code-review/<waveTaskId>' already exists
```

Treat that as **"this wave is already claimed"** — do not delete the branch to force the
claim. Pick a different wave, or if no other wave is open, stop and report that the wave
is in flight elsewhere. See [Recovery](#recovery) for genuinely abandoned claims.

Only after the claim succeeds, flip the wave parent to `In Progress`. Claiming first
means a failed claim never leaves a task marked in progress by a run that never started.

## The Main-Checkout Rule

**Code edits happen in the worktree. Every `backlog` command runs from the main
checkout.**

`backlog` stores tasks as files inside the repository. A worktree holds a *separate copy*
of those files, so task-status edits made from a worktree would ride the wave branch and
collide with every other wave's task edits on merge.

| Action | Where it runs |
|---|---|
| `backlog task view` / `edit` / `create` / `list` / `search` | main checkout |
| Reading and editing source files | wave worktree |
| `ops verify` (pre-merge) | wave worktree |
| `commit-script` and the generated script | wave worktree |
| `ops verify` (integration), merge, `chore(backlog)` commit | main checkout |

The useful side effect: the wave branch contains only code, and backlog task files are
committed separately from the main checkout. Code commits and bookkeeping commits can no
longer end up mixed in one blob.

### Task files are shared mutable state

The rule above is what keeps *code* isolated. It does the opposite for task files: it
routes every concurrent wave's `backlog task edit` into the one main checkout, so at any
moment its `.backlog/tasks/` holds a mix of edits belonging to every wave in flight.

Run literally, `git add .backlog` therefore stages all of them. Nothing is lost — the file
contents are exactly what each wave wrote — but three things go wrong:

- the bookkeeping commit no longer describes the wave whose message it carries
- git attributes another wave's task edits to the wrong wave, permanently
- the wave that *owned* those edits later finds nothing to commit and silently skips its
  own bookkeeping commit

**Stage bookkeeping by path, never by directory.** A wave knows exactly which task files
are its own: its parent, its members, and any `Triage` task it filed. Ask `backlog` where
each one lives rather than reconstructing the filename — the first line of `task view` is
the path:

```bash
for id in <waveTaskId> <memberId>... <filedTriageId>...; do
  git add "$(backlog task view "$id" --plain | sed -n '1s/^File: //p')"
done

# Nothing but this wave's files may be staged. If anything else is listed,
# unstage it — it belongs to a wave that is still running.
git diff --cached --name-only
git commit -m "chore(backlog): close code-review wave <N>"
```

An empty staged set here is a symptom, not a no-op: this wave edited its own task files,
so if none are staged, another runner has already swept them into its commit. Say so in
the report rather than skipping the commit in silence.

Other waves' modified task files are left unstaged in the working tree on purpose. They
are not yours to commit, and their own runners will.

## Merging

Merges are serialized through a lock directory. `mkdir` is atomic on POSIX filesystems,
so it either creates the directory or fails — there is no race window:

```bash
# acquire (retry in a loop; do not proceed without it)
mkdir .git/code-review-merge.lock

# release, always, including on failure
rmdir .git/code-review-merge.lock
```

Holding the lock, land the wave:

```bash
# 1. rebase the wave branch onto the landing branch, from the worktree
cd ../.wave-<waveTaskId> && git rebase <landing-branch>

# 2. integration verify: the merged result, not the isolated result
ops verify

# 3. fast-forward the landing branch, from the main checkout
git merge --ff-only code-review/<waveTaskId>
```

The **landing branch** is the `code-review/run-<YYYYMMDD>` integration branch checked
out in the main checkout — created by `code-review-run-waves` for a fan-out, or by a
standalone `code-review-run-wave` run before it claims its wave. Waves never land on
`main` directly; the landing branch ships to `main` as one PR, opened by whichever
skill owns the run once all its waves have landed. Never switch the main checkout away
from the landing branch while waves are in flight — every runner derives its rebase
target and merge destination from it.

`--ff-only` is deliberate. After a successful rebase the merge must be a fast-forward;
if git refuses, the landing branch moved under you — another wave merged while you held
a stale rebase. Re-run the rebase rather than falling back to a merge commit.

Release the lock as soon as the fast-forward completes or the attempt fails. Never hold
it across the member-fix phase — only across rebase → integration verify → merge.

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

Resolve it in the worktree — you have both sides and the wave's full context. If the
resolution is not obvious, `git rebase --abort` restores the branch exactly as it was;
the wave's commits are not lost. Then either retry after the conflicting wave settles, or
leave the wave parked (below) and report it.

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

## Recovery

**A parked wave (merge failed, worktree still present).** The branch holds the committed
fixes and the worktree holds any uncommitted remainder. Resume by re-entering the
worktree, finishing the work, and retrying rebase → integration verify → merge. Nothing
needs to be recreated.

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

**A stuck merge lock.** The lock is a plain directory, so a killed runner leaves it
behind. Verify no wave is mid-merge (`git worktree list`, plus `git status` in each
worktree showing no rebase in progress), then `rmdir .git/code-review-merge.lock`.

**A wave whose branch no longer rebases cleanly after repeated attempts.** Stop retrying.
Leave it parked, file a `Triage` task describing the conflict and which wave it collides
with, and report it. A wave that fights the base branch usually means the grouping put
genuinely coupled work in two different waves — that is triage feedback, not a merge
problem to brute-force.

## Invariants

1. One wave, one branch, one worktree. Never two runners on one wave.
2. Claim before mutating any task state.
3. All `backlog` commands from the main checkout; all code edits in the worktree.
4. The merge lock is held across rebase → integration verify → merge, and nothing else.
5. A wave closes `Done` only when every member is `Done` **and** the merge landed.
6. Never `--force` a worktree removal or `-D` a wave branch to clear an obstacle.
7. A failed wave never blocks another wave — it parks and the others carry on.
