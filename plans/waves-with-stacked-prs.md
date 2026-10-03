# Waves With Stacked PRs

Plan for a `stacked` delivery mode in `code-review-run-waves`: one wave, one pull
request, linked as a native GitHub Stack through the `gh stack` CLI extension.

Status: proposal, nothing implemented. Written 2026-10-03 against `gh` 2.102.0,
`gh-stack` v0.2.0 and ops 0.77.0.

## Target behaviour

```bash
claude -p "/code-review-run-waves"           # today: one run branch, one PR
claude -p "/code-review-run-waves stacked"   # new: one PR per wave, one Stack
```

In `stacked` mode a run of three waves ends like this, and GitHub's web UI shows the
three PRs as one Stack with its navigator on each PR:

```text
code-review/TASK-0131 → PR #43 (base: code-review/TASK-0125) ← top
code-review/TASK-0125 → PR #42 (base: code-review/TASK-0119)
code-review/TASK-0119 → PR #41 (base: main)                  ← bottom
─────────────
main (trunk)
```

- One wave is one layer and one PR. A reviewer sees that wave's diff alone.
- Layer order is the order the waves **actually landed**, not the planned order.
- A parked wave is not in the stack. It keeps its branch and worktree, as today.
- Merging stays the human gate. `gh stack merge` lands the layers bottom-up; under this
  repo's squash-only setting `main` gets one commit per wave instead of one per run.
- The default mode is unchanged. Nothing in this plan alters a run without `stacked`.

## Why it fits the existing protocol

The merge step already builds a stack and then throws it away. Under the merge lock a
wave rebases onto the landing branch, verifies, and fast-forwards the landing branch to
its own tip. So at the moment a wave lands, its branch is exactly "the previous landed
wave's tip plus this wave's commits". The chain of wave branches, in landing order, is
a valid linear stack by construction.

Today the runner deletes the wave branch right after landing. Stacked mode keeps it,
and that is most of the change:

| Step | Default mode | Stacked mode |
|------|--------------|--------------|
| Fan-out, worktrees, claim, member fixes, pre-merge verify | unchanged | unchanged |
| Locked merge (rebase → integration verify → fast-forward) | unchanged | same, plus bookkeeping inside the lock (below) |
| Teardown of a landed wave | remove worktree, delete branch | remove worktree, **keep branch** |
| Publish | push run branch, `gh pr create` | push the wave branches, `gh pr create` per layer, `gh stack link` |
| After merge | `git branch -D <run-branch>` | `gh stack sync --prune`, then drop the run branch |

Parallel execution, the 4-wave cap, the merge lock, both verifies, parking and the
"No leftovers" contract carry over untouched.

## Design

### 1. Mode selection

- `code-review-run-waves` takes an optional argument: `stacked`. Absent means the
  current single-PR delivery.
- The fan-out passes the mode to every runner. `code-review-run-wave` accepts the same
  argument, because its merge and teardown steps are the ones that differ. A standalone
  `/code-review-run-wave stacked` appends one layer to the run's stack.
- The mode is recorded on the run branch when Step 0 creates it, so a resumed run
  cannot switch delivery halfway:

  ```bash
  git config branch.<run-branch>.codeReviewDelivery stacked
  ```

  A resume whose argument disagrees with the recorded mode stops and reports.

### 2. The run branch becomes a landing pointer

The main checkout must have some branch checked out: runners derive their rebase target
from it and `ops backlog` commits land on it. A wave branch cannot serve, since it is
checked out in a worktree. So `code-review/run-<date>` stays, with a narrower job:

- It is still the landing branch in the locked merge. No change to that command's
  rebase target or `--ff-only` destination.
- It is not pushed when its tip equals the top wave branch, which is the normal case.
- If it carries commits beyond the top wave branch (a Step 5 fix for a combined
  `ops verify` failure, a parked wave's bookkeeping, the final sweep), it is submitted
  as the top layer of the stack, titled `code-review run <date>: integration and
  bookkeeping`.

### 3. Bookkeeping must land inside the wave's own layer

Today the `chore(backlog)` commit is made after the merge lock is released. In stacked
mode that puts wave A's task flips on top of whatever landed after A, so they show up
in another wave's PR, and the last wave's flips land in no PR at all.

Stacked mode therefore extends the locked command. The wave closes and commits its
bookkeeping while it still owns the tip, then the wave branch is fast-forwarded to
include that commit:

```bash
ops lock code-review-merge --timeout 3600 -- bash -c '
  set -e
  git -C ../.wave-<waveTaskId> rebase <landing-branch> \
    || { git -C ../.wave-<waveTaskId> rebase --abort; exit 3; }
  (cd ../.wave-<waveTaskId> && ops verify)
  git merge --ff-only code-review/<waveTaskId>
  ops backlog task edit -s Done <waveTaskId>
  ops lock code-review-backlog --timeout 600 -- \
    ops backlog commit <waveTaskId> <memberId>... <filedTriageId>... \
      -m "chore(backlog): close code-review wave <N>"
  git -C ../.wave-<waveTaskId> merge --ff-only <landing-branch>
'
```

Consequences to write into the protocol:

- Invariant 4 ("the merge lock is held across rebase → integration verify → merge, and
  nothing else") gets a stacked-mode clause. The additions are three fast commands, no
  thinking and no build, so other waves do not wait meaningfully longer.
- "No runner holds both locks at once" becomes "the backlog lock is only ever taken
  inside the merge lock or with no lock held". Lock order is always merge then backlog,
  so there is no deadlock. A parking wave still takes the backlog lock alone.
- The wave is only marked `Done` in this path when every member is already `Done`. A
  wave with open members never enters the locked command in stacked mode; it parks. A
  partial wave must not become a layer, because a layer that merges would close out
  work that is not finished.
- The wave branch now contains task files. That was forbidden to keep concurrent waves
  from colliding on `.backlog/`; it is safe here because the commit is made on the
  landing branch under both locks and the wave branch only fast-forwards to it.

### 4. Teardown keeps landed branches

Stacked mode runs `git worktree remove ../.wave-<waveTaskId>` and skips
`git branch -d`. The branch is the PR head and must outlive the run.

This changes what a leftover branch means, so three places need a stacked-mode reading:

- `code-review-run-waves` Step 6 ("anything left besides the run branch belongs to a
  parked wave"): a branch with no worktree whose wave task is `Done` is a landed layer.
- Protocol Recovery, "abandoned claim branch": same test before calling it abandoned.
- Preconditions, "no stale worktrees": unaffected, landed layers have no worktree.

The claim guard still works. A landed wave is `Done`, so it is never enumerated, and
its surviving branch would refuse a second claim anyway.

### 5. Publishing the stack

Step 5 of `code-review-run-waves`, after every runner has returned and the combined
`ops verify` has passed on the run branch. Layer order is derived from git, with no
extra state to keep:

```bash
# landed wave branches, bottom to top
for b in $(git branch --list 'code-review/TASK-*' --merged <run-branch> \
             --format='%(refname:short)'); do
  echo "$(git rev-list --count main.."$b") $b"
done | sort -n | cut -d' ' -f2
```

Then, from the main checkout, which stays on the run branch throughout:

```bash
export GH_STACK_NO_UPDATE_NOTIFIER=1
git push -u origin <bottom> ... <top> [<run-branch>]
# once per layer, bottom to top; the base is the layer below, `main` for the bottom
gh pr create --base <layer-below> --head <branch> \
  --title "<wave title>" --body-file <wave report>
gh stack link --base main <bottom> ... <top> [<run-branch>]   # links the PRs into one Stack
```

`gh stack link` (checked against `gh stack link --help`, v0.2.0) takes branches, PR
numbers or PR URLs in bottom-to-top order, reuses a branch's open PR, creates any that
are missing, corrects bases, and needs no local tracking state.

- `link` is preferred over `gh stack init` + `gh stack submit` for two reasons the help
  text makes clear. `submit`, `sync`, `push` and `view` act on the *current* stack, the
  one containing the checked-out branch, and the main checkout sits on the run branch,
  which is usually not a layer. And `init` checks out the top branch it adopts, which
  would move the main checkout off the run branch that parked waves resume against.
- Creating the PRs with `gh pr create` first gives each one its real title and body at
  creation. `submit --auto` would generate titles and open drafts.
- Each PR body is that wave's own report: members with `✓`/`✗`/`~`, both verify
  results, `Triage` tasks it filed. The bottom PR additionally carries the run summary:
  the wave table, the executed order, parked waves and how to resume them.
- The stack number for the report is read from the PR after linking (REST `stack`
  object on the pull request; exact field path is a spike item).
- A resumed run appends with `gh stack link <stack-number> <new-branch>...`, which adds
  to the top of an existing Stack without re-listing its PRs.
- Local tracking is only needed for the follow-up commands in section 7. It is created
  on demand with `gh stack checkout <stack-number>`, never during a run.
- `gh stack` mutations coordinate only with other `gh stack` processes. They run in
  Step 0 and Step 5 only, never while a runner is in flight.

### 6. Run state and resume

Default mode decides a run's state from the run branch's PR. Stacked mode decides it
from the stack, in Step 0, before anything is created:

| Stack state | Action |
|-------------|--------|
| No kept wave branches, no stack | Fresh run |
| Kept wave branches, nothing submitted | Run parked before publishing: resume, the branches stay as the lower layers |
| Stack open, nothing merged | Resume: new waves land on top, `gh stack link <stack-number> <new-branch>...` adds their PRs to the top of the existing Stack |
| Stack open, lower layers merged | `gh stack sync --prune` first, so remaining layers are rebased onto `main`; then re-point the run branch at the stack top and resume |
| Every PR merged | Completed run whose cleanup was skipped: `gh stack sync --prune`, drop the run branch, start fresh. A fully merged Stack cannot be extended, so the new run links a new one |
| Any PR closed unmerged | Stop and report, as `CLOSED` does today |

Re-pointing the run branch after a sync is `git checkout -B <run-branch> <top-branch>`,
allowed only when the run branch has no commits of its own. If it does, it is a layer
and `gh stack sync` has already rebased it.

### 7. After review

The skill does not merge unless asked, same as today. What changes is the user's side,
and it belongs in the protocol reference rather than in a report:

```bash
gh stack merge --yes --squash        # whole stack, all-or-nothing, bottom-up
gh stack merge <pr-number>           # everything up to and including that PR
gh stack sync --prune                # afterwards: rebase what is left, delete merged local branches
git checkout main && git pull && git branch -D <run-branch>
```

Review feedback on a lower layer is fixed on that branch, then `gh stack rebase
--upstack` and `gh stack push`. That is a manual flow in the first version (see open
questions).

### 8. Preconditions added in stacked mode

- `gh stack` is installed: `gh extension list` shows `github/gh-stack`. It is not
  installed on this machine today. Stop with the install line
  (`gh extension install github/gh-stack`) if missing; never install it silently.
- Git 2.36 or newer.
- All branches live in this repository. Stacks do not span forks.
- No `ops` floor change. Every ops command used is already covered by 0.74.0.

## Trade-offs to accept

- **A stack is linear, waves are not always dependent.** Two waves that overlap nothing
  still end up as layer 1 and layer 2, so a stalled review on layer 1 blocks merging
  layer 2. Independent PRs per wave would avoid that, but then each wave would need its
  integration verify against `main` alone and conflicts would move to merge time. The
  stack keeps the property that the combination was verified.
- **CI runs once per layer.** Every PR in a stack triggers `pull_request` workflows as
  if it targeted `main`, so an N-wave run costs N CI runs instead of one. `ci.yml` can
  gate expensive jobs on `github.event.pull_request.stack.position`; left out of scope
  until it hurts.
- **A lower layer that changes forces a cascade rebase** of everything above it, and a
  force-push per layer. Default mode has no equivalent cost.
- **Bookkeeping moves inside the merge lock**, a small widening of the one section that
  serialises the whole fan-out.

## Work items

1. **Spike on a scratch repo** (blocks everything else; see open questions 1 to 3):
   `gh pr create` per chained branch, `gh stack link` over them in a non-TTY, appending
   with `gh stack link <stack-number> <branch>`, `gh stack merge <stack-number> --yes
   --squash`, then `gh stack checkout <stack-number>` and `gh stack sync --prune`.
2. `plugins/dev/skills/code-review-run-wave/references/stacked-delivery.md` (new): the
   whole of the Design section as protocol. A new file rather than more sections in
   `worktree-protocol.md`, so a default-mode runner never reads it, and because
   `code-review-run-wave/SKILL.md` is already at 435 lines.
3. `code-review-run-waves/SKILL.md`: argument and mode recording in Step 0, stack run
   state, Step 5 publish branch, Step 6 teardown reading, Step 7 report (stack number,
   one URL per layer), frontmatter `description` (no longer always "a single PR"),
   `allowed-tools` gains `Bash(gh stack:*)`, `Bash(gh extension list)`,
   `Bash(git config:*)`.
4. `code-review-run-wave/SKILL.md`: mode argument, Step 5 note that "never per-wave PR"
   applies to `commit-script` `pr` mode only, Step 7 locked command variant, Step 8
   teardown and bookkeeping variant, the same `allowed-tools` additions. Each a short
   pointer into `stacked-delivery.md`.
5. `worktree-protocol.md`: invariants 4 and 6 and the Recovery "abandoned claim" entry
   get a one-line stacked-mode pointer.
6. `README.md`: overview row, the usage example, and Requirements (`gh stack` for
   stacked mode only).
7. `AGENTS.md`: the `code-review-run-wave` / `code-review-run-waves` relationship
   bullets, plus a note that `gh stack` is an optional dependency outside the ops table.
8. `ops qa`, then one real stacked run against a repo with at least three open waves,
   two of them overlapping, before merging.

`commit-script`, `code-review-triage` and the review skills need no change.

## Open questions

1. **Is the Stacks feature enabled for the target repos?** The CLI installs anywhere,
   but the Stack object is created server-side. The spike answers this for
   `rsvalerio/ai`; consumer repos need a preflight that fails clearly rather than
   leaving N unlinked PRs behind.
2. **Does `gh stack link` behave in a non-TTY agent shell** as its help describes,
   including the append form on resume and the case where a lower layer already merged?
3. **Where does the main checkout sit during `gh stack sync`?** `sync` acts on the
   current stack, so the lower-layers-merged resume in section 6 needs
   `gh stack checkout <stack-number>` first and a switch back to the run branch after.
   That is safe only because Step 0 runs before any runner starts; confirm the round
   trip leaves the run branch pointing at the rebased stack top.
4. **Should the runner handle review feedback?** A follow-up
   `/code-review-run-waves stacked sync` could run `gh stack sync`, re-verify each
   rebased layer and push. Left out of the first version.
5. **Should partial waves ever become layers?** This plan says no. The alternative, a
   draft layer for a wave with open members, makes the stack unmergeable past it.
6. **Does ops want a `wave land` command** that owns the extended locked sequence? Not
   needed for a first version; worth it if the bash block in section 3 proves fragile.
