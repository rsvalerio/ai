# Apply Templates

What `--apply` writes, and how. Only **safe** findings that have a template
here are applied. Trade-off findings are never applied. Safe findings without a
template (PROF-5, DEP-1, DEP-2) are manual work and stay as tasks. A
standalone TEST-2 is a trade-off and is never applied.

Every template edits one small region of one file. Never reformat a file,
reorder keys, or touch anything outside that region. The diff should show the
fix and nothing a reviewer has to check twice.

| Template | Check | File |
|----------|-------|------|
| `test-profile-align` | PROF-2, the safe keys only | Root `Cargo.toml` |
| `gate-nextest` | TEST-1 (with its doctest step), TEST-3 | `.ops.toml` |
| `nextest-leak-timeout` | TEST-4 | `.config/nextest.toml` |
| `gate-staged` | GATE-1 | `.ops.toml` |
| `gate-barrier` | GATE-2 | `.ops.toml` |
| `own-target-dir` | GATE-3, TGT-1 | `.ops.toml`, or the script the gate calls |

Only `.ops.toml` gates are applied automatically. A gate defined in a
`Makefile`, a `justfile`, an `xtask` or a CI workflow is manual work: those
files have no single layout to template, and a CI edit changes what everyone's
pull requests run. The finding is filed either way. Only the automatic write is
limited to `.ops.toml`.

## `test-profile-align`

Delete only the **safe** divergent keys from `[profile.test]`, the ones
PROF-2's table in [checks.md](checks.md#prof-2--test-profile-diverges-from-dev)
classifies as safe: `codegen-units`, `incremental`, `split-debuginfo` and
`strip`. `test` then inherits them from `dev` again. If that leaves the table
empty, delete the table header and any comment that describes the deleted
keys.

```toml
# before
[profile.test]
codegen-units = 1      # "faster tests"
incremental = true

# after: nothing. test inherits dev, and `incremental = true` restated the default
```

Leave every other key where it is, even when it diverges from `dev`: `opt-level`,
`lto`, `debug`, `overflow-checks`, `debug-assertions`, `panic`, and any
`package` override. These change how fast the tests run, what they check, or
what a debugger shows. They are PROF-2 trade-offs and are never applied. If
removing the safe keys would still leave `test` diverging from `dev`, say in
the report that the double compile remains until the trade-off is decided.

## `gate-nextest`

In the gate composite, swap each libtest step for its nextest counterpart from
the `ops` rust stack, and make sure the gate runs doctests:

| Before | After |
|--------|-------|
| `test` | `next`, plus `test-doc` if the gate lacks it. `cargo test` ran doctests, so this keeps coverage the same |
| `test-ignored` | `next-ignored` |

```toml
# before
[commands.qa]
commands = ["deps", "release-lint", "test", "test-ignored"]

# after
[commands.qa]
commands = ["deps", "release-lint", "next", "test-doc", "next-ignored"]
```

Keep the order and the other steps as they are, and keep the gate's
`parallel` and `fail_fast` settings. Update its `help` string when it lists the
steps. If the swapped step was the gate's own override with extra arguments
(say `--features x`), carry those arguments over to a `[commands.next]`
override. Otherwise the swap quietly drops them.

**Verify by running the gate once.** If a test fails under nextest that passes
under `cargo test`, the test shares process-global state across tests. Revert
this template's edit, keep the task open, and record the failing test names on
it with `ops backlog task edit <id> --append-notes`.

## `nextest-leak-timeout`

```toml
[profile.default]
# nextest flags a test as LEAK when its output pipes have not reached EOF this
# long after the test reports a result. Raised from the 100ms default because
# under contention an exit that loses the race for a core is flagged as a leak.
# A real leak still reports LEAK, only later; a run with no leak pays nothing,
# because the wait ends at EOF, not at the timeout.
leak-timeout = "2s"
```

If `[profile.default]` already exists, add only the key and its comment. If
`leak-timeout` is already set to 2s or more, the check should not have fired.
Fix the check, not the file.

## `gate-staged`

When `.ops.toml` redefines `[commands.verify]` with a list that includes the
stack's own steps, switch to extending it. Keep only the steps the stack does
not already provide:

```toml
# before: a redefinition that copies the stack's list and then runs flat
[commands.verify]
commands = ["fmt", "clippy", "build", "doc", "doc-default", "next"]
parallel = false

# after: the stack's staged verify, plus the two extra steps
[extend.verify]
commands = ["doc-default", "next"]
```

Before rewriting, compare against `ops explain verify --json`. The redefinition may
have left out a stack step on purpose (for example no `doc`). If so, do not
apply the template. Mark the task manual and quote the omission in its notes,
because putting the step back is a coverage change, not a speed change.

## `gate-barrier`

Put an exclusive step between the build steps and the test step, so the test
step starts after `build` has finished and reuses its artifacts. Prefer a
cheap check that already exists (a lockfile check, a sync check, a lint on a
config file) and set `exclusive = true` on it:

```toml
# fuzz-lock is read-only and fast, but `exclusive` is load-bearing: in the
# parallel `verify` plan it puts a stage barrier after clippy | build | doc,
# so `next` starts only once `build` has finished and reuses its artifacts
# instead of racing it for the cargo lock.
[commands.fuzz-lock]
exclusive = true
```

Also make sure the test step comes after the barrier in the gate's order. With
`[extend.verify]` that means it is listed after the barrier step. If no cheap
step exists, do not invent one, and never make a slow step exclusive. Mark the
task manual and say so.

## `own-target-dir`

Give the step whose features or profile differ from the rest of the gate its
own target directory under the project's `target/`:

```toml
[commands.clippy-default]
program = "cargo"
args = ["clippy", "--workspace", "--all-targets", "--", "-D", "warnings"]
# Default features are a second fingerprint. In their own target dir they stay
# warm instead of evicting the --all-features artifacts on every run.
env = { CARGO_TARGET_DIR = "target/clippy-default" }
```

`env` values in `.ops.toml` are literal strings. `target/clippy-default` would
override a target directory set anywhere else and put this step's build back
under the project. Apply this form **only when nothing else sets the target
directory**, meaning `ops about machine --json` reports
`cargo.targetDir.source: "default"`. Any other source (`env:CARGO_TARGET_DIR`,
or a config file setting `build.target-dir`) makes the `.ops.toml` form
**manual**. Say in the task which setting
blocked it, and suggest the script form below.

If the gate runs through a script instead, set it in the script, keeping the
user's directory as the base the way dbsec's `doc-default-check.sh` does.
This form is safe to apply either way:

```bash
export CARGO_TARGET_DIR="${CARGO_TARGET_DIR:-target}/doc-default"
```

Name the directory after the step. Say in the report that the first run after
applying is cold, and give that one-off cost from the measurement.

## Verifying what was written

Check every file that was written before reporting success:

| File | Check |
|------|-------|
| `Cargo.toml` | `cargo metadata --locked --format-version 1 >/dev/null` parses it, and a `cargo build --locked` of the gate command reports no `unused manifest key` warning |
| `.ops.toml` | `ops explain <gate> --json` resolves every edited gate, with the new steps in the stages the template intended, for example the test step after the barrier for `gate-barrier`, or the `env.CARGO_TARGET_DIR` for `own-target-dir` |
| `.config/nextest.toml` | `python3 -c 'import sys, tomllib; tomllib.load(open(sys.argv[1], "rb"))' .config/nextest.toml` parses it. The gate run below then loads it for real. Do not use `cargo nextest show-config` as a cheap check: it builds the test binaries, and in the eval it compiled a new default-feature fingerprint |

Then run the gates that were edited once, and compare against the numbers the
finding recorded. A safe fix that did not make anything faster was
misclassified, or the measurement was noise. Say which, and keep the task open.
