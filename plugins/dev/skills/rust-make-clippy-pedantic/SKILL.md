---
name: rust-make-clippy-pedantic
description: Runs Clippy at pedantic strength over a clean checkout without touching the source tree, then files one backlog task per warning, each labelled pedantic, and reports a high-level effort estimate for clearing them. Test-only style findings, generated files, and out-of-tree warnings are dropped, and a lint firing more than twenty times in one crate becomes a single aggregate task. Passing --apply additionally writes the lint policy into Cargo.toml and clippy.toml; without it the run only shows what those files would contain. Use when a Rust project should be held to stricter lint levels than its current configuration enforces.
allowed-tools: Read Edit Write Grep Glob Bash(git status:*) Bash(git rev-parse:*) Bash(git log:*) Bash(cargo --version) Bash(cargo clippy --version) Bash(ops --version) Bash(ops clippy-findings:*) Bash(ops about crates:*) Bash(ops backlog:*) Bash(ops init --rust:*) Bash(jq:*) Bash(mktemp:*) Bash(mkdir:*) Bash(touch:*) Bash(printf:*) Bash(python3:*) Bash(xargs:*) Bash(sha256sum) Bash(rg:*) Bash(wc -l)
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

`--apply` is the single exception to this skill's no-writes rule, and it is deliberate: the
sweep is worthless as a one-off if nothing stops the same warnings coming back. Nothing
else about the run changes — the same preflight, the same flags, the same tasks.

## Purpose

- Verify the working tree is clean before linting, so findings map to a known commit
- Run Clippy through `ops clippy-findings` with ops's foundation lints as `-W` flags,
  leaving the repository byte-identical
- Diff the pedantic run against a default-level baseline so pre-existing warnings are
  labelled honestly
- Create one backlog task per finding via `ops backlog task create --plain`, every task
  labelled `pedantic`
- Report what ran, what was filed, and a higher-view work estimate for clearing the backlog
- Show the `Cargo.toml` and `clippy.toml` lint policy that locks the strictness in, and
  write it when — and only when — `--apply` was passed

## Execution Contract (MUST follow)

You are running unattended — nobody is watching to course-correct.

1. **Never mutate the repository, except under `--apply`.** No `cargo clippy --fix`, no
   `git stash`, no `git pull`, no lint attributes, no source edits — ever. Writes go to
   `.backlog/` (through the `ops backlog` CLI) and to a scratch directory. The one exception is
   [Step 7](#step-7--apply-the-lint-policy---apply): with `--apply`, and only then, the run
   writes `Cargo.toml` and `clippy.toml`. Without the flag those files are printed, never
   written. Never commit, stage, or push what `--apply` writes.
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

- **No modifications, staged or unstaged, and no untracked files.** `git status --porcelain`
  must print nothing. Untracked files count: a stray `src/scratch.rs` gets linted and would
  file findings against code that is not in the commit. `.backlog/` is the one exclusion:
  task files are never linted, and this run writes there anyway. Step 7 checks the tree
  against the same pathspec.
- **Do not fetch, pull, rebase, or stash.** The point of the check is that the tree already
  is what it claims to be; making it clean would change what gets linted.
- A detached HEAD is fine — record the SHA and carry on.

Then confirm the toolchain and record it for the report:

```bash
cargo --version && cargo clippy --version
ops --version    # must be 0.74.0 or newer: clippy-findings v2, init --rust
```

If `cargo clippy` is not installed (`rustup component add clippy`), or `ops` is missing or
older than 0.74.0, stop and say so.

### Step 2 — Establish the default-level baseline

Lint once at the project's own configured level, into a scratch target directory so the
project's `target/` and its incremental caches are untouched:

```bash
SCRATCH="$(mktemp -d)"
CARGO_TARGET_DIR="$SCRATCH/target" \
  ops clippy-findings --schema-version 2 > "$SCRATCH/baseline.json" 2> "$SCRATCH/baseline.err"
```

`ops clippy-findings` is a survey, not a gate. It runs
`cargo clippy --workspace --all-features --all-targets --locked --message-format=json`,
never adds `-D warnings`, and prints one normalized JSON row per Clippy diagnostic
([extraction.md](references/extraction.md)).

`--locked` is on by default and is part of the non-destructive promise
([lint-catalog.md](references/lint-catalog.md#the-flag-set)); never pass `--no-locked`. If
Cargo refuses with `the lock file needs to be updated`, or the project commits no lock file,
**stop and report it**: refreshing the lock is the user's change to make, not a lint sweep's.

**Features.** The survey defaults to `--all-features`, the build the `ops clippy` gate lints.
If it fails with a feature conflict (mutually exclusive features), rerun **both** passes
with `--no-all-features`, and note the reduced coverage in the report. Steps 2, 3 and the
Step 7 verification must always use the same feature set, or the baseline diff compares two
different builds.

**If this run fails to compile, stop.** A tree that does not build cannot be linted
meaningfully; report the compiler error and file nothing.

Warnings present here are *pre-existing at the project's own settings* — they are still
findings, but they are labelled `clippy-default` rather than `pedantic-only`, because they
are failures of the current gate, not new demands from a stricter one.

### Step 3 — Run the pedantic pass

The lints are ops's Rust foundation policy, which Step 7 applies. Render it into `$SCRATCH`
([apply-config.md](references/apply-config.md#the-source-opss-rust-foundation), never in the
repository), write `$SCRATCH/lint-flags` ([lint-catalog.md](references/lint-catalog.md#the-flag-set)),
record the flags, and rerun Step 2 with them:

```bash
CARGO_TARGET_DIR="$SCRATCH/target" \
  xargs ops clippy-findings --schema-version 2 -- < "$SCRATCH/lint-flags" \
  > "$SCRATCH/pedantic.json" 2> "$SCRATCH/pedantic.err"
```

- **Flags, never source**, so the run is non-destructive and repeatable.
- **Never `-D`**, even for a foundation `deny`: it truncates the survey.
- **Add nothing** unless the user names lints; report those, as `--apply` will not write them.

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

- **Lint group** — resolve `clippy::<lint>` to its group and effort class using
  [lint-catalog.md](references/lint-catalog.md).
- **Severity** — map with the table in [Severity Scale](#severity-scale).

Report `droppedOutOfTree` and `rustcWarnings` as counts; neither is filed. Then discard
before filing:

- Findings in generated files that live inside the repository (`include!`d generated
  modules checked in, for example). ops only drops what is out of tree. Note the count in
  the report instead.
- **Test-only style findings.** Lints such as `clippy::unwrap_used`, `clippy::panic`, and
  `clippy::missing_panics_doc` firing exclusively inside `#[cfg(test)]` modules, files under
  `tests/` (`targetKind` `test`), or `#[test]` functions are not findings. A finding that
  disappears when test code is excluded is not filed.

### Step 5 — Deduplicate, then file one task per finding

The identity of a finding is its full row: lint, package, target, file, line, column and
message together. A narrower key merges distinct findings: `(file, line)` merges two lints,
the lint alone a whole crate, and dropping the message merges two problems one lint reports
at one span. A reworded message in a newer Clippy then reads as a new finding; prefer that
over a lost one, and close the stale task.

Pass that identity as `--unless-exists`, with the message hashed so the key stays one
short line:

```bash
KEY="PED:<lint>:<package>:<target>:<file>:<line>:<column>:$(printf %s "<message>" | sha256sum | cut -c1-12)"
```

When an open task already carries the key, ops creates nothing and prints `Exists <id>`.
The check runs under the backlog's allocation lock, so it holds across concurrent runs. A
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

**Fix sketch**: <the clippy help text, or the mechanical change it implies>

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
- **Status is always `Triage`.** This skill never assigns work, only files it.

**Volume guard.** Pedantic runs on a mature workspace routinely emit thousands of warnings,
and one task per instance would bury the backlog rather than describe it. So: file one task
per finding, except that when a single lint fires **more than 20 times inside one crate**,
file one aggregate task for that `(lint, crate)` pair with every instance listed as
`file:line` in the description and one `--modified-file` per distinct path. Say plainly in
the report how many tasks were aggregated this way, and add
`<!-- scan confidence: candidates to inspect -->` to any aggregate whose instances were not
individually read.

### Step 6 — Report

Print, in this order:

1. **What ran** — commit SHA and branch, `cargo`/`clippy` versions, the exact flag list, the
   feature set used, and whether the tree was verified clean.
2. **What was found** — total warnings, split `pedantic-only` vs `clippy-default`, and a
   table of the top lints by instance count with their effort class.
3. **What was filed** — task count, how many were aggregates, how many were skipped as
   duplicates, and how many were discarded as test-only or out-of-tree.
4. **Work estimate** — the higher-view sizing from [estimation.md](references/estimation.md):
   a per-effort-class band, a workspace total as a range in engineer-days, a T-shirt size,
   and the two or three lints that dominate the total. State the assumptions (rates come
   from a fixed table, not from reading the code) so the number is read as a planning
   signal, not a quote.
5. **Suggested next step** — `code-review-triage` to group the new `Triage` tasks into waves.

Verify the filing landed:

```bash
ops backlog task list --status 'Triage' --plain
```

### Step 7 — Apply the lint policy (`--apply`)

The sweep proves the project *can* be held to a stricter standard; this step is what keeps
it there, by moving the strictness out of the command line and into checked-in
configuration. Templates, the level policy, and the gotchas that make a policy silently
inert live in [apply-config.md](references/apply-config.md) — read it before writing
anything.

Three files are involved: the root `Cargo.toml` (`[workspace.lints.*]`), every member
`Cargo.toml` (`[lints] workspace = true`, without which the workspace tables configure
nothing), and a root `clippy.toml` (plus `msrv` from `rust-version`), all from Step 3's
render. In existing files, change only what `ops init --rust --check` reports.

**Without `--apply` — the default — write nothing.** Print each file's proposed content in
full, as a fenced TOML block per file, under a heading that names the path and says whether
the file would be created or edited. For a file that already exists, show only the block
that would be added or changed, so the reader sees a diff rather than a re-listing. Then say
explicitly that nothing was written and that `--apply` would write it. A run that prints
this and stops has succeeded.

**With `--apply`:**

1. **Re-verify that nothing but the backlog changed** before the first write. A plain
   `git status --porcelain` is now guaranteed dirty — Step 5 just wrote task files under
   `.backlog/`, which most consumer repos track — so gating on it would abort every
   `--apply` run. Exclude the backlog and compare against the Step 1 snapshot:

   ```bash
   git status --porcelain -- . ':(exclude).backlog'   # must still be EMPTY
   git rev-parse --short HEAD                          # must equal the Step 1 SHA
   ```

   Anything else appearing here means the tree moved under the sweep; stop and report
   rather than writing a policy derived from code that is no longer checked out.
2. **Write the three file kinds** from the rendered foundation, surgically. Do not reformat
   the manifest, reorder dependencies, or touch anything but the lint tables.
3. **Choose the level from the sweep's own result** — `warn` when it found anything, `deny`
   only when it found nothing. Denying a workspace that has open findings breaks
   `cargo build` for everyone on code nobody has fixed yet.
4. **Verify the policy took effect.** Re-run the Step 2 command, with no lint flags at
   all and the same feature set as Steps 2 and 3:

   ```bash
   CARGO_TARGET_DIR="$SCRATCH/target" \
     ops clippy-findings --schema-version 2 > "$SCRATCH/applied.json" 2> "$SCRATCH/applied.err"
   ```

   Then `ops init --rust --check` must report no drift in `clippy.toml`, the root lint
   tables or any member's `lints.workspace`.

   The configuration is correct when this run's `findings` reproduce the pedantic finding
   set from Step 3. A count far *below* it means the policy is inert —
   almost always a member crate missing `[lints] workspace = true`. A manifest error here
   (`lint group has the same priority as`) means the `priority = -1` entries are wrong. Fix
   and re-verify; do not report success on an unverified write.
5. **Report the files touched and stop.** Do not commit, stage, or push — the user reviews
   the diff. Say plainly that the working tree is now dirty by design, and name the level
   that was written along with the condition for raising it to `deny`.

## Finding ID Prefixes

| Prefix | Meaning |
|--------|---------|
| `PED-<lint_name>` | One Clippy lint at one location, or one aggregated `(lint, crate)` pair |

The lint name *is* the title's identifier: it is stable across runs and greppable. The
duplicate check does not rely on it. That is the full-row `--unless-exists` key from
Step 5.

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

Signals worth calling out explicitly in the report, because they change the estimate:

| Signal | Why it matters |
|--------|----------------|
| `clippy::missing_errors_doc` / `missing_panics_doc` in bulk | Documentation debt: high count, near-zero risk, ideal first wave |
| `clippy::must_use_candidate` in bulk | Mechanical, but touches the public API surface — a semver review |
| `clippy::module_name_repetitions` | Renames ripple through call sites; cheap per site, wide blast radius |
| `clippy::cast_possible_truncation` / `cast_precision_loss` | Each one is a real numeric decision, not a rename — the expensive class |
| `clippy::too_many_lines` / `cognitive_complexity` | Structural refactors; the dominant term in most estimates |
| Findings concentrated in one crate | Suggests a single wave rather than a workspace-wide push |
| A high `clippy-default` count | The current gate is not being enforced in CI — worth flagging on its own |

## Concurrency

The skill is read-only on the codebase and writes only through the `ops backlog` CLI, so
parallel instances cannot corrupt each other. Two caveats:

- Filing is idempotent: the Step 5 `--unless-exists` key is checked under the backlog's
  allocation lock, so two runs over one workspace file each finding once. Two runs still
  build the workspace twice for nothing, so run one at a time per repository.
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
