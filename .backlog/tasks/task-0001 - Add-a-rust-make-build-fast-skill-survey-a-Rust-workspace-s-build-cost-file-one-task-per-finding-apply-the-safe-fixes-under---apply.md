---
id: TASK-0001
title: 'Add a rust-make-build-fast skill: survey a Rust workspace''s build cost, file one task per finding, apply the safe fixes under --apply'
status: Done
assignee: []
created_date: '2026-09-26 14:33'
updated_date: '2026-09-27 20:54'
labels:
  - skill
  - build-performance
  - rust
dependencies: []
modified_files: []
priority: medium
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**Context**: the same build-speed work has now been done by hand in three workspaces — ops, dbsec, and event0 (in progress, 2026-09-26). The checks repeat each time, so they belong in a skill, modelled on `rust-make-clippy-pedantic`: survey without touching the tree, file one backlog task per finding, write configuration only under `--apply`.

**Prior art to extract from**:
- dbsec `docs/developing.md` ("ops verify" / "ops qax" sections): staged `verify` (rewriters alone, then read-only steps in parallel, `exclusive` steps as stage barriers so `next` reuses `build`'s artifacts instead of racing it for the cargo lock); separate target dirs for builds that resolve features differently (the two doc builds cost 14.5s every run while they shared `target/`, ~1.6s once split); nextest (`next`, `next-all`) with `leak-timeout` tuned under contention; every cost stated with a measured number and date.
- ops: stack `verify` staging (commit 5adb6be5), `clippy-default` kept out of `verify` because a second feature fingerprint means a second full compile per commit, nextest `ci` profile.
- event0 (the third case, measured during TASK-0667 and the follow-up build work): `[profile.dev.package."*"] opt-level = 2` compiling all ~417 dependencies optimized; `profile.test` `opt-level = 1` differing from dev so build and test compile the workspace twice; explicit `debug = true` + `incremental = true` with sccache (incremental crates are not cacheable — 35% Rust hit rate); 42 duplicated crate versions; a 60 GB `target/`; plain `cargo test` instead of nextest; `/tmp` on a 16 GB tmpfs that a cold all-features build overflowed (exit 101 with no compile error); `cargo test -- --ignored` also running ```ignore doctests, and stopping at the first failing doctest crate.

**How this differs from rust-make-clippy-pedantic** (design decisions, already agreed):
1. **Findings are measurements, not binary.** Each finding carries its measured cost on this machine and the date. Measuring is slow (a cold event0 build took 30+ min under load) and noisy, so the default mode is cheap — read profiles, `.cargo/config.toml`, `.ops.toml`, nextest config and the dependency graph, run `cargo tree -d`, `sccache --show-stats`, a warm `cargo build --timings` — and a cold measurement (into a target dir on real disk, never tmpfs) is opt-in via a flag. Record machine load alongside every timing.
2. **Some findings are trade-offs, not fixes** (e.g. dropping dependency opt-level speeds the build but may slow the tests, especially crypto). These are filed with both measurements and a recommendation, and are never auto-applied — not even under `--apply`.
3. **`--apply` touches more files** than lint policy: `Cargo.toml` profiles, `.ops.toml` gates, `.config/nextest.toml`, possibly `.cargo/config.toml`. Only findings classified as safe are applied.

**Sequencing (agreed)**: finish event0's build work by hand first, keeping a findings log (what was checked, what it cost to check, what it found, before/after numbers). Write the skill from all three cases, not from two plus guesses. Then use ops and dbsec — already optimized — as the skill's eval: a survey there should come back near-clean, and anything it flags is either a real leftover or a false positive to fix in the skill.

**Name**: `rust-make-build-fast`, matching `rust-make-clippy-pedantic`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 skills/rust-make-build-fast/ exists with SKILL.md (frontmatter name matches the directory, under ~500 lines) and references/ for the checks catalog, the measurement method, and the --apply templates; make ci passes
- [x] #2 The checks catalog covers at least: dev/test profile overrides (dependency opt-level, a test profile that differs from dev, debug/incremental settings vs sccache), test runner and gate layout (nextest, doctests run separately, staged verify with exclusive barriers), target-dir sharing and cargo-lock contention between builds with different feature fingerprints, duplicate crate versions, unused dependencies, sccache hit rate, and the tmpfs /tmp hazard
- [x] #3 The default mode never runs a cold build; a cold, --timings measurement is opt-in, writes its target dir to real disk, and records machine load with every timing
- [x] #4 Each finding is filed through ops backlog task create --plain with its measured cost, the date, and a safe or trade-off classification; trade-off findings carry both sides' measurements and are never auto-applied
- [x] #5 Without --apply the repository is byte-identical after a run; with --apply only safe findings' configuration is written, and nothing is committed, staged or pushed
- [x] #6 Surveys of ops and dbsec come back near-clean, and every finding they do produce is either confirmed as a real leftover or fixed in the skill as a false positive
- [x] #7 The skill is registered wherever the others are: README overview table and usage section, AGENTS.md skill relationships and directory tree, and the skill count in .claude-plugin/plugin.json and marketplace.json

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-09-26: skill written from the dbsec/ops docs and the event0 findings recorded in this task, by the user's decision to not wait for event0's hand-tuning (event0 becomes the first real run, not a source).

Eval (AC #6), default mode, ops @ 24d9b227 then dbsec @ d5b8337, run by a subagent with task creation diverted to scratch copies:
- Near-clean as expected. Real leftovers: ops comfy-table 7.1.4 -> 7.2.2 (cargo update -p comfy-table) removes crossterm 0.28 / rustix 0.38 / linux-raw-sys 0.4 duplicates; ops shlex 1 vs 2 (trivial).
- False positives, fixed in the skill: PROF-3 fired on target/ size that was stale accumulation (now --measure-cold only); TGT-2 had no file to modify (now report-only, with stale-share measurement); TEST-2 fired on dbsec verify although doctests run in pre-release and CI (now fires only when nothing runs doctests, and is a trade-off alone); DEP-1 filed upstream-bound duplicates (now filed only when an update removes them; count only distinct versions).
- Instruction defects fixed: `ops --dry-run run-before-push/commit` runs the gate for real; preflight vs untracked .backlog/; zero-dirty catch-up has no per-unit data; UNIT_DATA has no link section; sccache JSON field paths and 0/0 hit rate; nextest show-config builds; concurrent capped builds evade the load check (added pgrep); `task edit --notes` -> `--append-notes`.
- Still open: re-run the survey on ops and dbsec with the fixed skill to confirm it now comes back with only the real leftovers.

2026-09-27: skills moved onto ops 0.70.0 (explain, about machine/crates/dependencies --duplicates, backlog --unless-exists, lock, wave claim/park/overlap/create, backlog commit, clippy-findings).

Re-eval of rust-make-build-fast (default mode) on ops @ d3a50ef7 and dbsec @ bdd1afc, repos untouched, filing in scratch mirrors:
- ops: one finding, BF-DEP-1 comfy-table 7.1.4 (update removes crossterm 0.28 / rustix 0.38 / linux-raw-sys 0.4) -- REAL leftover, still unfixed. Everything else clean.
- dbsec: no findings. All four earlier false positives (PROF-3, TGT-2 filed, TEST-2, DEP-1 upstream-bound) are gone.
- --unless-exists: second create printed `Exists TASK-0001`.
- 13 instruction/ops-shape mismatches fixed in the skill: explain plan tree (stage vs sequence), hooks explainable when defined as composites, step `id`/origin object, duplicates JSON path, self-pulled and platform-only duplicates, major-bump candidates report-only, `du` per subdir, DEP-1 --modified-file Cargo.lock, DEP severity vs unmeasured default, incremental evidence from not_cached, null Rust counts, matrix vars unexpanded, "No findings filed" line, rc capture.

Delivered in PR #20 (commit 1bff9e4, feat(rust-make-build-fast)); later moved onto ops 0.72.0 in the same PR.

<!-- SECTION:NOTES:END -->
