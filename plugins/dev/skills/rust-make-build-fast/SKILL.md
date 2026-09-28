---
name: rust-make-build-fast
description: Surveys a Rust workspace's build cost without touching the tree, reading its profiles, cargo config, gates, nextest config and dependency graph, taking sccache stats and a warm cargo build --timings, and files one backlog task per finding, each with its measured cost, the date and machine load, and a safe or trade-off classification. A cold build is opt-in via --measure-cold, into a target directory on real disk, never tmpfs. Passing --apply writes the safe fixes into Cargo.toml profiles, .ops.toml gates and .config/nextest.toml; trade-offs such as dependency opt-level are never applied. Use when a Rust workspace's builds, tests or gates feel slow, or before tuning its profiles by hand.
allowed-tools: Read Edit Write Grep Glob Bash(git status:*) Bash(git rev-parse:*) Bash(git log:*) Bash(git show:*) Bash(cargo build:*) Bash(cargo metadata:*) Bash(cargo clippy:*) Bash(cargo doc:*) Bash(cargo nextest:*) Bash(cargo machete:*) Bash(cargo shear:*) Bash(cargo --version) Bash(ops --version) Bash(ops explain:*) Bash(ops about machine:*) Bash(ops about crates:*) Bash(ops about dependencies:*) Bash(ops backlog:*) Bash(jq:*) Bash(python3:*) Bash(du:*) Bash(date:*) Bash(mktemp:*) Bash(mkdir -p:*) Bash(rg:*)
license: Apache-2.0
---

# Make Build Fast

Survey a Rust workspace's build cost and file what it finds. Every finding is
backed by a **measurement**: a number, the date it was taken, and what the
machine was doing at the time. The output is one backlog task per finding,
each classified **safe** or **trade-off**, plus a report. With `--apply`, the
run also writes the safe fixes. Trade-offs are never applied.

This is `rust-make-clippy-pedantic`'s shape applied to build time, with two
differences:

1. **Findings are measurements, not yes/no.** A lint fires or it doesn't. A
   profile setting costs *some* seconds on *this* machine under *this* load,
   and the task has to say how many, when, and under what conditions.
2. **Some findings are decisions.** Dropping dependency `opt-level` speeds up
   the build and may slow down the tests. That finding is filed with both
   numbers and a recommendation, and `--apply` never writes it.

## Invocation

| Argument | Effect |
|----------|--------|
| *(none)* | Cheap survey. Reads configuration, runs fast probes and a warm `--timings` build, files findings, and **shows** the safe fixes without writing them |
| `--measure-cold` | Also runs the cold builds that trade-off findings need, into a target directory on real disk. Slow: each cold build costs the project's full build time |
| `--apply` | Also writes the safe fixes that have a template, then verifies them |

The flags can be combined. `--measure-cold --apply` measures first and applies
second, so the trade-off tasks carry both sides' numbers while `--apply` still
writes only the safe fixes.

## Purpose

- Verify the tree is clean, so findings are tied to a known commit
- Record the machine's state (cores, load, `jobs` cap, compiler wrapper, where
  `/tmp` and the target directory live), because that state decides whether any
  timing can be trusted
- Run every check in [checks.md](references/checks.md) at the cost its mode
  allows. The default mode never runs a cold build
- File one task per finding through `ops backlog task create --plain`, with
  the measured cost, the date, the load, and a safe or trade-off label
- Report what was measured, what was filed, and what `--apply` would write or
  did write

## Execution Contract (MUST follow)

You are running unattended, and nobody is watching to course-correct.

1. **The repository stays byte-identical, except under `--apply`.** Do not
   edit, stash, pull, `cargo update` or `cargo clean`. Pass `--locked` to every
   cargo command that resolves dependencies. The project's own `target/` is a
   cache that git ignores, so warm builds go there. Cold builds go to a scratch
   directory. Nothing else is written outside `.backlog/` (through the CLI) and
   scratch space.
2. **Never run a cold build without `--measure-cold`.** A cold event0 build
   took more than 30 minutes under load. A survey that costs that much stops
   getting run.
3. **Never apply a trade-off.** Not under `--apply`, and not because a
   measurement makes the answer look obvious. The task is where that decision
   gets made.
4. **Never commit, stage or push.** That applies to what `--apply` writes too.
5. **Abort on a dirty tree.** Print the blocking condition and stop.
6. **Findings are emitted only through `ops backlog task create --plain`.** A
   prose list instead of tasks is a failed run. The exceptions are ENV
   findings and TGT-2, which describe this machine and this checkout rather
   than the repository. They go in the report and are not filed
   ([checks.md](references/checks.md#environment--env-report-only)).
7. **Never ask for confirmation.** You are pre-authorized to file tasks.
8. **On tool failure, retry once, then report the specific error.** `ops`
   0.72.0 or newer is required: findings are filed through `ops backlog`, and
   the survey reads gate plans, machine state and duplicates through it. If it
   is missing or older, stop at preflight and report nothing as findings. A missing
   optional tool (`cargo machete`/`cargo shear`, `sccache`, `cargo nextest`)
   skips its checks. Name each skipped check in the report. Never install a
   tool.

## Process

### Step 1 — Preflight

```bash
git rev-parse --is-inside-work-tree                 # must be true
git status --porcelain -- . ':(exclude).backlog'    # must be EMPTY, untracked files included
git rev-parse --short HEAD                          # findings are pinned to this SHA
git rev-parse --abbrev-ref HEAD
cargo --version
ops --version                                       # must be 0.72.0 or newer
```

`.backlog/` is excluded because task files there are routine, and this run
writes to it anyway. Step 9 checks the tree against this same pathspec.

Do not fetch, pull or stash to make the tree clean. If `Cargo.lock` is missing,
or `--locked` refuses with `the lock file needs to be updated`, stop and report
it. Refreshing the lock is a change to the repository.

### Step 2 — Record the machine

Before any timing, run `ops about machine --json`. It returns every field of the
timing record in
[measurement.md](references/measurement.md#the-record-that-goes-with-every-timing),
including each cargo setting's source layer and the tmpfs status of `tmpdir` and
`targetDir`. Evaluate ENV-1 and ENV-2 now. A 16 GB tmpfs
`/tmp` or a `jobs = 2` cap changes what every number after this point means,
so say so at the top of the report.

If `buildProcesses` is not empty, or the 1-minute load is above half the core
count, keep going, but mark every timing taken under those conditions
**loaded**. Load alone misses a build capped at a low `jobs` count, which is
why the process list is checked too. Run the command again before each timing.

### Step 3 — Read the configuration

This step only reads files and runs commands that do not build:

- The root `Cargo.toml` profiles, and any `[profile]` table in a member
  manifest (PROF-1 to PROF-5)
- The cargo config files `ops about machine` listed in `cargo.configFiles`, for
  the comments and settings behind CACHE-1
- Gates: `ops explain <gate>… --json` for each composite the project runs
  regularly, plus `Makefile`/`justfile` and `.github/workflows/*.yml`. It returns
  the stages directly, and never executes a step
  ([checks.md](references/checks.md#test-runner-and-gates--test-gate))
  (TEST-*, GATE-*)
- `ops about crates --json` for the members (`manifestDir`, `inTree`), for
  PROF-5. A nested manifest with its own `[workspace]` is not a member
- `.config/nextest.toml` and `cargo nextest --version` (TEST-1, TEST-4)
- `ops about dependencies --duplicates --json` (DEP-1), and the transitive
  dependency count from `cargo metadata --locked --format-version 1` (PROF-1).
  `ops about dependencies` lists direct dependencies only
- `cargo machete` or `cargo shear`, if installed (DEP-2)
- `du` of `target/` and its subdirectories, `df` of its filesystem, and its
  stale share (TGT-2, report-only)

### Step 4 — Warm measurements

Take the first sccache snapshot, which is the `sccache` object of
`ops about machine --json` (present when sccache is the wrapper). Then run the
per-edit gate's build command twice with `--timings` into the project's
`target/`: the catch-up run, then the no-op run. Follow
[measurement.md](references/measurement.md#warm-build) for how to read them,
and never treat the catch-up time as a finding. If the catch-up compiled
nothing, per-unit costs are **unmeasured**. Do not force a rebuild. Take the
second sccache snapshot and compute the difference (CACHE-1). With fewer than
20 Rust compilations in the delta, CACHE-1 is not evaluated. **Never** run
`--zero-stats`.

Then run the ping-pong probe for each pair of regularly run cargo invocations
that share a target directory with different features or profiles
([measurement.md](references/measurement.md#ping-pong-probe)): TGT-1, GATE-3.

### Step 5 — Cold measurements (`--measure-cold` only)

Without the flag, skip this step. Every check that needs it records its cost
as **unmeasured — run with `--measure-cold`**.

With the flag, first list the cold builds the pending findings need. Only
checks that fired need one, and each variant needs its own. Print how many
there are, then run them following
[measurement.md](references/measurement.md#--measure-cold-the-opt-in-cold-measurement):

- The target directory goes under `${XDG_CACHE_HOME:-$HOME/.cache}`, and you
  check that it is not tmpfs before using it:
  `CARGO_TARGET_DIR=<dir> ops about machine --json` reports `targetDir.tmpfs`
  and `availableBytes` for that path. Never use `/tmp`
- The compiler wrapper is off. The user's `jobs` setting stays on and is
  recorded
- Variants are `--config` overrides, never file edits
- The load is recorded at the start and end of every build
- The scratch directories are deleted at the end, on success or failure

### Step 6 — Classify

For each check that fired, fill in:

- **Check ID** from [checks.md](references/checks.md), and the **subject**:
  the profile, gate, step, crate or directory it concerns
- **Class**: **safe** or **trade-off**, by the rule in the check's entry. When
  in doubt, trade-off
- **Cost**: each measured number with its timing record, or **unmeasured** and
  the flag that would measure it
- **For a trade-off**, both sides: build cost and what gets worse. Leave a
  side unmeasured only when its mode wasn't requested, and label the task
  `needs-measurement` in that case
- **Apply**: the template name from
  [apply-templates.md](references/apply-templates.md), `manual`, or `never`
  (every trade-off)
- **Severity**, from the [Severity Scale](#severity-scale)

Drop differences below the noise floor in
[measurement.md](references/measurement.md#noise): under 10% or under two
seconds. They are not findings.

### Step 7 — Deduplicate, then file one task per finding

A finding's identity is its check ID plus its subject: `BF-PROF-1:profile.dev.package."*"`,
or `BF-GATE-3:verify/clippy-default`. Pass it as `--unless-exists`. ops stores it
on the task and, when an open task already carries it, creates nothing and
prints `Exists <id>`. The check and the write happen under the store's
allocation lock, so two concurrent runs cannot both file. A key whose only
task is `Done` files again. Mention the old task in the new description.

On `Exists <id>`, the finding is not new, but its measurement may be. Append
the new timing record and numbers with `ops backlog task edit <id> --append-notes`, so
the task keeps its history of numbers.

Use a `"$(cat <<'EOF' … EOF)"` heredoc for the description. Do not use
`$'…'` quoting, which triggers a safety prompt on every call. Keep the `'EOF'`
quoted, because the body is full of backticks that an unquoted heredoc would
execute. Write the measured values into the text literally. Do not
interpolate shell variables.

```bash
ops backlog task create "BF-<CHECK-ID>: <short description of the subject>" \
  -d "$(cat <<'EOF'
**Check**: `BF-<CHECK-ID>` — <check name> (**<safe|trade-off>**)

**Where**: `<file>` `<table, gate or step>`

**Evidence**: <the setting or output, quoted verbatim>

**Measured** <YYYY-MM-DD> · <cores> cores, jobs=<n> · load <start>→<end> · <wrapper> · <target dir fstype> · <cargo version>
- <metric>: <value> (`<exact command>`)

**Trade-off** (trade-off only):
| | Project setting | Alternative |
|-|-----------------|-------------|
| Build | <value or unmeasured> | <value or unmeasured> |
| <tests / debugging / coverage> | <value or unmeasured> | <value or unmeasured> |

**Recommendation**: <what to do and why, given the numbers>

**Apply**: <template name | manual | never — trade-off>

**Commit**: <short SHA>
EOF
)" \
  -s "Triage" \
  -l "rust-make-build-fast,build-fast,<safe|trade-off>,<category>" \
  --priority <high|medium|low> \
  --modified-file "<file the fix edits>" \
  --ac "<the measurable outcome, e.g. a no-op verify under N seconds on the recorded machine>" \
  --ac "Behaviour is unchanged: the gates that passed before still pass" \
  --unless-exists "BF-<CHECK-ID>:<subject>" \
  --plain
```

Non-negotiables:

- **Labels**: every task carries `build-fast`, exactly one of `safe` or
  `trade-off`, and its category in lower case (`prof`, `test`, `gate`, `tgt`,
  `dep`, `cache`). Add `needs-measurement` to a trade-off with an unmeasured
  side.
- **`--modified-file`**: at least one, repo-root-relative, naming the file the
  fix edits (`Cargo.toml`, `Cargo.lock` for DEP-1, `.ops.toml`,
  `.config/nextest.toml`, a member manifest, a script). `code-review-triage` computes wave scope from it.
- **The date and the load go into every task that has a number.** A timing
  without them cannot be compared with the next one.
- **Status is always `Triage`.**

### Step 8 — Report

Print, in this order:

1. **What ran**: SHA and branch, toolchain, mode flags, and the machine record
   including ENV-1, ENV-2 and any other build seen running. Mark as **loaded**
   every timing taken above half the core count or next to another build.
2. **Where the time goes**: the catch-up and no-op wall times, the ten slowest
   units from `--timings` (or "up to date, unmeasured"), the sccache hit rate
   (or "not evaluated"), TGT-2's size, stale share and suggested clean-up, and
   the real duplicates, with the upstream-bound ones listed but not filed.
3. **What was filed**: a table of check ID, subject, class, cost and apply
   status; list existing tasks (`Exists <id>`) and checks skipped for a missing tool
   separately. If nothing fired, say `No findings filed`.
4. **Trade-offs**: for each, both numbers and the recommendation in a sentence
   or two. This is the part a human has to act on.
5. **What `--apply` would write**, per file as a fenced block, when `--apply`
   was not passed. Otherwise, what it wrote and how it was verified (Step 9).
6. **Next step**: `code-review-triage` to group the `Triage` tasks, and
   `--measure-cold` if any trade-off is labelled `needs-measurement`.

### Step 9 — Apply the safe fixes (`--apply`)

**Without `--apply`, write nothing.** Step 8 already showed each change. Say
that nothing was written.

**With `--apply`:**

1. **Check that the tree has not moved.** `.backlog/` is dirty by now, so leave
   it out:

   ```bash
   git status --porcelain -- . ':(exclude).backlog'   # must be EMPTY
   git rev-parse --short HEAD                          # must equal the Step 1 SHA
   ```

2. **Apply each safe finding that has a template**, one at a time, as
   [apply-templates.md](references/apply-templates.md) specifies. Leave trade-offs
   and `manual` findings alone.
3. **Verify each file** with the checks at the end of that reference, then run
   each edited gate once. If a gate fails because of an edit, revert that one
   edit, record why on its task, and continue with the rest.
4. **Compare against the recorded cost.** A safe fix that made nothing faster
   was misclassified or was noise. Say which.
5. **Report the files touched and stop.** The tree is dirty by design, and
   nothing is committed.

## Finding ID Prefixes

| Prefix | Meaning |
|--------|---------|
| `BF-PROF-<n>` | Cargo profile settings |
| `BF-TEST-<n>` | Test runner and doctest handling |
| `BF-GATE-<n>` | How gates are composed and staged |
| `BF-TGT-<n>` | Target directory sharing. TGT-2, the size of `target/`, is report-only |
| `BF-DEP-<n>` | Dependency graph: duplicates, unused crates |
| `BF-CACHE-<n>` | Compiler cache effectiveness |
| `ENV-<n>` | The machine, not the repository. Report-only, never filed |

## Severity Scale

A build cost's weight is its size multiplied by how often it is paid. For a
DEP finding, use the "cold build" row, and treat five or more crates removed
as the 10–60s column.

| Paid | ≥ 60s | 10–60s | < 10s |
|------|------------------|--------|-------|
| On every edit (per-edit gate, no-op rebuild) | high | high | medium |
| On every push or CI run | high | medium | low |
| On a cold build only (new worktree, `cargo update`) | medium | low | low |

Outside DEP findings, which follow the rule above, a finding whose cost is
**unmeasured** is `medium`. Say in the task that the
priority is a placeholder until a measurement exists. A trade-off keeps the
priority of its build-side cost. The recommendation decides what to do about
it, not the priority.

## Scan Checklist

| Signal | Check |
|--------|-------|
| `[profile.dev.package."*"] opt-level >= 1` | PROF-1 (trade-off) |
| `[profile.test]` sets something `dev` does not | PROF-2 |
| Full debuginfo on dependencies (`--measure-cold` only) | PROF-3 (trade-off) |
| `lto`, `codegen-units = 1`, workspace `opt-level >= 2` in `dev`/`test` | PROF-4 (trade-off) |
| `[profile]` in a member manifest | PROF-5 |
| A regular gate runs `cargo test` / `test` | TEST-1 |
| No gate and no CI job runs doctests | TEST-2 (trade-off on its own) |
| `cargo test -- --ignored` and ` ```ignore ` blocks | TEST-3 |
| `LEAK` in a nextest run, default `leak-timeout` | TEST-4 |
| Rewriters and readers in one stage, or a flat per-edit gate | GATE-1 |
| Test step in the same stage as `build` over the same `target/` | GATE-2 |
| A different feature or profile fingerprint in the per-edit gate | GATE-3 |
| Ping-pong probe: A rebuilds after B | TGT-1 |
| `target/` > 20 GB, or > 30% of free space | TGT-2 (report-only) |
| `ops about dependencies --duplicates`: an entry with `updateRemovesDuplicate: true` | DEP-1 |
| `cargo machete` / `cargo shear` reports, confirmed by `rg` | DEP-2 |
| sccache wrapper, Rust hit rate < 50% over ≥ 20 compilations | CACHE-1 (trade-off) |
| `ops about machine`: `tmpdir.tmpfs` or `targetDir.tmpfs` | ENV-1 (report-only) |
| `jobs`, wrapper, linker or rustflags in user-level cargo config | ENV-2 (report-only) |

## Concurrency

- **One run per machine at a time.** Two surveys running at once load each
  other's timings, and every number both of them record is then **loaded**.
- The warm builds take the project's `target/` lock. A developer building in
  the same checkout waits, and so does the survey.
- Filing is idempotent: `--unless-exists` is checked under the backlog's
  allocation lock, so two runs over one repository file each finding once.
  Their timings still load each other, which is the reason for the first rule.

## References

- [Checks catalog](references/checks.md) — every check: its signal, how it is measured, its classification, and where each came from
- [Measurement method](references/measurement.md) — the timing record, warm and cold measurements, the ping-pong probe, noise
- [Apply templates](references/apply-templates.md) — what `--apply` writes to `Cargo.toml`, `.ops.toml` and `.config/nextest.toml`, and how each write is verified
- [OpenAI agent metadata](assets/openai.yaml) — optional agent configuration for compatible runtimes
- `rust-make-clippy-pedantic` — the sibling this skill is modelled on
- `code-review-triage` — groups the `Triage` tasks this skill files into waves
