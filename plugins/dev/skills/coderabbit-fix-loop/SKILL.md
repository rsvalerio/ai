---
name: coderabbit-fix-loop
description: Runs the CodeRabbit CLI review in agent mode, fixes the findings worth fixing, runs the repo's gate, commits the round locally, and reviews again until a round brings no new finding worth fixing or a round cap is hit. Declined findings are recorded with a reason so later rounds skip them. Never pushes. Use when the user asks to run coderabbit (or cr) review and fix what it finds, or to loop CodeRabbit until clean.
license: Apache-2.0
---

# CodeRabbit Fix Loop

## Purpose

Loop review → fix → gate → local commit, with a fixed stopping rule and a memory of declined findings.

Never: push, pass `--use-credits`, run `coderabbit review findings --clear`, or commit work that was in the tree before the run without the user's yes.

## Invocation

Arguments (free-form): `--max-rounds <n>` (default 5), `--base <branch>` / `--base-commit <sha>`, `--min-severity critical|major|minor|trivial|info` (default `minor`), and `--deep` / `--dir <path>`, which are passed through to every review.

## Process

### 1. Preflight

Stop if `coderabbit` is missing or the directory is not a git repo. If `git status --porcelain` shows changes, ask once whether to commit them first. If the user says no, they are reviewed but never staged. A fix that needs one of those files is reported, not applied.

### 2. Pin the review base

Resolve one base and reuse it every round. A default review after a commit sees nothing and would end "clean".

1. `--base` / `--base-commit` if given.
2. On a non-default branch: `--base <default>`, from `git symbolic-ref --short refs/remotes/origin/HEAD` (fallback `main`).
3. On the default branch: `--base-commit <HEAD at start>` (after any step 1 commit). If unpushed commits are the work to review, use `git merge-base HEAD origin/<default>` instead. Ask if it is unclear which.

If round 1 reviews no files, the base is wrong: stop with `blocked`, not `clean`.

### 3. Ledger

`<git-dir>/coderabbit-fix-loop/ledger.json` holds `base`, `startHead`, `rounds` (`n`, `commit`, `fixed`, `declined`), and `declined` (`fingerprint`, `file`, `title`, `severity`, `reason`). If the stored `base` matches, keep `declined` across runs. Otherwise start fresh.

### 4. Round

```bash
coderabbit review --agent <base flag> [--deep] [--dir <path>]
```

On a usage-limit, auth or network error, stop with `blocked`. Do not retry. If the output shape is unexpected, `coderabbit review findings` shows the stored findings.

Skip findings that are in the ledger, matched by `fingerprint`, or by `file` + `title` when lines moved. Read the code behind each new one, then:

- **Fix** a real defect: correctness, security, error handling, a leak, an edge case, a wrong doc claim. Also fix a cheap, clear improvement at or above `--min-severity`.
- **Decline**, with a one-line reason, a finding that:
  - conflicts with repo rules (`CLAUDE.md`, `AGENTS.md`, linter config)
  - is a taste nit
  - widens the scope
  - targets generated or vendored code
  - is already handled elsewhere
  - is wrong: verify this one carefully before declining
  - is below `--min-severity`, unless it is a one-line obvious fix

Never weaken a test, delete a check or add a lint `allow` to silence a finding. If that is the only fix, decline it.

### 5. Gate and commit

Run the first gate that exists: `ops verify` (`.ops.toml`), a Makefile `check`/`ci`/`test` target, `package.json` `typecheck`/`lint`/`test`, or `cargo check --all-targets && cargo test`. If none exists, say so.

If a fix breaks the gate, repair it or revert it and decline it with reason `fix broke <gate>`. If the gate already failed at `startHead`, only judge whether this round made it worse.

Stage only the files the round changed, then commit with `fix: address CodeRabbit review (round <n>)`. Use a narrower type or scope if all fixes share one, and put one body line per fix. No attribution trailers. A round with no fixes makes no commit.

### 6. Stop or continue

Stop on the first that applies:

- `clean`: no findings.
- `no new actionable findings`: nothing was fixed.
- `oscillating`: a finding fixed in an earlier round came back. Do not refix it.
- `round cap`: `--max-rounds` reached.
- `blocked`: the review or the gate cannot run.

Otherwise go back to step 4.

### 7. Report

Give the stop reason, the rounds and base, `git log --oneline <startHead>..HEAD`, the fixes by file, and the declined findings with reasons. To overrule a declined finding, delete its ledger entry and rerun. End with the gate result and confirm that nothing was pushed.

## Concurrency

One loop per worktree. The ledger and CodeRabbit's checkpoint are scoped per repo and branch.

## References

- `coderabbit review --help`: check flags there rather than guessing.
- `skills/commit-script/SKILL.md` in `pr` mode, to regroup the commits or open a PR afterwards.
