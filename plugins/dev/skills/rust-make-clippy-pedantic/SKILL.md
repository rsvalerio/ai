---
name: rust-make-clippy-pedantic
description: Runs Clippy at pedantic strength over a clean checkout without touching the source tree, then files one backlog task per warning, each labelled pedantic, and reports a high-level effort estimate for clearing them. Generated files and out-of-tree warnings are dropped, the four panic lints the policy allows in tests are not reported from test code, and a lint firing more than twenty times in one crate becomes a single aggregate task. Passing --apply additionally writes the lint policy into Cargo.toml and clippy.toml; without it the run only shows what those files would contain. Use when a Rust project should be held to stricter lint levels than its current configuration enforces.
allowed-tools: Read Edit Write Grep Glob Bash(git status:*) Bash(git rev-parse:*) Bash(git log:*) Bash(cargo --version) Bash(cargo clippy --version) Bash(cargo clippy --explain:*) Bash(clippy-driver -W help) Bash(ops --version) Bash(ops clippy-findings:*) Bash(ops about crates:*) Bash(ops about machine:*) Bash(ops backlog:*) Bash(ops init --rust:*) Bash(jq:*) Bash(mktemp:*) Bash(mkdir:*) Bash(rm -rf:*) Bash(cp:*) Bash(touch:*) Bash(printf:*) Bash(python3:*) Bash(xargs:*) Bash(sha256sum) Bash(rg:*) Bash(wc -l)
license: Apache-2.0
---

# Make Clippy Pedantic

Raise a Rust project to pedantic-grade linting **without changing a line of its source**.
The strict lint levels are command-line flags; no `#![warn(...)]` attribute is added, and
`--fix` is never used. The run produces one backlog task per finding, an effort estimate,
and the lint configuration that would make the strictness permanent — written only under
`--apply`.

## Invocation

| Argument | Effect |
|----------|--------|
| *(none)* | Survey only. Files the findings, prints the report, and **shows** the configuration Step 7 would write without writing it |
| `--apply` | Everything above, and then writes the lint policy into `Cargo.toml` and `clippy.toml` |

`--apply` is the single exception to this skill's no-writes rule. Nothing else about the run
changes — the same preflight, the same flags, the same tasks.

## Purpose

- Verify the working tree is clean before linting, so findings map to a known commit
- Run Clippy through `ops clippy-findings` with ops's foundation lints as `-W` flags and its
  `clippy.toml` from scratch, leaving the repository byte-identical
- Diff the pedantic run against a default-level baseline, so pre-existing warnings are
  labelled as such
- Create one backlog task per finding, every task labelled `pedantic`
- Report what ran, what was filed, and a work estimate for clearing the backlog
- Show the lint policy that locks the strictness in, and write it only under `--apply`

## Execution Contract (MUST follow)

You are running unattended — nobody is watching to course-correct.

1. **Never mutate the repository, except under `--apply`.** No `cargo clippy --fix`, no
   `git stash`, no `git pull`, no lint attributes, no source edits — ever. Writes go to
   `.backlog/` (through the `ops backlog` CLI) and to a scratch directory outside the
   repository. The one exception is [Step 7](#step-7--apply-the-lint-policy---apply): with
   `--apply`, and only then, the run writes `Cargo.toml` and `clippy.toml`. Never commit,
   stage, or push what it writes.
2. **Abort — do not adapt — on a dirty tree.** See [Step 1](#step-1--preflight-a-clean-tree).
   Print the blocking condition and stop. Cleaning it up for the user is not in scope.
3. **Findings are emitted ONLY via `ops backlog task create --plain`.** A prose list of
   warnings in lieu of tasks is a failed run.
4. **Never ask for confirmation.** You are pre-authorized: findings go straight to
   `ops backlog task create --plain`.
5. **The only terminal action is the report** ([Step 6](#step-6--report)), printed after
   every task creation has succeeded, followed by Step 7's configuration block or diff.
6. **On tool failure, retry once, then report the specific error.** Do not silently
   degrade to a text summary.

## Process

### Step 1 — Preflight a clean tree

All four checks must pass. On any failure, print the reason and stop.

```bash
git rev-parse --is-inside-work-tree              # must be true
git status --porcelain -- . ':(exclude).backlog'  # must be EMPTY (tracked + untracked)
git rev-parse --short HEAD                       # record: findings are pinned to this SHA
git rev-parse --abbrev-ref HEAD                  # record: branch name
```

- **No modifications, staged or unstaged, and no untracked files.** A stray untracked
  `src/scratch.rs` gets linted and would file findings against code that is not in the
  commit. `.backlog/` is the one exclusion: task files are never linted, and this run writes
  there anyway. Step 7 checks the tree against the same pathspec.
- **Do not fetch, pull, rebase, or stash.** Making the tree clean would change what gets
  linted.
- A detached HEAD is fine — record the SHA and carry on.

Then confirm the toolchain and record it for the report:

```bash
cargo --version && cargo clippy --version
ops --version    # must be 0.74.0 or newer: clippy-findings v2, init --rust
```

If `cargo clippy` is not installed, or `ops` is missing or older than 0.74.0, stop and say
so.

### Step 2 — Establish the default-level baseline

Lint once at the project's own configured level, into a scratch target directory so the
project's `target/` and its incremental caches are untouched. The scratch directory goes on
real disk: a bare `mktemp -d` lands in `TMPDIR`, often a tmpfs a lint build can fill, and
cargo then exits 101 with no compile error.

```bash
BASE="${XDG_CACHE_HOME:-$HOME/.cache}/rust-make-clippy-pedantic"
mkdir -p "$BASE" && SCRATCH="$(mktemp -d -p "$BASE")"
CARGO_TARGET_DIR="$SCRATCH/target" ops about machine --json | jq '.targetDir'   # .tmpfs must be false
CARGO_TARGET_DIR="$SCRATCH/target" \
  ops clippy-findings --schema-version 2 > "$SCRATCH/baseline.json" 2> "$SCRATCH/baseline.err"
```

If `tmpfs` is true, stop before building and say so; the user points `XDG_CACHE_HOME` at
real disk. **Delete `$SCRATCH` with `rm -rf` when the run ends**: after the Step 6 report, or
after Step 7's verification under `--apply`, and also when the run stops on an error, once
the error has been reported.

`ops clippy-findings` is a survey, not a gate. It runs
`cargo clippy --workspace --all-features --all-targets --locked`, never adds `-D warnings`,
and prints one normalized JSON row per Clippy diagnostic
([extraction.md](references/extraction.md)).

`--locked` is on by default and is part of the non-destructive promise
([lint-catalog.md](references/lint-catalog.md#the-flag-set)); never pass `--no-locked`. If
Cargo refuses with `the lock file needs to be updated`, or the project commits no lock file,
**stop and report it**: refreshing the lock is the user's change to make, not a lint sweep's.

**Features.** The survey defaults to `--all-features`, the build the `ops clippy` gate lints.
If it fails on mutually exclusive features, rerun **both** passes with `--no-all-features`
and note the reduced coverage in the report. Steps 2, 3 and the Step 7 verification must
use the same feature set, or the baseline diff compares two different builds.

**If this run fails to compile, stop**, report the compiler error and file nothing.

Warnings present here are pre-existing at the project's own settings. They are still
findings, labelled `clippy-default` rather than `pedantic-only`: failures of the current
gate, not new demands from a stricter one.

### Step 3 — Run the pedantic pass

The lints and the Clippy configuration are ops's Rust foundation policy, which Step 7
applies. Prepare both in `$SCRATCH`, never in the repository:

1. Render the foundation
   ([apply-config.md](references/apply-config.md#the-source-opss-rust-foundation)).
2. Save the foundation check to `$SCRATCH/check.txt`. Its `waived` lines are lints and keys
   the repository has declined on the record
   ([apply-config.md](references/apply-config.md#waivers)). They are not surveyed, not
   filed and not written; they are reported.
3. Build `$SCRATCH/conf/clippy.toml`, the file Step 7 would leave at the repository root
   ([apply-config.md](references/apply-config.md#the-sweeps-clippytoml)).
4. Write `$SCRATCH/lint-flags` ([lint-catalog.md](references/lint-catalog.md#the-flag-set)),
   which leaves the waived lints out, and record the flags.

Then rerun Step 2 with the flags, and with `CLIPPY_CONF_DIR` pointing Clippy at that file:

```bash
CLIPPY_CONF_DIR="$SCRATCH/conf" CARGO_TARGET_DIR="$SCRATCH/target" \
  xargs ops clippy-findings --schema-version 2 -- < "$SCRATCH/lint-flags" \
  > "$SCRATCH/pedantic.json" 2> "$SCRATCH/pedantic.err"
```

- **Flags and a scratch config, never source**, so the run is non-destructive and repeatable.
- **The config is half the policy**: the thresholds and the `allow-*-in-tests` keys. Without
  it the sweep reports a finding set the applied policy never produces. The baseline pass
  in Step 2 keeps the project's own configuration.
- **Never `-D`**, even for a foundation `deny`: it truncates the survey.
- **Add nothing** unless the user names lints; report those, as `--apply` will not write them.
- **An empty `lint-flags`** (every lint waived) still runs the pass, without `xargs` and `--`.

### Step 4 — Classify findings

Each report's `findings` are normalized rows: `lint`, `package` (`name@version`),
repo-relative `manifestDir` and `file`, `target`, `targetKind`, `line`, `column` and the
verbatim `message`. Out-of-tree spans and rustc warnings are only counted
(`droppedOutOfTree`, `rustcWarnings`). What each field guarantees, and the defect it
prevents, is in [extraction.md](references/extraction.md).

For each pedantic row:

- **Origin** — the identical row (every field) is also in `baseline.json` →
  `clippy-default`; otherwise → `pedantic-only`:

  ```bash
  jq -c --slurpfile base "$SCRATCH/baseline.json" \
    '.findings[] | . as $r | .origin = (if ($base[0].findings | index([$r])) then "clippy-default" else "pedantic-only" end)' \
    "$SCRATCH/pedantic.json"
  ```

- **Lint group** — look the lint up in `$SCRATCH/lint-groups.json`, built from the installed
  Clippy ([lint-catalog.md](references/lint-catalog.md#lint-groups)). Never from memory.
- **Effort class** — from [lint-catalog.md](references/lint-catalog.md#effort-classes); a
  lint it does not name takes its group's default class.
- **Severity** — map with the table in [Severity Scale](#severity-scale).

Report `droppedOutOfTree` and `rustcWarnings` as counts; neither is filed. Then discard
before filing:

- Findings in generated files that live inside the repository (`include!`d generated
  modules checked in, for example). ops only drops what is out of tree. Note the count in
  the report instead.

**Nothing is discarded for being in test code.** Clippy already applied the policy's one
test exemption: the pass ran under the foundation's `clippy.toml`, so `unwrap_used`,
`expect_used`, `panic` and `indexing_slicing` (the four lints with an `allow-*-in-tests`
key) never reach the report from a `#[test]` function or a `#[cfg(test)]` module. Every
other row is filed wherever it sits, because the applied policy fires on it there too. Do
not drop a row by `targetKind`, by path, or by reading the source for `#[cfg(test)]`. That
includes one of the four in a `tests/` helper outside any `#[test]`, which is not test code
to Clippy.

### Step 5 — Deduplicate, then file one task per finding

The identity of a finding is its full row: lint, package, target, file, line, column and
message together ([why no narrower key](references/extraction.md#finding-identity)). Pass it
as `--unless-exists`, with the message hashed so the key stays one short line:

```bash
KEY="PED:<lint>:<package>:<target>:<file>:<line>:<column>:$(printf %s "<message>" | sha256sum | cut -c1-12)"
```

When an open task already carries the key, ops creates nothing and prints `Exists <id>`. A
key whose only task is `Done` files again: the warning has regressed.

The one sanctioned exception is the `(lint, crate)` aggregate described in the volume
guard below, which deliberately covers many keys in one task and records each of them in
its description. Its key is `PED:<lint>:<package>:aggregate`.

Then create the task. Use a `"$(cat <<'EOF' ... EOF)"` heredoc for the description — do not
use `$'...'` ANSI-C quoting, which triggers a safety prompt on every call.

```bash
ops backlog task create "PED-<lint_name>: <short description>" \
  -d "$(cat <<'EOF'
**Lint**: `clippy::<lint_name>` (<group>, <origin>)

**File**: `<path>:<line>`

**What**: <the clippy message, verbatim>

**Why it matters**: <what the lint protects against>

**Fix sketch**: <the change the message implies>

**Commit**: <short SHA from Step 1>
EOF
)" \
  -s "Triage" \
  -l "rust-make-clippy-pedantic,pedantic,<group>,<origin>" \
  --priority <critical|high|medium|low> \
  --modified-file "<path>" \
  --ac "`clippy::<lint_name>` no longer fires at `<path>` under `-W clippy::pedantic`" \
  --ac "Behaviour is unchanged: existing tests still pass" \
  --unless-exists "$KEY" \
  --plain
```

Non-negotiables for every task:

- **The `pedantic` label is required on every task**, including `clippy-default`-origin ones
  — it is what identifies this run's output as a set.
- **`--modified-file` is required**, one flag per touched path, repo-root-relative and
  **without** the `:<line>` suffix. `code-review-triage` reads it to compute wave scope and
  merge order; a finding filed without it is invisible to triage.
- **Every field comes from the row, the group lookup or the catalog.** The row has no help
  text; `cargo clippy --explain <lint_name>` prints the lint's own rationale and example.
- **Status is always `Triage`.** This skill never assigns work, only files it.

**Volume guard.** One task per instance would bury the backlog on a mature workspace. When
a single lint fires **more than 20 times inside one crate**, file one aggregate task for
that `(lint, crate)` pair, with every instance listed as `file:line` in the description and
one `--modified-file` per distinct path. Report how many tasks were aggregated, and add
`<!-- scan confidence: candidates to inspect -->` to any aggregate whose instances were not
individually read.

### Step 6 — Report

Print, in this order:

1. **What ran** — commit SHA and branch, `cargo`/`clippy` versions, the exact flag list, the
   feature set used, and whether the tree was verified clean.
2. **What was waived** — each `waived` line of `check.txt` with its reason, verbatim, and
   the statement that none of them was surveyed. Omit when there is none.
3. **What was found** — total warnings, split `pedantic-only` vs `clippy-default`, and a
   table of the top lints by instance count with their effort class, marking each class
   that is a group default.
4. **What was filed** — task count, how many were aggregates, how many were skipped as
   duplicates, and how many were discarded as generated or out-of-tree.
5. **Work estimate** — the sizing from [estimation.md](references/estimation.md): a band per
   effort class, a workspace total as a range in engineer-days, a T-shirt size, and the two
   or three lints that dominate. State that the rates come from a fixed table, not from
   reading the code, so the number reads as a planning signal, not a quote.
6. **Suggested next step** — `code-review-triage` to group the new `Triage` tasks into waves.

Verify the filing landed:

```bash
ops backlog task list --status 'Triage' --plain
```

### Step 7 — Apply the lint policy (`--apply`)

This step moves the strictness out of the command line and into checked-in configuration.
The level policy and the gotchas that make a policy silently inert live in
[apply-config.md](references/apply-config.md) — read it before writing anything.

Three files are involved: the root `Cargo.toml` (`[workspace.lints.*]`), every member
`Cargo.toml` (`[lints] workspace = true`, without which the workspace tables configure
nothing), and a root `clippy.toml` (plus `msrv` from `rust-version`), all from Step 3's
render. In existing files, change only what `check.txt` reports as `drift`.

**Nothing to write** is a result of its own. When `check.txt` has no `drift` line for
`clippy.toml`, the lint tables or a member's `lints.workspace`, the policy is in place or
every difference is waived. With or without `--apply`, write nothing, skip the procedure
below, and report `nothing to write: <n> waived, 0 drift`. The verification is that
`git status --porcelain -- . ':(exclude).backlog'` is still empty; there is no rerun,
because it would only reproduce Step 2
([apply-config.md](references/apply-config.md#waivers)).

**Without `--apply` — the default — write nothing.** Print each file's proposed content as
a fenced TOML block under a heading that names the path and says whether the file would be
created or edited. For an existing file, show only the block that would be added or changed.
Then say that nothing was written and that `--apply` would write it. A run that prints this
and stops has succeeded.

**With `--apply`**, follow
[the apply procedure](references/apply-config.md#the---apply-procedure) in order:

1. Re-verify that nothing but `.backlog/` changed since Step 1, and stop if it did.
2. Write the three file kinds, surgically. The root `clippy.toml` is
   `$SCRATCH/conf/clippy.toml`, the file the sweep ran under.
3. Choose the level from the sweep's own result: `warn` when it found anything, `deny` only
   when it found nothing.
4. Verify: a flagless rerun of Step 2 must reproduce Step 3's finding set row for row, and
   `ops init --rust --check` must report no lint-policy drift. Do not report success on an
   unverified write.
5. Report the files touched and stop. Never commit, stage, or push them.

## Finding ID Prefixes

| Prefix | Meaning |
|--------|---------|
| `PED-<lint_name>` | One Clippy lint at one location, or one aggregated `(lint, crate)` pair |

The lint name is the title's identifier, stable across runs and greppable. The duplicate
check is the full-row `--unless-exists` key from Step 5, not the title.

## Severity Scale

Clippy's own category is the primary signal; the pedantic group is style-and-clarity by
construction and rarely rises above medium.

| Clippy category | Priority | Rationale |
|-----------------|----------|-----------|
| `correctness` | critical | The code is wrong, not merely unidiomatic |
| `suspicious` | high | Very likely a defect; needs a human decision |
| `perf` | medium | Real cost, but bounded and local |
| `complexity` | medium | Maintenance burden; raise to high above ~30 lines of affected code |
| `pedantic`, `nursery`, `style` | low | Clarity and idiom; batch them |
| `restriction` (named foundation lints) | medium | A panic or silent wrap-around in production code |

Escalate one level when the finding sits in a public API, an `unsafe` block, or an error
path — the same code being wrong costs more there.

## Scan Checklist

Signals that change the estimate, and so are called out in the report: bulk documentation
lints, `must_use_candidate`, renames, numeric casts, structural lints, findings concentrated
in one crate, and a high `clippy-default` count. The table is in
[estimation.md](references/estimation.md#signals-to-call-out).

## Concurrency

The skill writes only through the `ops backlog` CLI, so parallel instances cannot corrupt
each other. Two caveats:

- Filing is idempotent through the Step 5 `--unless-exists` key, so two runs over one
  workspace file each finding once. They still build it twice, so run one at a time.
- Run it before `code-review-triage`, not during: tasks filed mid-triage land in the next
  wave, not the current one.

## References

- [Extraction](references/extraction.md) — Why the `jq` row is shaped as it is, and the defects each field prevents
- [Lint catalog](references/lint-catalog.md) — Groups, flag set, and effort class per lint family
- [Estimation model](references/estimation.md) — Effort classes, rates, and how the higher-view number is built
- [Applying the lint policy](references/apply-config.md) — Rendering ops's Rust foundation, what `--apply` writes from it, level policy, and what not to write
- [OpenAI agent metadata](assets/openai.yaml) — Optional agent configuration for compatible runtimes
- `code-review-rust` — Semantic Rust review; this skill is its mechanical counterpart
- `code-review-triage` — Groups the `Triage` tasks this skill files into waves
