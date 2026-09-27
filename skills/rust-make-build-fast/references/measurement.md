# Measurement Method

How the survey times things, and what it records alongside every timing. A
build timing is slow to take and noisy to read. A number with no date, no
machine state and no command attached cannot be compared with anything, so the
rules below are about making every number comparable.

## The record that goes with every timing

Every timing in a task or in the report carries this record. Most of it comes
from one `ops about machine --json` call, taken before the timing and again
after it for the load. That command is portable to macOS, and it resolves
`jobs`, the wrapper and the target dir across every cargo config layer and the
environment, naming the source of each:

| Field | Source |
|-------|--------|
| Date | `date -u +%F` |
| Command | The exact cargo invocation, including any `--config` override |
| Wall time | `date +%s.%N` before and after. Don't use `time`: its output format differs between shells. Capture the build's exit code right after it (`cmd; rc=$?`), before the second `date` overwrites `$?` |
| Load | `loadAverage[0]` at the start and at the end |
| Cores | `cores` |
| Jobs | `cargo.jobs.value`, or `default` when absent, plus `cargo.jobs.source` |
| Wrapper | `cargo.rustcWrapper.value`, or `none` |
| Incremental | `cargo.incremental.value`, or the `dev` entry of `cargo.incrementalProfiles` when it is `profile` |
| Target dir | `targetDir.path` and `targetDir.fsType` |
| Toolchain | `cargo --version` |

Write it in one line, for example:
`2026-09-26 · 16 cores, jobs=2 · load 2.9→7.4 · sccache on · /home ext4 · cargo 1.98.0`.

**Other builds decide it before load does.** Before every timing, check
`buildProcesses` in the same output, at a moment when none of your own builds
is running.

Any other build running means every timing you take is **loaded**, even when
the load average looks low. A build capped at `jobs=2` barely moves the load
on 16 cores. That is exactly how the ops/dbsec eval ran alongside another
session's cold event0 benchmark without its load check ever tripping. Wait
for the other build to finish, or mark the timings.

**Load decides whether a number can be trusted.** If the 1-minute load at the
start is above half the core count, mark the timing **loaded**. It still goes
in the task, but it cannot back a trade-off recommendation. Wait for the load
to drop, then take the measurement again, or say in the task that it is
unreliable. Do not scale a loaded number by some correction factor. There is no
honest factor to use.

## Default mode: cheap probes only

The default mode reads files and runs commands that finish quickly on a warm
target directory. It **never runs a cold build**. A cold event0 build took more
than 30 minutes under load, and a survey nobody can afford to run gets skipped.

| Probe | Command | Feeds |
|-------|---------|-------|
| Machine | `ops about machine --json` | the timing record, ENV-1, ENV-2, CACHE-1 |
| Profiles, config | Read the root `Cargo.toml` and the files in `cargo.configFiles` | PROF-*, CACHE-1 |
| Gates | `ops explain <gate>… --json`, `Makefile`/`justfile`, `.github/workflows/*.yml` | TEST-*, GATE-* |
| nextest | `.config/nextest.toml`, `cargo nextest --version` | TEST-1, TEST-4 |
| Members | `ops about crates --json` | PROF-5 |
| Graph | `ops about dependencies --duplicates --json`; `cargo metadata --locked --format-version 1` for the transitive count | DEP-1, PROF-1 |
| Unused deps | `cargo machete` or `cargo shear`, if installed | DEP-2 |
| Disk | `du -sh target`, then `du -sh target/*/` separately, `targetDir.availableBytes`, the stale share (TGT-2) | TGT-2 (report-only) |
| Cache | The `sccache` object of `ops about machine --json`, before and after the warm build | CACHE-1 |
| Warm build | See below | PROF-4, GATE-3, no-op rebuild |
| Ping-pong | See below | TGT-1, GATE-3 |

### Warm build

Run it in the project's own `target/`. That directory is a cache that git
ignores, so building into it leaves the repository byte-identical, and a warm
number has to come from a warm directory. Run the command the per-edit gate
runs (usually `cargo build --workspace --all-features --all-targets --locked`),
with `--timings` added, **twice**:

1. The **catch-up** run brings `target/` up to date with HEAD. Record its wall
   time and the dirty/total unit counts from the report. This is not a finding.
   In ops, a checkout a few commits behind took 134s to rebuild 63 of 418
   units, and that number describes when someone last built, not the
   workspace.
2. The **no-op** run should finish in a second or two. If it rebuilds
   anything, something invalidates the build on every run: a build script
   without `rerun-if-changed`, a generated file, or an environment variable.
   Report that.

**If the catch-up run compiles nothing** (0 dirty units, which is normal for a
checkout someone built recently), no unit has a timing. Every unit reads
0.0s, and there is no list of slowest units or per-unit cost for this run.
Record that as **unmeasured — target was up to date**, and let every
unit-level cost wait for `--measure-cold`. Do not force a rebuild by touching a
source file, because that modifies the tree. Do not quote an older report
left in `target/cargo-timings/` as this run's measurement either: it was taken
at another commit, under another load. You may mention it in the report with
its own timestamp and dirty-unit count, labelled as historical.

When the catch-up did compile something, read the per-unit timings from its
report. The HTML embeds them as a JSON array:

```bash
python3 - "$(ls -t target/cargo-timings/cargo-timing-*.html | head -1)" <<'EOF'
import json, re, sys
html = open(sys.argv[1]).read()
units = json.loads(re.search(r'const UNIT_DATA = (\[.*?\]);\n', html, re.S).group(1))
for u in sorted(units, key=lambda u: -u["duration"])[:15]:
    print(f'{u["duration"]:7.1f}s  {u["name"]} {u["version"]} {u["target"].strip()}')
EOF
```

As of cargo 1.98, the fields you can use are:

- `name`, `version` and `duration` in seconds.
- `target`, a display string with quotes and a `(test)` suffix, such as
  `ops_core "lib" (test)`. Strip it before printing.
- `sections`, which is `null` for most units and otherwise holds only
  `frontend` and `codegen`. **There is no link section**, so link time cannot
  be read from this report.

`mode` is always `todo` or `run-custom-build`, so it is useless. The format is
internal to Cargo. If the regex stops matching after a toolchain upgrade,
report the wall times alone and say the per-unit breakdown was unavailable.
Do not guess.

### Ping-pong probe

For two cargo invocations A and B that share a target directory (the two doc
builds, `clippy` and `clippy-default`, `build` and a `--release` lint):

1. Run A, so it is warm.
2. Run B.
3. Run A again, and time it.

If step 3 is close to a no-op, the two coexist. If it rebuilds, B evicted A's
output, and the cost of step 3 is paid on every alternation: that is TGT-1.
Step 2's time tells you whether B has a GATE-3 problem: the first time B runs
it pays for a full second fingerprint.

## `--measure-cold`: the opt-in cold measurement

This is the only mode that runs a cold build, and it runs one only for the
checks that need it: PROF-1 to PROF-4 and TEST-1. PROF-3 is evaluated nowhere
else. List those checks first,
state in the report how many cold builds they will take, and then run them.
Each one costs as much as the project's full cold build.

### Cold target directory

**Never under `/tmp` and never on tmpfs.** `mktemp -d` defaults to `TMPDIR`,
which is often a tmpfs sized to a fraction of RAM. A cold all-features build
filled event0's 16 GB `/tmp`, and cargo exited 101 without printing a compile
error. Use a directory on real disk, and check it before using it:

```bash
COLD_BASE="${XDG_CACHE_HOME:-$HOME/.cache}/rust-make-build-fast"
mkdir -p "$COLD_BASE"
COLD="$(mktemp -d -p "$COLD_BASE")"
CARGO_TARGET_DIR="$COLD" ops about machine --json | jq '.targetDir'
# .tmpfs must be false; .availableBytes must exceed the fresh target/debug size, with margin
```

`ops about machine` reports the filesystem of whatever `CARGO_TARGET_DIR`
points at, on Linux and macOS alike. State `fsType` in the timing record.
Delete `$COLD` when the run
ends, whether it succeeded or failed. It is tens of gigabytes that belong to
nobody.

### Cold means cold

- **Turn the compiler cache off**: set `RUSTC_WRAPPER=` and
  `CARGO_BUILD_RUSTC_WRAPPER=` to empty. A "cold" build with a warm sccache
  measures the cache, not the compiler. If the user asks for the cached number
  as well, take it as a separate labelled measurement.
- **Keep the user's `jobs` setting** and record it. The point is to measure
  what the user will experience. If the cap distorts the result (ENV-2), say
  so in the report. Don't remove the cap on your own initiative.
- **Measure variants with `--config`, never by editing a file.** For example:
  `cargo build … --config 'profile.dev.package."*".opt-level=0'`. The
  repository stays byte-identical, and the override is written in the command
  field of the timing record, where it can be reproduced exactly.
- **Each variant starts from an empty target directory.** Give each variant
  its own `mktemp -d -p "$COLD_BASE"`. A variant that reuses the previous
  variant's artifacts is not cold.

### Both sides of a trade-off

A trade-off finding needs two measurements, one for each side:

| Check | Build side | Other side |
|-------|-----------|------------|
| PROF-1 | Cold build, project setting vs `opt-level=0` for dependencies | Test suite wall time under each build (`cargo nextest run`, already built) |
| PROF-2 (opt-level) | `nextest run --no-run` after a warm `build`, project vs aligned | Test suite wall time under each |
| PROF-3 | Cold build wall time and `du` of `target/`, full vs `line-tables-only` | Not measurable; name what the debugger loses |
| PROF-4 | Warm rebuild of one workspace crate, project vs dev defaults | Test suite wall time under each |
| CACHE-1 | Hit rate before and after, from sccache stats | Not measured locally. The cost is incremental rebuilds, which the survey does not touch the source to trigger |

Put the numbers in the task as a two-column comparison under the same timing
record. If one side is missing because the mode was not requested, write
**unmeasured** and say which flag measures it. Don't fill it with an estimate.

### Noise

Take a cold build once. They are too slow to repeat, which is why the load
record matters. Take a warm timing of a few seconds three times and report the
median. Differences smaller than 10% of the larger number, or smaller than two
seconds, are noise: do not file a finding on them.
