# Build-Cost Checks Catalog

Every check the survey runs. Each one lists the signal that triggers it, how
the default mode gathers the evidence, what `--measure-cold` adds, its
classification, and whether `--apply` has a template for it.

The checks come from three workspaces tuned by hand — dbsec, ops and event0 —
and the case each one comes from is named. Do not add checks here on reasoning
alone: a check earns its place when it has cost a real workspace real time.

## Classification

| Class | Meaning | `--apply` |
|-------|---------|-----------|
| **safe** | Nothing gets worse except that someone has to do the work. Runtime behaviour, runtime speed, debuggability and gate coverage stay the same | Written if the check has a template in [apply-templates.md](apply-templates.md); otherwise filed as manual work |
| **trade-off** | The fix makes something else worse: slower tests, a weaker debugger, less gate coverage, slower local rebuilds. The fix is a decision someone has to make, and the task carries the evidence for it | **Never** written, not even under `--apply` |

Some checks are trade-offs in one form and safe in another (PROF-2, GATE-3). The
entry says which form is which. When a finding could go either way, call it a
**trade-off**. Wrongly calling something safe means `--apply` quietly makes a
workspace's tests slower. Wrongly calling it a trade-off only means a human reads
one more task.

## Profiles — `PROF`

Read the root `Cargo.toml`'s `[profile.*]` tables. Profiles are
workspace-root-only, so a `[profile]` table in a member manifest is ignored,
and Cargo warns about it. That warning is a finding of its own (PROF-5).

### PROF-1 — Dependencies optimized in the dev profile

**Signal**: `[profile.dev.package."*"]` (or `[profile.test.package."*"]`) sets
`opt-level` to 1 or higher.

**Why it costs**: every non-workspace crate in the graph compiles with
optimizations. event0 had `opt-level = 2` on about 417 dependencies. Every cold
build, every new worktree and every `cargo update` pays for it again. A
wave-runner worktree is a cold build too.

**Default mode**: record the setting and the dependency count
(`cargo metadata --locked --format-version 1 | jq '[.packages[] | select(.source != null)] | length'`).
Cost: **unmeasured**.

**`--measure-cold`**: two cold builds of the same command. One uses the
project's settings. The other overrides the setting from the command line:
`--config 'profile.dev.package."*".opt-level=0'`, which changes no file. Then run
the test suite once under each build. That gives both sides of the trade-off.

**Class**: **trade-off**, always. The optimization exists to make tests fast.
Crypto, compression and parsers can run several times slower at `opt-level = 0`,
and a slower test suite may cost more than the compile time saved. The
recommendation depends on the two numbers, so state both. Often the answer is
somewhere in between: optimize only the few heavy dependencies with
`[profile.dev.package.<name>]` and leave the rest at 0.

### PROF-2 — Test profile diverges from dev

**Signal**: `[profile.test]` sets something that changes code generation and
differs from `[profile.dev]`: `opt-level`, `debug`, `codegen-units`,
`overflow-checks`, `debug-assertions`, `lto`, `panic`, or a `package` override.

**Why it costs**: `cargo build`, `cargo check` and `cargo clippy` use `dev`,
while `cargo test` and `cargo nextest run` use `test`. When the two differ, the
same crates compile twice under two fingerprints, so a gate that runs `build`
and then `next` compiles the workspace twice. In event0, `profile.test` had
`opt-level = 1` and dev had 0.

**Default mode**: diff the two tables. Settings that `test` inherits from `dev`
are not divergence. Cost: **unmeasured**.

**`--measure-cold`**: with a warm `build`, time `cargo nextest run --no-run`.
Do this once with the project's settings and once with each divergent key
overridden back to its dev value, for example
`--config 'profile.test.opt-level=0'`. The difference is the second compile.

**Class**: it depends on the key, because most of these keys change what the
tests do, not just how long they take to compile.

| Divergent key | Class | Why |
|---------------|-------|-----|
| `codegen-units`, `incremental`, `split-debuginfo` | **safe** | Only compile time and artifact layout change. `--apply` removes the key (template `test-profile-align`) |
| `opt-level`, `lto`, or a `package` override setting either | **trade-off** | The tests run the optimized code, as in PROF-1 |
| `overflow-checks`, `debug-assertions`, `panic` | **trade-off** | Test **behaviour** changes. A test that relies on an overflow panic or a `debug_assert!` passes under one setting and fails under the other |
| `debug`, `strip` | **trade-off** | Debuggability changes, as in PROF-3. Removing a test-profile `strip` override makes tests inherit dev's stripping, and backtraces can lose their symbols |

A key not in this table is a **trade-off** until someone adds it here with a
reason. Keys that only restate what `dev` already says, such as
`incremental = true` when dev is incremental too, cost nothing. Note them in
the report and do not file them.

### PROF-3 — Full debuginfo on dependencies

**Signal**: the dev profile's `debug` is `true`, `2` or `"full"`, the default
when unset, and nothing lowers it for dependencies with
`[profile.dev.package."*"] debug = …`. On its own this is Cargo's default, not
a defect, so this check is **evaluated only under `--measure-cold`**, and it
fires only when the measured difference clears the noise floor.

**Do not fire it from the size of `target/`.** A long-lived checkout's
`target/` is mostly stale artifacts from earlier commits. In the ops and dbsec
evals, `target/debug/deps` held 20–31 copies of the main library's rlib and
7–10 GB of files older than a week. Warm-only evidence cannot separate
debuginfo from that accumulation, and the eval fired PROF-3 as a false positive
in both repos.

**Why it costs**: full debuginfo is the largest part of a fresh dev build's
output, and linking has to process all of it. It contributed to event0's 60 GB
`target/`.

**`--measure-cold`**: two cold builds, one as configured and one with
`--config 'profile.dev.package."*".debug="line-tables-only"'`. Compare the wall
time and the size of the fresh target directory. A cold directory holds no
stale artifacts, so its size is an honest measure.

**Class**: **trade-off**. Backtraces keep file and line numbers, but a debugger
can no longer inspect variables inside dependencies.

### PROF-4 — Release-grade settings in dev or test

**Signal**: `lto` other than `false`/`"off"`, `codegen-units = 1`, or
`opt-level >= 2` for workspace crates in `dev` or `test`.

**Why it costs**: these settings add the most time to compiling the crates you
edit, so every edit-and-compile cycle pays for them.

**Default mode**: record the settings. Cost: warm `--timings` of the workspace
units when the target directory is already up to date, otherwise
**unmeasured**.

**Class**: **trade-off**, because it changes how fast the code under test runs.

### PROF-5 — Ignored profile tables in member manifests

**Signal**: a member `Cargo.toml` has a `[profile.*]` table. Cargo prints
`profiles for the non root package will be ignored`. Take membership from
`ops about crates --json` (`inTree` members and their `manifestDir`), not from a grep for `^\[profile`. A
manifest that declares its own `[workspace]`, such as dbsec's `fuzz/`, is a
separate root, and its profiles do apply.

**Why it costs**: it costs no build time. It is filed because the author
believes a setting is in effect when it is not, and every timing gathered while
tuning the workspace rests on that wrong belief.

**Class**: **safe**, and manual: move the table to the root manifest or delete
it. Which one is right depends on what the author intended, which the survey
cannot know.

## Test runner and gates — `TEST`, `GATE`

Gates live in `.ops.toml`, where the `ops` stack defaults apply; in `Makefile`,
`justfile` or `xtask`; and in CI workflows. For `ops`, read the effective plan
with `ops explain <gate>… --json`. It resolves the gate exactly as running it
would, and it never executes a step. The output has:

- `commands[].plan`: a tree. A node with `type: "stage"` is a parallel composite, and
  its `stages[]` each list `steps` and say whether they run `concurrent`ly. A node with
  `type: "sequence"` is a sequential composite (`qax`, a hook composite): it has no
  `stages`, only `children[]`, each a plan node of its own. Walk the tree; a flat
  `.plan.stages` path returns `null` for a sequence. The stages already account for
  `exclusive` barriers, stack defaults, `[extend.*]` and `clone` inheritance, so read
  them as given.
- `steps[]`, keyed by `id`: each step's `program`, `args`, `display`, `env`,
  `exclusive` and `origin`, an object `{source, extended, cloneOf?,
  exclusiveOverridden?}` where `source` is `stack`, `config`, `clone`, `extension`
  or `builtin`.
- `composites[]`: each composite's `parallel`, `failFast`, member `commands` and
  `origin`.

A `matrix` step keeps its template in `args` and `display` (`${matrix.crate}`), and lists
the expanded commands under `matrix.cells[]`, one per cell, each with its own `args`,
`env` and `id`. Read the cells, not the template.

A step's `env.CARGO_TARGET_DIR` tells you which target directory it uses, for
GATE-2, GATE-3 and TGT-1. A step with no such entry shares the project's
`target/`.

The pre-commit and pre-push hooks run the `run-before-commit` / `run-before-push`
composites that `.ops.toml` defines (for example `commands = ["qax", "clippy-default"]`).
`ops explain run-before-push --json` resolves them like any other composite, and never
runs them. A project that defines no such composite has only the built-in hook
installer under that name, and `ops explain` reports `unknown command`: it has no
hook gate to survey.

### TEST-1 — `cargo test` where nextest would do

**Signal**: a gate that someone runs regularly (the per-edit gate, the
pre-push gate, CI) runs `cargo test`, or the `ops` stack's `test` step, and not
`cargo nextest run`. In event0, `qa` ran `test` and `test-ignored`.

**Why it costs**: libtest runs the test binaries one after another and the
tests inside each binary on threads. nextest runs every test as its own
process, all at once across binaries, so it does not wait on the slowest
binary.

**Default mode**: check that `cargo nextest --version` works, and record which
gate runs which runner. Then time the suite under each runner with the
[runner comparison](measurement.md#runner-comparison), which needs no cold
build when the warm build already produced the test binaries. On dbsec, three
runs of each took under a minute in total: `cargo test` 9.5s, nextest 6.9s
(medians). Cost: the difference between the two medians. A difference inside
the [noise](measurement.md#noise) band is not a finding: report both numbers
and file nothing.

When the comparison's conditions do not hold, the cost is **unmeasured**, and
the task says which condition failed.

**`--measure-cold`**: runs the same comparison when the test binaries need a
build first, or when the suite ran past the default-mode deadline. The build
and the unbounded run are what the flag pays for.

**Class**: **safe**. `--apply` uses template `gate-nextest`, which swaps the
step for the stack's `next` (or `next-ignored`). When the gate is the stack's own
composite and `.ops.toml` only extends it, the swap has to
[redefine the gate](apply-templates.md#a-gate-the-stack-owns), and the task
says so. Doctests are the one thing
nextest does not run, so the same edit has to handle TEST-2. Tests that share
process-global state can break when each runs in its own process. `--apply`
therefore runs the new gate once, and if it fails where the old runner passed,
it reverts that one edit and records the failure on the task.

### TEST-2 — Doctests run nowhere

nextest does not run doctests, so swapping `cargo test` for nextest drops
them unless something else runs them. This check has two parts.

**As part of TEST-1**, it is not filed separately. The `gate-nextest`
template adds `test-doc` beside `next` whenever the step it replaces ran
doctests. Plain `cargo test` without `--lib`/`--tests` filters does run them.
Coverage stays the same, so this part is safe.

**On its own**, it fires only when **no** gate and **no** CI job runs
doctests: no `cargo test --doc`, no `test-doc`, and no unfiltered `cargo test`
anywhere. A per-edit gate that runs nextest while pre-push, release or CI runs
the doctests is working as designed. In the eval, dbsec's `verify` fell into
this case, since its doctests run in `pre-release` and in CI, and filing it
was a false positive.

**Class**: when it fires on its own, it is a **trade-off**. Adding doctests to
a gate adds compile time to it, in exchange for coverage. It is never applied.

### TEST-3 — `cargo test -- --ignored` also runs ignored doctests

**Signal**: a gate runs `cargo test … -- --ignored` (the stack's
`test-ignored`) without `--lib --bins --tests`, and the workspace has doc
examples marked ` ```ignore `. Find them with
`rg -n '^\s*//[/!]\s*```ignore' --glob '*.rs'`.

**Why it costs**: `--ignored` turns ignored doctests back on. A block marked
` ```ignore ` is usually not meant to compile, so it fails. Without
`--no-fail-fast`, `cargo test` also stops at the first test binary that fails,
so every crate after that one goes unchecked. event0 lost the second half of
its ignored suite this way.

**Class**: **safe**. `--apply` uses template `gate-nextest` and swaps to
`next-ignored`, which never runs doctests.

### TEST-4 — nextest leak detection flagged under contention

**Signal**: a nextest run the survey saw, or a CI log someone pasted, reports
`LEAK` for a test that starts no subprocess, and `ops init --rust --check`
reports `leak-timeout` drift in `.config/nextest.toml` (typically the 100ms
default). File this only when a leak was actually
seen. A default setting alone is not a finding.

**Why it costs**: a flagged run waits out the timeout, and under load it fails
tests that are fine. dbsec saw it in about one full-workspace run in three at
`--test-threads=16` on 12 cores, and the flagged test changed from run to run.

**Class**: **safe**. `--apply` uses template `nextest-leak-timeout`, which writes
the Rust foundation's value from `ops init --rust` (2s as of ops 0.74.0).
Leak detection stays on, and a run with no leak pays nothing, because the wait
ends when the output reaches EOF, not at the timeout.

### GATE-1 — Per-edit gate not staged

**Signal**: the per-edit gate (`verify` in `ops`) either runs file-rewriting
steps (`fmt`, whitespace and EOF fixers) in the same stage as steps that read
those files, or runs every step one after another when the read-only steps
could run together. In ops, `verify` became staged in commit 5adb6be5.

**Why it costs**: a rewriter that runs next to a reader either races it or
forces a second run. A fully sequential gate adds up every step's wall time.

**Default mode**: rebuild the stages as described above. Cost: from a warm run
of the gate, compare the sum of the step times with the longest step in each
stage.

**Class**: **safe**. `--apply` uses template `gate-staged`: drop any
`[commands.verify]` redefinition in favour of `[extend.verify]`, so the stack's
staged default applies and the extra steps are added after it.

### GATE-2 — Test step races the build for the cargo lock

**Signal**: in a parallel gate, a test step (`next`, `test`) is in the same
stage as `build`, `clippy` or `doc`, and they share a target directory.

**Why it costs**: only one process can hold the lock on a target directory, so
the "parallel" steps queue behind each other anyway. Worse, the test step may
take the lock first and compile the test targets under the `test` profile,
while `build` then waits and gains nothing from them. dbsec avoided this by
making the step before `next` exclusive, which puts a stage barrier there:
`next` starts after `build` has finished and reuses its artifacts.

**Class**: **safe**. `--apply` uses template `gate-barrier`: move the test step
after an existing exclusive step, or make the cheap check just before it
exclusive. Never make a slow step exclusive only to get a barrier, because
that makes the whole gate take longer.

### GATE-3 — A second feature or profile fingerprint in the per-edit gate

**Signal**: the per-edit gate contains a cargo step whose features or profile
differ from the rest of the gate, such as `--release`, no `--all-features`, or
a different `--features` set, and it shares `target/` with them. ops keeps
`clippy-default` out of `verify` for exactly this reason. event0 keeps
`release-lint` in `qa`, not in `verify`.

**Why it costs**: a new fingerprint compiles every crate again, and it happens
on every commit.

**Default mode**: list the steps whose feature or profile flags differ. For
the cost, run the gate warm twice. On the second run a step that stays slow
has fallen into GATE-3 or TGT-1.

**Class**: two fixes, classified differently. Giving the step its **own target
directory** is **safe** (template `own-target-dir`): the first run pays once,
and later runs are warm. **Moving the step out of the per-edit gate** into
pre-push or CI is a **trade-off**: fewer runs catch what it catches. File the
safe fix. Mention the move only as an alternative.

## Target directories — `TGT`

### TGT-1 — Builds with different fingerprints evict each other

**Signal**: two cargo invocations that someone runs regularly share a target
directory, differ in features or profile, and each one makes the other rebuild.
Output at fixed paths gets overwritten: `target/doc/`, binaries copied up to
`target/debug/`, build-script output. In dbsec, the `--all-features` doc build
and the per-crate default-feature doc build cost 14.5s together on **every**
run while they shared `target/`. Split apart, they cost about 1.6s once warm.

**Default mode**: the ping-pong probe from
[measurement.md](measurement.md#ping-pong-probe). Run A, then B, then A again,
each on a warm target directory. If A's second run is not close to a no-op,
this is TGT-1.

**Class**: **safe**. `--apply` uses template `own-target-dir`.

### TGT-2 — Oversized target directory (report-only)

**Signal**: `du -sh target/` is over 20 GB, or over 30% of the free space on
its filesystem. event0's was 60 GB.

**Why it is report-only**: the size of `target/` describes this checkout's
history, not the repository. A clone made today has none of it. Most of it is
stale artifacts: the ops and dbsec evals found 20–31 copies of the main rlib
and 7–10 GB of files older than a week. No file in the repository fixes it, so
it has no `--modified-file` and is not filed. It goes in the report next to the
ENV findings.

**Default mode**: gather the following and print them in the report, together
with `cargo sweep` / `cargo clean` as the user's action:

- The `du` of `target/`, then of each directory one level down (`debug`,
  `release`, `doc`, `nextest`, any separate target directories) as a **separate**
  `du -sh target/*/`. One `du -sh target target/*` counts every file once, under
  `target`, and prints the subdirectories as empty.
- The free space on the filesystem.
- The stale share:
  `find target/debug/deps -type f -mtime +7 -printf '%s\n' | awk '{s+=$1} END {print s}'`.
- The highest rlib copy count per crate.

A large target directory that is mostly **fresh** is evidence for PROF-3 or
TGT-1. Say so, and point to `--measure-cold`.

## Dependencies — `DEP`

### DEP-1 — Duplicate crate versions

**Signal**: crates that appear in the lock at two or more **distinct**
versions. event0 had 42. Read them from `ops about dependencies --duplicates --json`,
not from `cargo tree -d`. The ops command lists only real duplicates, leaving
out a crate whose one version is reached through several paths. In the evals,
`cargo tree -d` listed 24 names for 17 real duplicates in ops, and 33 for 13 in
dbsec.

**Why it costs**: each extra version is another crate to compile, and duplicate
proc-macro and `syn` versions sit on the critical path.

**Default mode**: each entry is `crates[].{name, versions, older[]}`, and each
`older[]` item is `{version, pulledBy[]}`, the direct dependencies pulling that
version, each `{name, version, updateRemovesDuplicate}`. ops works that out with
`cargo update --dry-run` and verifies that `Cargo.lock` is unchanged afterwards. Two
things to read correctly first:

- **A puller that is the duplicated crate itself** (`rand@0.8.8` pulled by
  `rand@0.8.8`) means a workspace member depends on that old version directly. Only a
  change to the member's manifest removes it.
- **Platforms.** The report counts only dependency edges active on the host, and
  evaluates build-dependency and proc-macro edges against the host as well, so a
  Windows-only duplicate does not appear in a Linux survey. When the project also
  ships for other targets (its CI matrix, `[target.*]` sections, a `rust-toolchain`
  `targets` list), rerun with one `--target <triple>` per shipped target (the flag is
  repeatable), and say in the report which targets the list covers. The JSON does not
  record them. `--target all` counts every edge, whatever platform gates it.

Then:

- **`updateRemovesDuplicate: true`**: a semver-compatible update of that
  dependency removes the duplicate. **File it.** In ops, comfy-table 7.1.4
  pulled crossterm 0.28, rustix 0.38 and linux-raw-sys 0.4, while 7.2.2 uses
  crossterm 0.29: one lockfile update removes three duplicates.
- **`false` for every puller**: it is upstream-bound (`syn` 2 alongside 3,
  `block-buffer` 0.10 through `hmac`/`sha2`/`sqlx`). **Do not file it.** List
  it in the report as upstream-bound. That includes self-pulled entries: a major
  bump of a direct dependency can remove one, but whether it is possible is an API
  judgement the graph does not show. dbsec's `rand = "0.8"` has no other puller, yet
  it is tied to `aes-gcm` 0.10 through the `rand_core` 0.6 traits. List these in the
  report as **major-bump candidates** for a human to decide, and do not file them.
  The ops and dbsec evals produced eight tasks that could not be fixed before this
  rule existed.

**Class**: **safe**, and manual: updating a dependency is a code change and
gets reviewed like one. File one task per pulling dependency, not one per
duplicated crate. Its `--modified-file` is `Cargo.lock`, because a semver-compatible
update changes only the lock. Dev-only duplicates are left out by default. Add
`--include-dev` only when one of them is large.
Their compile time is measured only if a cold measurement ran. Otherwise it is
**unmeasured**, and that is fine: the count of crates the fix removes is itself
the evidence.

### DEP-2 — Unused dependencies

**Signal**: `cargo machete` or `cargo shear` reports a dependency. Use
whichever is installed, and **do not install either**. If neither is present,
say in the report that DEP-2 was skipped and why.

**Why it costs**: the crate compiles, often along with its own dependencies,
and nothing uses it.

**Verify before filing**: both tools give false positives for crates used only
through macros, only in `build.rs`, or only to enable a feature. `rg` for the
crate name, with `-` turned into `_`, across the member's sources before
filing.

**Class**: **safe**, and manual.

## Compiler cache — `CACHE`

### CACHE-1 — sccache configured but rarely hits

**Signal**: `RUSTC_WRAPPER`, `build.rustc-wrapper` or
`CARGO_BUILD_RUSTC_WRAPPER` names sccache, and the Rust hit rate across the
survey's own builds is below 50%. event0's was 35%.

**It needs compilations to judge.** When the warm build is a no-op, the delta
is zero requests, so there is no hit rate: 0/0 does **not** fire. Evaluate the
check only when the delta covers at least 20 executed Rust compilations,
`cache_hits.counts.Rust + cache_misses.counts.Rust`. With fewer, report it as
not evaluated, and do not file it. The counters are server-wide, so a build
elsewhere on the machine during the survey pollutes the delta. That is one more
reason for Step 2's process check.

**Why it costs**: every miss pays for the cache lookup and write on top of the
compile. The usual cause is incremental compilation: sccache cannot cache a
crate that is compiled incrementally, and Cargo compiles workspace members and
path dependencies incrementally in `dev` by default. The other causes are
worktrees and checkouts at different absolute paths (an empty `basedirs`), and a
`jobs` cap that makes the cache a bottleneck.

**Default mode**: `ops about machine --json` carries sccache's own statistics
under `sccache` when sccache is the wrapper. Take it before and after the warm
build, and use the difference. **Never** run `sccache --zero-stats`, because it
wipes counters the user may be watching. Inside that object:

| Path | Meaning |
|------|---------|
| `.stats.cache_hits.counts.Rust` | Rust hits |
| `.stats.cache_misses.counts.Rust` | Rust misses |
| `.stats.requests_not_cacheable` | Calls sccache refused to cache |
| `.stats.not_cached` | Map from reason to count (`crate-type`, `incremental`, …) |
| `.basedirs` | Path prefixes stripped from cache keys (empty means none) |

Hit rate = hits / (hits + misses). sccache does not report one ready-made. With no
Rust hits or misses, the `Rust` key is absent (`counts: {}`), so read it as 0
(`.counts.Rust // 0`). Before blaming incremental compilation, read the
setting itself from `ops about machine --json`:

- `cargo.incremental`: `{value, source}`. A global override
  (`CARGO_INCREMENTAL`, `CARGO_BUILD_INCREMENTAL` or `build.incremental`) shows its
  value and where it came from. `value: "profile"` means there is none, and each
  profile decides.
- `cargo.incrementalProfiles`: then `dev` and `release`, each `{value, source}`,
  resolved from `CARGO_PROFILE_<NAME>_INCREMENTAL`, config, the workspace
  `Cargo.toml`, or Cargo's default (`dev` on, `release` off). It is `null` when a
  global override applies.

When the survey's builds use a profile with incremental `true`, workspace crates are
uncacheable by design, and an `incremental` count in the `not_cached` delta confirms it.
When incremental is off (on the eval machine, `CARGO_INCREMENTAL=0` from the
environment), it is not the cause: look at `basedirs` and the `jobs` cap instead.

**Class**: **trade-off**. `CARGO_INCREMENTAL=0` lets sccache cache workspace
crates, but local edit-and-compile cycles get slower. The usual answer is to
turn incremental off in CI and leave it on locally, and that answer goes in a
CI file, which `--apply` does not edit. A comment in the repo's cargo config
claiming sccache makes incremental unnecessary is the usual sign (event0's
`.cargo/config.toml`). Quote it in the task.

## Environment — `ENV` (report-only)

These are facts about the machine the survey ran on, not about the repository.
They are **printed in the report and never filed**: a task would make every
contributor's backlog carry one machine's setup. They are still checked before
any timing, because they invalidate timings.

### ENV-1 — `/tmp` or `TMPDIR` on a small tmpfs

**Signal**: `ops about machine --json` reports `tmpdir.tmpfs: true` with
`totalBytes` smaller than a cold build's target directory, or
`targetDir.tmpfs: true`, meaning `CARGO_TARGET_DIR` or `build.target-dir`
points at a tmpfs.

**Why it matters**: the danger is not rustc's own temporary files, which are
small. It is a **target directory** that ends up in `/tmp`, because anything
that makes a scratch build with `mktemp -d` (a benchmark script, a bisect, a
careless survey) lands on the tmpfs. When it fills up, the build fails with
exit code 101 and **no compile error**. event0 hit this: a cold all-features
build overflowed a 16 GB `/tmp`.

The size to compare against is a *fresh* build, not the accumulated
`target/debug`: use the cold measurement if one ran, otherwise
`target/debug` minus its stale share (TGT-2). This is also why
`--measure-cold` never uses `mktemp -d` with the default location. See
[measurement.md](measurement.md#cold-target-directory).

### ENV-2 — User-level cargo configuration shapes every timing

**Signal**: in `ops about machine --json`, a `cargo.jobs`, `cargo.rustcWrapper`,
`cargo.targetDir`, `cargo.linker` or `cargo.rustflags` whose `source` is a
user-level config (`~/.cargo/config.toml`, or a `.cargo/config.toml` above the
repo) or the environment (`env:…`), not the repository's own config.

**Why it matters**: a `jobs = 2` cap on a 16-core machine makes every timing in
the report measure the cap, not the workspace. Record these settings with each
timing. Do not measure against a cap without saying so.

## Not findings

- **The linker.** Since Rust 1.90, `x86_64-unknown-linux-gnu` links with
  `rust-lld` by default. Do not recommend mold or lld on that target unless a
  `--timings` report shows link time dominating. If the user has configured
  mold on purpose, leave it alone.
- **`incremental = true` restated in a profile.** It is the default for `dev`
  and `test`, so the line changes nothing. It only matters as evidence for
  CACHE-1.
- **Settings in the `release` or `bench` profile.** They cost a release build,
  not the edit loop. Leave them alone unless the per-edit gate builds
  `--release` (GATE-3).
