---
name: commit-script
description: Review unstaged/staged changes and git log, then generate a shell script that groups related files into conventional commits
allowed-tools: Bash, Read, Write, Glob, Bash(git *)
license: Apache-2.0
---

# Task

Review the current git state and generate a commit script.

## Step 0 — Determine the output path

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

## Step 2 — Analyse and group

Group the changed files by **semantic meaning** — what they do together, not where they live. Each group becomes one commit.

Pick exactly one type per commit from:
`feat` `fix` `docs` `perf` `refactor` `style` `test` `build` `ci` `chore`

Format: `type(scope): short imperative description`

- scope = the affected area (crate name, module, directory, concept)
- description = what it does, not what you changed

## Step 3 — Write the script

Create the script at the output path from Step 0, with this structure:

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

After writing the file, print the full script content so the user can review it before running.

## Concurrency

Multiple instances can run in parallel only if each is given a distinct output path
(Step 0) **and** each runs against a distinct working tree. Two instances sharing one
checkout would stage from the same git index and interleave commits; isolate them with
`git worktree` first — see `skills/code-review-run-wave/references/worktree-protocol.md`
in the **code-review-run-wave** skill.
