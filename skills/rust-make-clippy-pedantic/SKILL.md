---
name: rust-make-clippy-pedantic
description: Runs Clippy at pedantic strength over a clean checkout without touching the source tree, then files one backlog task per warning, each labelled pedantic, and reports a high-level effort estimate for clearing them. Test-only style findings, generated files, and out-of-tree warnings are dropped, and a lint firing more than twenty times in one crate becomes a single aggregate task. Passing --apply additionally writes the lint policy into Cargo.toml and clippy.toml; without it the run only shows what those files would contain. Use when a Rust project should be held to stricter lint levels than its current configuration enforces.
allowed-tools: Read Edit Write Grep Glob Bash(git status:*) Bash(git rev-parse:*) Bash(git log:*) Bash(git stash list:*) Bash(cargo clippy:*) Bash(cargo metadata:*) Bash(cargo --version) Bash(jq:*) Bash(mktemp:*) Bash(backlog task:*) Bash(backlog search:*)
license: Apache-2.0
---

# Make Clippy Pedantic

Raise a Rust project to pedantic-grade linting **without changing a line of its source**.
The aggressive lint levels are passed as command-line flags to `cargo clippy`; no
`#![warn(...)]` attribute is added to any crate, and `--fix` is never used. The output of
the run is a set of backlog tasks, one per finding, plus an effort estimate, plus the lint
configuration that would make the strictness permanent — shown by default, and written to
`Cargo.toml` and `clippy.toml` only when the run is invoked with `--apply`.

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
- Run `cargo clippy` with `clippy::pedantic` (and the other strict groups) supplied as
  `-W` flags after `--`, leaving the repository byte-identical
- Diff the pedantic run against a default-level baseline so pre-existing warnings are
  labelled honestly
- Create one backlog task per finding via `backlog task create --plain`, every task
  labelled `pedantic`
- Report what ran, what was filed, and a higher-view work estimate for clearing the backlog
- Show the `Cargo.toml` and `clippy.toml` lint policy that locks the strictness in, and
  write it when — and only when — `--apply` was passed

## Execution Contract (MUST follow)

You are running unattended — nobody is watching to course-correct.

1. **Never mutate the repository, except under `--apply`.** No `cargo clippy --fix`, no
   `git stash`, no `git pull`, no lint attributes, no source edits — ever. Writes go to
   `.backlog/` (through the `backlog` CLI) and to a scratch directory. The one exception is
   [Step 7](#step-7--apply-the-lint-policy---apply): with `--apply`, and only then, the run
   writes `Cargo.toml` and `clippy.toml`. Without the flag those files are printed, never
   written. Never commit, stage, or push what `--apply` writes.
2. **Abort — do not adapt — on a dirty tree.** See [Step 1](#step-1--preflight-a-clean-tree).
   Print the blocking condition and stop. Cleaning it up for the user is not in scope.
3. **Findings are emitted ONLY via `backlog task create --plain`.** A prose list of
   warnings in lieu of tasks is a failed run.
4. **Never ask for confirmation.** You are pre-authorized: findings go straight to
   `backlog task create --plain`.
5. **The only terminal action is the report** ([Step 6](#step-6--report)), printed after
   every task creation has succeeded, followed by Step 7's configuration block or diff.
6. **On tool failure, retry once, then report the specific error.** Do not silently
   degrade to a text summary.

## Process

### Step 1 — Preflight a clean tree

All four checks must pass. On any failure, print the reason and stop.

```bash
git rev-parse --is-inside-work-tree              # must be true
git status --porcelain                           # must be EMPTY (tracked + untracked)
git rev-parse --short HEAD                       # record: findings are pinned to this SHA
git rev-parse --abbrev-ref HEAD                  # record: branch name
```

- **No modifications, staged or unstaged, and no untracked files.** `git status --porcelain`
  must print nothing. Untracked files count: a stray `src/scratch.rs` gets linted and would
  file findings against code that is not in the commit.
- **Do not fetch, pull, rebase, or stash.** The point of the check is that the tree already
  is what it claims to be; making it clean would change what gets linted.
- A detached HEAD is fine — record the SHA and carry on.

Then confirm the toolchain and record it for the report:

```bash
cargo --version && cargo clippy --version
```

If `cargo clippy` is not installed (`rustup component add clippy`), stop and say so.

### Step 2 — Establish the default-level baseline

Lint once at the project's own configured level, into a scratch target directory so the
project's `target/` and its incremental caches are untouched:

```bash
SCRATCH="$(mktemp -d)"
CARGO_TARGET_DIR="$SCRATCH/target" \
  cargo clippy --workspace --all-targets --locked --message-format=json --quiet \
  > "$SCRATCH/baseline.json" 2> "$SCRATCH/baseline.err"
```

`--locked` is part of the non-destructive promise: without it, a missing or stale
`Cargo.lock` is silently written during dependency resolution, and a run that edits a
tracked file is exactly what Step 1 verified would not happen. If Cargo refuses with
`the lock file needs to be updated`, **stop and report it** — refreshing the lock is a
change to the repository and belongs to the user, not to a lint sweep. The same applies to
a project that does not commit its lock file at all: say so rather than generating one.

**If this run fails to compile, stop.** A tree that does not build cannot be linted
meaningfully; report the compiler error and file nothing.

Warnings present here are *pre-existing at the project's own settings* — they are still
findings, but they are labelled `clippy-default` rather than `pedantic-only`, because they
are failures of the current gate, not new demands from a stricter one.

### Step 3 — Run the pedantic pass

Same invocation with the strict groups appended as flags after `--`:

```bash
CARGO_TARGET_DIR="$SCRATCH/target" \
  cargo clippy --workspace --all-targets --locked --message-format=json --quiet -- \
    -W clippy::pedantic \
    -W clippy::nursery \
    -W clippy::cargo \
    -A clippy::multiple_crate_versions \
  > "$SCRATCH/pedantic.json" 2> "$SCRATCH/pedantic.err"
```

Rules for this invocation:

- **Flags, never source.** Everything strict arrives through `-W` after `--`. This is what
  makes the run non-destructive and repeatable.
- **Never pass `-D warnings`.** Denying turns the first warning into a hard error and
  truncates the survey; the whole point is to enumerate everything.
- `-A clippy::multiple_crate_versions` is suppressed by default: it is a dependency-graph
  fact, not a code defect, and files a task nobody can act on. Drop the `-A` only if the
  user explicitly asks for dependency hygiene findings.
- Add `--all-features` only if the workspace has no mutually exclusive features. If the
  run fails with a feature conflict, retry without it and note the reduced coverage in the
  report.
- Passing flags after `--` disables Clippy's ability to reuse cached results for the final
  crates, but dependencies are still only checked once. Expect a full workspace build on the
  first pass; `$SCRATCH` is reused between Steps 2 and 3 so this is paid once.

### Step 4 — Extract and classify findings

```bash
jq -r 'select(.reason == "compiler-message")
       | select(.message.code.code? // "" | startswith("clippy::"))
       | . as $m
       | ($m.message.spans // [] | map(select(.is_primary)) | first) as $s
       | [ ($m.message.code.code | ltrimstr("clippy::")),
           ($m.package_id // "-"),
           ($m.target.name // "-"),
           ($s.file_name // "-"),
           (($s.line_start // 0) | tostring),
           (($s.column_start // 0) | tostring),
           $m.message.message ]
       | @tsv' "$SCRATCH/pedantic.json" | sort -u
```

Every field of that row earns its place, and three of them fix a defect that is invisible
until it corrupts the output — the rationale, the spanless-path resolution, and the
`@tsv` escaping guarantee are in [extraction.md](references/extraction.md). Read it before
changing the pipeline.

Run the same extraction over `baseline.json`. Then, for each pedantic finding:

- **Origin** — present in the baseline set → `clippy-default`; otherwise → `pedantic-only`.
- **Lint group** — resolve `clippy::<name>` to its group and effort class using
  [lint-catalog.md](references/lint-catalog.md).
- **Severity** — map with the table in [Severity Scale](#severity-scale).

Discard before filing:

- Findings whose primary span is outside the repository (paths under `~/.cargo/registry`,
  `$SCRATCH`, or any generated `OUT_DIR`). These are dependency or build-script code.
- Findings in generated files (`build.rs` output, `include!`d generated modules) — note the
  count in the report instead.
- **Test-only style findings.** Lints such as `clippy::unwrap_used`, `clippy::panic`, and
  `clippy::missing_panics_doc` firing exclusively inside `#[cfg(test)]` modules, files under
  `tests/`, or `#[test]` functions are not findings. A finding that disappears when test
  code is excluded is not filed.

### Step 5 — Deduplicate, then file one task per finding

Check the backlog before writing:

```bash
backlog search "clippy::<lint_name>" --plain
```

The identity of a finding is the full row from Step 4: lint, `package_id`, target, file,
line, column and message together. If an open (not `Done`) task already covers that key,
skip it. If it is `Done`, file again only if the warning has genuinely
regressed. Do not treat two findings as the same because they share a lint and a file:
`(file, line)` alone merges distinct findings, and the lint alone merges a whole crate. The
message belongs in the key too — one lint can report several distinct problems at one span,
and dropping it lets the second silently reuse the first one's task. The cost is that a
reworded message in a newer Clippy reads as a new finding; prefer that over a lost one, and
close the stale task when it happens.

The one sanctioned exception is the `(lint, crate)` aggregate described in the volume
guard below, which deliberately covers many keys in one task and records each of them in
its description.

Then create the task. Use a `"$(cat <<'EOF' ... EOF)"` heredoc for the description — do not
use `$'...'` ANSI-C quoting, which triggers a safety prompt on every call.

```bash
backlog task create "PED-<lint_name>: <short description>" \
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
backlog task list --status 'Triage' --plain
```

### Step 7 — Apply the lint policy (`--apply`)

The sweep proves the project *can* be held to a stricter standard; this step is what keeps
it there, by moving the strictness out of the command line and into checked-in
configuration. Templates, the level policy, and the gotchas that make a policy silently
inert live in [apply-config.md](references/apply-config.md) — read it before writing
anything.

Three files are involved: the root `Cargo.toml` (the `[workspace.lints.*]` tables), every
member `Cargo.toml` (`[lints] workspace = true`, without which the workspace tables
configure nothing), and a root `clippy.toml` (thresholds, `msrv` copied from `rust-version`,
and the `allow-*-in-tests` opt-outs).

**Without `--apply` — the default — write nothing.** Print each file's proposed content in
full, as a fenced TOML block per file, under a heading that names the path and says whether
the file would be created or edited. For a file that already exists, show only the block
that would be added or changed, so the reader sees a diff rather than a re-listing. Then say
explicitly that nothing was written and that `--apply` would write it. A run that prints
this and stops has succeeded.

**With `--apply`:**

1. **Re-verify the tree is still clean** (`git status --porcelain`) before the first write.
   The sweep takes minutes; something may have changed underneath it.
2. **Write the three file kinds** using the templates, editing surgically. Do not reformat
   the manifest, reorder dependencies, or touch anything but the lint tables.
3. **Choose the level from the sweep's own result** — `warn` when it found anything, `deny`
   only when it found nothing. Denying a workspace that has open findings breaks
   `cargo build` for everyone on code nobody has fixed yet.
4. **Verify the policy took effect.** Re-run the Step 2 command with no `-W` flags at all:

   ```bash
   CARGO_TARGET_DIR="$SCRATCH/target" \
     cargo clippy --workspace --all-targets --locked --message-format=json --quiet \
     > "$SCRATCH/applied.json" 2> "$SCRATCH/applied.err"
   ```

   Extract it exactly as in Step 4. The configuration is correct when this run reproduces
   the pedantic finding set from Step 3. A count far *below* it means the policy is inert —
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

The lint name *is* the identifier — it is stable across runs and greppable, which is what
makes `backlog search "clippy::<lint_name>"` a reliable duplicate check.

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
| `cargo` | low | Manifest hygiene |

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

The skill is read-only on the codebase and writes only through the `backlog` CLI, so
parallel instances cannot corrupt each other. Two caveats:

- Two runs over the same workspace will file the same findings twice — the duplicate check
  in Step 5 is per-run, not a lock. Run one at a time per repository.
- Run it before `code-review-triage`, not during: tasks filed mid-triage land in the next
  wave, not the current one.

## References

- [Extraction](references/extraction.md) — Why the `jq` row is shaped as it is, and the defects each field prevents
- [Lint catalog](references/lint-catalog.md) — Groups, flag set, and effort class per lint family
- [Estimation model](references/estimation.md) — Effort classes, rates, and how the higher-view number is built
- [Applying the lint policy](references/apply-config.md) — `--apply` templates for `Cargo.toml` and `clippy.toml`, level policy, and what not to write
- [OpenAI agent metadata](assets/openai.yaml) — Optional agent configuration for compatible runtimes
- `code-review-rust` — Semantic Rust review; this skill is its mechanical counterpart
- `code-review-triage` — Groups the `Triage` tasks this skill files into waves
