---
name: babysit-prs
description: Watches every open pull request the user authored across GitHub (the github.com/pulls list), plus Dependabot PRs in their own repos, and moves each one forward in a single pass. It fixes failing CI, rebases conflicted or stale branches and applies requested review changes, pushing from an isolated worktree, and drafts replies to review threads, including Greptile findings weighed by severity, that are posted only after the user approves them. It never merges. Use when the user asks to babysit, watch, check on, shepherd or "get green" their PRs, asks what their open PRs need, or runs it under /loop to keep PRs moving until they are ready to merge.
license: Apache-2.0
---

# Babysit PRs

## Purpose

One pass over the user's open PRs: work out what each one is waiting on, do the work
that is safe to do unattended, and hand back one short report naming what still needs
the user. The skill is built for `/loop /babysit-prs`. Each pass is idempotent, so
running it again changes nothing that has already been handled.

What a pass may do without asking:

- fix a failing check, or re-run it once when the failure is infrastructure, not code
- rebase a conflicted (`DIRTY`) or out-of-date (`BEHIND`) branch onto its base
- make the code change a review comment asks for, when the request is clear
- commit and push those changes to the PR's own head branch
- comment `@dependabot rebase` on a Dependabot PR that Dependabot still owns
  (`references/dependabot.md`)

What a pass never does without an explicit yes in this conversation: post any other
comment or reply, resolve a thread, request reviewers, change draft or ready status, edit the PR
title or body, close or merge. A reply goes out under the user's name, and once posted
it cannot be taken back.

## Invocation

| Argument | Effect |
|----------|--------|
| *(none)* | Every open PR authored by the user, all repos, plus Dependabot PRs in cloned repos the user can push to |
| `OWNER/REPO#N`, a PR URL, or `#N` (current repo) | Only that PR |
| `OWNER/REPO` | Only PRs in that repo |
| `--dry-run` | Classify and plan only. It may read clones, but it does not fetch, create worktrees, push, re-run, post or `--record`. Show each planned command and draft instead |
| `--from FILE.json` | Read a saved snapshot instead of querying GitHub (implies `--dry-run`, and `--record` is skipped too) |

## Process

### Step 1: Snapshot

```bash
gh auth status >/dev/null || { echo "gh is not authenticated"; exit 1; }
python3 scripts/pr-state.py [--from FILE.json] > "$SCRATCH/prs.json"
```

`scripts/` is relative to this skill's directory. The script reads every open PR the
user authored and its checks, unresolved review threads and merge state, finds a local
clone for each repo (under `$BABYSIT_PRS_ROOTS`, default `~/projects`), and gives each
PR one `next` value. Work from that JSON.

Two bots get their own handling, each in a reference file read only when the snapshot
calls for it. Read `references/greptile.md` when any PR has a non-null `greptile`, and
`references/dependabot.md` when any PR has `kind: "dependabot"`. Run your own `gh` queries only for what it
leaves out, such as failed job logs.

### Step 2: Triage

Group the PRs by `next`:

| `next` | Meaning | Action |
|--------|---------|--------|
| `rebase` | Conflicts with base (`DIRTY`), or base moved and the branch must be up to date (`BEHIND`) | Step 3a |
| `dependabot-rebase` | A Dependabot-owned PR is behind or conflicted | `@dependabot rebase` (`references/dependabot.md`) |
| `fix-ci` | A check failed on the head commit | Step 3b |
| `address-review` | A reviewer (human or bot) has an unresolved thread the user has not answered and no reply has been drafted | Step 3c |
| `stuck` | A check still fails after two fixes this skill pushed | Report what was tried; needs the user |
| `wait-ci` | Checks still running | Report only |
| `wait-bot` | Greptile has not reviewed the head yet (for up to 30 minutes after the push), or a requested Dependabot rebase has not landed | Report only; check back in minutes |
| `await-approval` | Every open thread already has a draft waiting on the user | Re-present the drafts |
| `wait-review` | Green, waiting for a reviewer | Report only |
| `draft` | Green draft PR | Report only. Marking it ready is the user's call |
| `ready` | Green, approved or no review required, nothing open | Report as ready to merge |

A PR whose `clone` is null cannot be changed from here. Report what it needs and
suggest the clone command, but do not clone on your own: where the user keeps
checkouts is their decision.

Handle PRs one at a time, each in its own worktree. A failure on one PR goes into the
report and the pass moves on to the next.

### Step 3: Work in a worktree, never in the user's checkout

The user's clone may hold uncommitted work, and its branch may be the PR branch itself.
Touching it would lose that work or fight their editor. Always work in a detached
worktree:

```bash
git -C "$CLONE" fetch origin "$BASE" "$HEAD"
WT="$SCRATCH/wt-$(basename "$CLONE")-$N"
git -C "$CLONE" worktree add --detach "$WT" "origin/$HEAD"
test "$(git -C "$WT" rev-parse HEAD)" = "$HEAD_OID"   # snapshot still current
```

If the SHA check fails, someone pushed since the snapshot. Drop this PR for the pass;
the next pass will see the new state. When the PR is done (pushed or abandoned), remove
the worktree: `git -C "$CLONE" worktree remove --force "$WT"`.

When `head_repo` differs from `repo`, the PR comes from a fork. Push to the fork's
remote, and skip the PR when the user cannot push there.

#### 3a. Rebase

```bash
git -C "$WT" rebase "origin/$BASE"
```

Resolve conflicts only where both sides' intent is clear from the code and the commit
messages. When a conflict needs a judgement about behaviour, `git rebase --abort` and
report the conflicting files. A wrong resolution pushed to a PR is worse than a
conflict left for the user. After a successful rebase, run the gate (Step 4) and push
with a lease pinned to the SHA you started from, so a concurrent push is refused, not
overwritten:

```bash
git -C "$WT" push --force-with-lease="$HEAD:$HEAD_OID" origin "HEAD:refs/heads/$HEAD"
```

#### 3b. Fix CI

Read the failure before changing anything:

```bash
gh run view <run-id> -R "$REPO" --log-failed | tail -n 200
```

The run id is in the check's `url` (`.../actions/runs/<run-id>/job/...`). Then decide:

- **Infrastructure** (runner lost, network timeout, rate limit, cache 5xx, a test that
  passes on re-run of the same SHA): `gh run rerun <run-id> --failed -R "$REPO"`, once
  per head SHA. If it fails the same way again, treat it as code.
- **Code**: reproduce locally in the worktree, fix the cause, run the gate, commit, push
  (a plain fast-forward `git push origin "HEAD:refs/heads/$HEAD"`). Then record the
  attempt:
  `python3 scripts/pr-state.py --record ci-attempt "$REPO#$N" "<check name>" "<new sha>"`.
- **Stop at two.** A failing check with `attempts >= 2` gets no third fix (the PR
  classifies as `stuck` once nothing else is actionable). Report it with what you tried. Two failed fixes mean the cause is not what you
  thought, and more pushes only add noise to the PR.

Fix the failure, not the check. Disabling a test, loosening a lint or adding `continue-on-error`
to make CI pass is not a fix; if that seems like the only way, report it instead.

#### 3c. Address review

Read each entry in `open_threads` whose `drafted` is false: the whole conversation, the
file at `path:line` in the worktree, and whether the thread is `outdated` (the code has
moved since). Then pick one:

- **Clear, correct request**: make the change, gate, commit, push. Draft a reply naming
  the commit (`Done in abc1234: <one line on what changed>`).
- **Already addressed** (often when `outdated`): draft a reply pointing at the commit
  that addressed it.
- **Disagree, unclear, or it changes behaviour the user chose**: change nothing. Draft a
  reply that explains the reasoning or asks the question, written as the user would.
  Bot reviewers (greptile, coderabbit, copilot and the like) are often wrong. Weigh
  their claims against the code; do not just accept them.

Batch every change for one PR into as few commits as makes sense, and push once.

### Step 4: Gate and commit

Before any push, run the repository's own gate in the worktree: `ops verify` when there
is a `.ops.toml`, otherwise the command the failing CI job runs, otherwise the
project's documented test command. Never push a change the gate rejects.

Commit with the repo's conventions (read `git log --oneline -10`; this user's repos use
Conventional Commits). Follow the user's global instructions on commit messages, which
for this user means no `Co-Authored-By` trailer and no AI attribution line.

### Step 5: Present drafts and ask

Collect every drafted reply from this pass, plus any earlier drafts still waiting
(`await-approval`), and show them to the user grouped by PR. For each, show the
reviewer's last comment (trimmed), the thread URL and the draft. Then ask once, as a
single question covering all drafts, whether to post them all, post some, or edit them.

Record each draft as soon as you show it, so the next `/loop` pass does not draft the
same thread again:

```bash
python3 scripts/pr-state.py --record drafted "$REPO#$N" "$THREAD_ID" "$LAST_COMMENT_ID" < "$DRAFT_FILE"
```

The draft text is saved with it, so an `await-approval` pass shows the saved `draft`
from the snapshot and does not write a new one. A reviewer comment that arrives later
changes the thread's last comment id, which reopens the thread for a fresh draft.

On approval, post each reply to its thread and resolve the thread only when the reply
says the request is done. Leave a disagreement open for the reviewer:

```bash
gh api graphql -f query='mutation($t:ID!,$b:String!){addPullRequestReviewThreadReply(input:{pullRequestReviewThreadId:$t,body:$b}){comment{url}}}' -f t="$THREAD_ID" -f b="$BODY"
gh api graphql -f query='mutation($t:ID!){resolveReviewThread(input:{threadId:$t}){thread{isResolved}}}' -f t="$THREAD_ID"
```

If the user does not answer (an unattended `/loop`), leave the drafts recorded and
unposted. The next pass will show them again as `await-approval`.

### Step 6: Report

End every pass with one table and a status line. Keep it short, because under `/loop` it
is what the user scrolls back through.

```text
| PR | State | This pass | Needs you |
|----|-------|-----------|-----------|
| rsvalerio/ops#117 | ready · Greptile 4/5 | — | merge |
| rsvalerio/ops#113 | dependabot-rebase | asked @dependabot to rebase | — |
| valycorp/valysec#23 | fix-ci | fixed clippy::needless_borrow, pushed 3f2a1c9 | — |
| rsvalerio/ai#33 | await-approval | 2 replies drafted | approve drafts |

Next: CI running on 1 PR; nothing else to do until it finishes.
```

The status line tells a self-paced `/loop` how long to wait: `CI running` or
`waiting on Greptile/Dependabot` means check back in minutes; `waiting on reviewers` or `waiting on you` means a long interval; and
`all PRs ready or waiting on humans; nothing left to babysit` means stop the loop.

## Concurrency

Two passes on the same PR would race to push. The SHA check in Step 3 and the
`--force-with-lease` push make the loser fail instead of clobbering, so a refused
push means another pass got there first. Drop the PR and let the next pass re-read it.

## References

- `scripts/pr-state.py`: snapshot, classification (`next`) and the state file
  (`${XDG_STATE_HOME:-~/.local/state}/babysit-prs/state.json`)
- `references/greptile.md`: where Greptile writes, severity-based handling, re-reviews
- `references/dependabot.md`: which Dependabot PRs are included, bot-owned vs edited
  branches, failing bumps, the commands that stay with the user
- `skills/commit-script/SKILL.md`: commit message conventions shared with this plugin
