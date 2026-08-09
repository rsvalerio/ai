---
name: commit-script
description: Review unstaged/staged changes and git log, then generate a shell script that groups related files into conventional commits, optionally on a branch that ends in a pull request
allowed-tools: Bash, Read, Write, Glob, Bash(git *), Bash(gh *)
license: Apache-2.0
---

# Task

Review the current git state and generate a commit script.

## Invocation

Arguments are free-form; recognise these anywhere in them:

| Argument | Effect |
|---|---|
| `pr`, `--pr`, `mode: pr`, "open a PR" | `pr` mode (Step 0) |
| `commit`, `--commit`, `mode: commit` | `commit` mode — the default |
| `draft`, `--draft` | `pr` mode with `gh pr create --draft` |
| `--base <branch>` | Override the PR base instead of resolving remote HEAD |
| `--branch <name>` | Use this topic branch name instead of deriving one |
| a path ending in `.sh` | Output path (Step 0b) |

Examples:

```text
/commit-script                                  # commit mode, /tmp/commit-groups.sh
/commit-script pr                               # branch + push + gh pr create
/commit-script pr --draft --base develop
/commit-script pr --branch feat/pr-mode
/commit-script /tmp/commit-groups-TASK-12.sh    # commit mode, custom output path
```

## Step 0 — Determine the mode

The skill has two modes. They share Steps 1–3 and differ only in what the generated
script does after the commits.

| Mode | What the script does | When to use |
|---|---|---|
| `commit` (default) | Stages and commits the groups on the current branch. Nothing is pushed. | Local work, and every automated caller — `code-review-run-wave` merges the branch itself. |
| `pr` | Creates a topic branch, commits the groups on it, pushes it, and opens a pull request with `gh`. | Work that should land through review instead of straight onto the current branch. |

Pick the mode in this order:

1. The caller or user named one explicitly ("mode: pr", "open a PR", "just commit").
2. Otherwise default to `commit`.

Never silently upgrade `commit` to `pr` — pushing a branch and opening a PR is
outward-facing, so it happens only when it was asked for.

If mode is `pr`, confirm `gh` is available and authenticated before writing the script:

```bash
gh auth status
```

If it is not, say so and fall back to `commit` mode rather than emitting a script that
will fail halfway through.

## Step 0b — Determine the output path

Default to `/tmp/commit-groups.sh`.

If the caller supplied an output path, use it verbatim. Callers that may run concurrently
**must** supply one — `code-review-run-wave` passes
`/tmp/commit-groups-<waveTaskId>.sh` so parallel waves cannot overwrite each other's
script.

All git commands below run in the **current working directory**. When the caller is
working inside a git worktree, run this skill from that worktree so `git status` and the
generated `git add` paths describe that tree and not the main checkout.

## Step 1 — Gather context

Run these to understand what's changed:

```bash
git log --oneline -20
git status --short
git diff --stat HEAD
```

If the repo has no commits yet, use `git diff --cached --stat` and `git status --short` instead.

In `pr` mode also resolve the current branch and the base to target:

```bash
git branch --show-current
git remote show origin | sed -n 's/.*HEAD branch: //p'
```

The base branch is `--base` if given, otherwise the remote HEAD (usually `main`). If the
current branch is already a topic branch — anything other than the base — reuse it
instead of creating another one.

## Step 2 — Analyse and group

Group the changed files by **semantic meaning** — what they do together, not where they live. Each group becomes one commit.

Pick exactly one type per commit from:
`feat` `fix` `docs` `perf` `refactor` `style` `test` `build` `ci` `chore`

Format: `type(scope): short imperative description`

- scope = the affected area (crate name, module, directory, concept)
- description = what it does, not what you changed

## Step 3 — Write the script

Create the script at the output path from Step 0b. Both modes share the same commit
blocks; `pr` mode wraps them in a branch and a pull request.

### 3a — Commit blocks (both modes)

```sh
#!/usr/bin/env bash
set -e

echo "Group N — <short label>"
git add <files...>
git commit -m "type(scope): description"
```

- One block per group, numbered sequentially
- No blank lines inside a block; one blank line between blocks
- All `git add` paths relative to repo root
- End with a newline

Never use `git add -A` or `git add .` — stage explicit paths only. A blanket stage sweeps
up anything else present in the tree, which is how unrelated work ends up in a commit.

In `commit` mode the script stops here. It never pushes.

### 3b — Branch and pull request (`pr` mode only)

Wrap the commit blocks: a branch prologue before Group 1, and a push plus PR epilogue
after the last group.

Prologue — only when the current branch is the base branch. If a topic branch is already
checked out, omit it entirely and commit onto that branch.

```sh
git switch -c <branch>
```

Branch name: `--branch` if given, otherwise `<type>/<short-slug>` derived from the
dominant group — for example `feat/pr-mode` or `fix/commit-paths`. Keep it kebab-case and
under ~40 characters.

Epilogue:

```sh
git push -u origin <branch>
gh pr create --base <base> --head <branch> --title "<title>" --body "<body>"
```

- title = the dominant group's commit subject, or a summary line when the groups are
  peers
- body = a short paragraph of intent followed by one bullet per commit group
- Write the body with `--body-file /tmp/pr-body-<slug>.md` and a heredoc when it spans
  more than a couple of lines, so quoting cannot mangle it
- Add `--draft` when the caller asked for a draft

Do not add `--fill`, `--web`, or any auto-merge flag. The script's job ends at an open PR.

Full shape of a `pr`-mode script:

```sh
#!/usr/bin/env bash
set -e

git switch -c feat/pr-mode

echo "Group 1 — PR mode"
git add skills/commit-script/SKILL.md
git commit -m "feat(commit-script): add pull request mode"

echo "Group 2 — docs"
git add README.md AGENTS.md
git commit -m "docs: describe commit-script modes"

git push -u origin feat/pr-mode
gh pr create --base main --head feat/pr-mode \
  --title "feat(commit-script): add pull request mode" \
  --body-file /tmp/pr-body-pr-mode.md
```

## Step 4 — Review

After writing the file, print the full script content so the user can review it before
running, and state which mode it is. In `pr` mode also name the branch, the base, and the
PR title, so the outward-facing part is visible before anything is pushed.

The script is never run by this skill — the user (or the calling skill) runs it.

## Concurrency

Multiple instances can run in parallel only if each is given a distinct output path
(Step 0b) **and** each runs against a distinct working tree. Two instances sharing one
checkout would stage from the same git index and interleave commits; isolate them with
`git worktree` first — see `skills/code-review-run-wave/references/worktree-protocol.md`
in the **code-review-run-wave** skill.

Concurrent runs use `commit` mode. `pr` mode creates and pushes a branch, which the wave
protocol already owns — a wave runner asking for a PR would push a second branch for work
it is about to merge itself.
