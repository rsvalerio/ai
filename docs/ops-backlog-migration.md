# Migrating the code-review skills to `ops backlog`

Status: applied. Written 2026-09-06 against ops v0.47.x, rewritten 2026-09-07
against what actually shipped (ops v0.52.0).

## What changed

The skills used to shell out to the Backlog.md npm CLI (`backlog`, pinned at
v1.51.0). They now call `ops backlog`, a native subsystem in
[ops](https://github.com/rsvalerio/ops) (`crates/backlog`, documented in
[`docs/backlog.md`](https://github.com/rsvalerio/ops/blob/main/docs/backlog.md))
that manages the same `.backlog/` markdown tree. It reads every file the npm
tool has written here and writes files that tool reads back, so both can
operate on one tree during a transition. That removes the node/npm dependency
from every review run.

The create/list/search calls the skills made needed no flag changes — only the
`ops` prefix. Two things did need work in ops first, and one convention
changed.

## 1. Membership could not be read the old way

`code-review-run-wave` used to take member ids from a `Dependencies:` line in
`ops backlog task view <waveTaskId> --plain`. That output has no dependency
block at all (and npm 1.51.0 prints a `Dependency Graph:` tree, not a comma
list, so the step was already stale). Waves are now enumerated with commands
that exist for the purpose:

```bash
ops backlog wave list -s 'To Do' --plain     # open waves
ops backlog wave members <waveTaskId> --plain # that wave's members
```

`wave members` returns the union of the wave's `dependencies:` and every task
whose `parent_task_id` names it, so it answers correctly whichever direction a
given wave was written in.

## 2. The assignee overload is retired

Wave bookkeeping used to overload `assignee`: the wave parent carried the
hardcoded assignee `code-review-wave`, and each member's assignee was its
wave's task id. Nothing could hold a real assignee. The convention is now
structural, and lives in ops rather than in four `SKILL.md` files:

| Overload before | Now | Written by |
|---|---|---|
| wave parent's `assignee` = `code-review-wave` | label `code-review-wave` | `-l code-review-wave` on create |
| member's `assignee` = wave task id | member's `parent_task_id` | `ops backlog task edit --parent <waveTaskId> <taskid>` |
| wave discovered via `task list -a code-review-wave` | `ops backlog wave list` | — |

Each wave keeps its `dependencies:` list of members exactly as before — the
direction was not flipped, so the backfill is purely additive.

Existing trees convert in one command:

```bash
ops backlog wave migrate --dry-run   # read the plan
ops backlog wave migrate             # confirm at the prompt
```

It moves the marker to the label, sets each member's `parent_task_id`, clears
those assignees, and adds any member found only through the assignee to the
wave's dependency list. It preflights the whole tree first — a member with a
conflicting `parent_task_id`, or an assignee naming a task that is not a wave,
aborts before the first write — and running it twice is a no-op.

## 3. Definition of Done exists now

`code-review-run-wave` referenced `--check-dod`, which ops did not have: it
rendered the DoD section as a hardcoded empty placeholder. ops now models
per-task definition-of-done items (`--dod` on create; `--dod`,
`--check-dod N`, `--uncheck-dod N` on edit), with the same on-disk shape the
npm CLI writes. `--dod` replaces the list, matching ops' own `--ac`; npm's
appends.

## Notes

- There is no `ops backlog init`. A fresh repo needs `mkdir -p .backlog/tasks`;
  `backlog.config.yml` at the workspace root is optional (defaults otherwise).
- `search` scoring is deterministic keyword containment, not npm's fuzzy
  algorithm. The dedup step matches on a rule id, so containment is what it
  wanted; the row shape is unchanged.
- `sed -n '1s/^File: //p'` on `task view --plain` still works — the first line
  is the absolute path, and an ops integration test pins it through a real
  `sed`.
- Output contracts are pinned by golden tests on the ops side, so a
  half-migrated tree and a half-migrated skill set interoperate.
