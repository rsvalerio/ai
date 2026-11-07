---
id: TASK-0024
title: 'code-review-run-waves: a fan-out can fill the disk and destroy in-flight wave work'
status: To Do
assignee: []
created_date: '2026-10-31 12:44'
labels:
  - plugins
  - waves
  - dogfood
dependencies: []
modified_files:
  - plugins/dev/skills/code-review-run-waves/SKILL.md
  - plugins/dev/skills/code-review-run-wave/SKILL.md
priority: medium
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**File**: `plugins/dev/skills/code-review-run-waves/SKILL.md`, `plugins/dev/skills/code-review-run-wave/SKILL.md`

**What**: During dbsec's 2026-10-30 run of nine waves, `/` reached 0 bytes available while four waves built concurrently, with `~/.cache/sccache` at about 125 GiB. Moving `CARGO_TARGET_DIR` to tmpfs did not protect `/`, because sccache stays on it, and four tmpfs build directories then exhausted the quota on Claude Code's temp directory, after which every Bash call lost its output.

**Why it matters**: Two runners rewrote source files in place on the full disk and left five files empty. Those were recovered from a scratch copy and by replaying an edit chain, and three have no original to compare with. `ops backlog wave park` also fails on a full disk, so a wave cannot be parked when it most needs to be.

**Also seen**: moving a target directory leaves stale `CARGO_BIN_EXE_*` paths in test binaries, so CLI tests fail with `NotFound` until the packages that embed them are rebuilt. `cargo clean -p dbsec` alone missed `dbsec-example-users`.

**Decided**: the sccache limit stays at 200G (`~/.config/zsh/rust.zsh`), so the skills have to carry the protection themselves.

**Origin**: dbsec TASK-1761.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 code-review-run-waves checks free space on the disk holding the worktrees and on the temp directory before each wave starts, and holds new waves below a stated floor
- [ ] #2 code-review-run-wave requires source edits to be written atomically, by temp file and rename
- [ ] #3 The skill says what to do when a wave cannot be parked because the disk is full
<!-- AC:END -->
