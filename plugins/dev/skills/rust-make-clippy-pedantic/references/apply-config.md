# Applying the Lint Policy

Rules for Step 7, which turns the sweep's flags into checked-in configuration. This is the
only part of the skill that writes to the repository, and it does so only when the run was
invoked with `--apply`.

## The source: ops's Rust foundation

The policy is not defined here. The lint tables and `clippy.toml` come from the Rust
foundation that ships inside `ops` (`ops init --rust`, ops 0.74.0 or newer), which is the one
source for every Rust repository's lint policy. This file says how to apply the foundation,
never what it contains, so a policy change is an ops release and nothing in this skill has to
follow it.

**Render it; never run the scaffold in the repository.** `ops init --rust` writes four files
plus the lint tables, including a `rustfmt.toml` that changes what `cargo fmt` accepts. This
skill owns only the lint policy. Render the foundation into a scratch crate instead, and take
what Step 7 needs from there:

```bash
FND="$SCRATCH/foundation"
mkdir -p "$FND/src" && touch "$FND/src/lib.rs"
printf '[package]\nname = "foundation"\nversion = "0.0.0"\nedition = "2021"\n' > "$FND/Cargo.toml"
(cd "$FND" && ops init --rust >/dev/null)
```

The scratch crate yields:

| Rendered | Used for |
|----------|----------|
| `$FND/Cargo.toml`, the `[lints.*]` tables | Step 3's `-W` flags, and the tables Step 7 writes |
| `$FND/clippy.toml` | The `clippy.toml` the sweep runs under and Step 7 writes, plus `msrv` (below) |

Step 3 renders it before the sweep, so the flags, the sweep's `clippy.toml` and the applied
policy come from the same ops binary and cannot disagree. The comments in the rendered files explain each value (why
`priority = -1` is on the groups, why `rust_2018_idioms` is absent, what the four
`allow-*-in-tests` keys cover). Copy them along with the values.

## Waivers

A repository records a deliberate divergence from the foundation under `[foundation.waivers]`
in `.ops.toml`, one key per location with the reason as its value. The check then prints the
location as `waived` instead of `drift`, and exits 0 when nothing else differs. dbsec waives
twelve lints this way, each with its finding count and one tracking task.

Read the check once, from the repository root, before the sweep. It is read-only:

```bash
ops init --rust --check > "$SCRATCH/check.txt" 2>&1; echo "check exit: $?"
```

Exit 1 with `drift` lines is the normal result for a repository that has not adopted the
policy. Any other failure stops the run.

| Line | Meaning for this run |
|------|----------------------|
| `drift   <location>: …` | The repository lacks it. Surveyed, and written under `--apply` |
| `waived  <location>: … (<reason>)` | The repository declined it. Not surveyed, not filed, not written |
| `unused  waiver <location>: …` | A waiver that matches nothing. Report it as found |

**A waived lint is not surveyed.** The sweep enables exactly what `--apply` writes, and
`--apply` never overrides a waiver, so a waived lint gets no flag
([lint-catalog.md](lint-catalog.md#the-flag-set)) and a waived `clippy.toml` key keeps the
repository's value ([below](#the-sweeps-clippytoml)). The first dbsec run did survey them,
and filed 200 tasks for work the repository already tracked in one.

**Nothing is filed for a waiver**, not even a summary task. The waiver's reason is the
repository's record, and it usually names the task that tracks the work.

**Every waiver is reported**, verbatim with its reason, in Step 6. Say there that the listed
lints were left out of the sweep, and that removing a waiver from `.ops.toml` is how to have
one surveyed.

A waived `<member>/Cargo.toml:lints.workspace` means that member stays outside the policy.
The flags reach every crate, so discard the pedantic-only rows whose `manifestDir` is that
member before filing, and report the count.

When every difference is waived, Step 7 has
[nothing to write](../SKILL.md#step-7--apply-the-lint-policy---apply). That result has no
flagless rerun to verify it: with no file written, the rerun is Step 2 again, and its
matching the baseline says nothing about whether a policy is inert. The check that applies
is that the tree is still clean outside `.backlog/`. This is what dbsec's `--apply` run
reached, with no rule to name it.

## The sweep's `clippy.toml`

The lint flags are only half of the policy. The thresholds (`too-many-lines-threshold`,
`too-many-arguments-threshold`, …) and the four `allow-*-in-tests` keys live in `clippy.toml`,
and a sweep that ran without them would report a different finding set from the one the
applied policy produces. So Step 3 builds the root `clippy.toml` as Step 7 would leave it,
in scratch, and the pedantic pass runs under it:

| Repository has | `$SCRATCH/conf/clippy.toml` is |
|----------------|--------------------------------|
| No root `clippy.toml` | A copy of `$FND/clippy.toml`, plus [`msrv`](#msrv) |
| A root `clippy.toml` | A copy of it, with each key the check reports as `drift   clippy.toml:<key>` set to the rendered value and its comment |

```bash
mkdir -p "$SCRATCH/conf"
cp clippy.toml "$SCRATCH/conf/clippy.toml" 2>/dev/null || cp "$FND/clippy.toml" "$SCRATCH/conf/clippy.toml"
grep '^drift *clippy\.toml:' "$SCRATCH/check.txt"     # the keys to set, when the file existed
grep '^waived *clippy\.toml:' "$SCRATCH/check.txt"    # the keys to leave as the repository has them
```

A waived key keeps the repository's value. When the file was copied from `$FND`, delete the
waived key from the copy so Clippy's default applies, as it does in the repository today.

`CLIPPY_CONF_DIR="$SCRATCH/conf"` makes Clippy read that file and no other. Two consequences:

- Only the pedantic pass sets it. The baseline pass and Step 7's verification read the
  repository's own file, which after `--apply` is this one.
- A member crate with its own `clippy.toml` is linted under the root policy during the
  sweep, while a normal run would use the member's file. Name such members in the report.
  Step 7 leaves their files alone.

## What gets written

| File | Content | Why |
|------|---------|-----|
| Root `Cargo.toml` | The rendered `[lints.rust]`, `[lints.rustdoc]` and `[lints.clippy]`, as `[workspace.lints.*]` in a workspace | One central lint policy (ARCH-11) |
| Every member `Cargo.toml` | `[lints]` with `workspace = true` | Without it the workspace table is inert, see below |
| Root `clippy.toml` | The rendered file, plus `msrv` | Configuration the lint levels cannot express |

A single-crate project has no workspace: keep the rendered `[lints.*]` headers in its
`Cargo.toml` and skip the member step. The `[lints]` table needs Cargo 1.74 or newer. Below
that, stop and report rather than falling back to crate-root `#![warn(...)]` attributes,
which spread the policy across source files this skill has no business editing.

**Where the file or table is missing**, write the rendered one. **Where it exists**, change
only what the foundation check reported in `$SCRATCH/check.txt` ([Waivers](#waivers)). The
check is read-only, so it also feeds the preview a run without `--apply` prints.

Each `drift` line names one location. Act on these three forms only:

| Drift location | Fix |
|----------------|-----|
| `clippy.toml:<key>` | Set the key to the rendered value, with its comment |
| `Cargo.toml:workspace.lints.<tool>.<lint>` (`Cargo.toml:lints.…` for a single crate) | Add the lint, or raise its level to the rendered one |
| `<member>/Cargo.toml:lints.workspace` | Add the member opt-in |

Keys and lints the repository adds are its own. The check accepts them, and so does this
skill: never remove one. A stricter level than the foundation's (`deny` where it has `warn`)
also passes; never lower it.

Drift in `deny.toml`, `rustfmt.toml` or `.config/nextest.toml` is not this skill's to change.
List it in the report as found, and point at `ops init --rust` for the rest of the foundation.

## The `--apply` procedure

The five steps of Step 7, in order. Nothing here runs without `--apply`.

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
2. **Write the three file kinds** from the rendered foundation, surgically. The root
   `clippy.toml` is `$SCRATCH/conf/clippy.toml`, the file the sweep ran under. Do not reformat
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

   No `CLIPPY_CONF_DIR` either: this run must read the `clippy.toml` that was just written.

   Then `ops init --rust --check` must report no `drift` line for `clippy.toml`, the root
   lint tables or any member's `lints.workspace`. `waived` lines are expected to remain.

   The configuration is correct when this run's `findings` are the pedantic finding set from
   Step 3, row for row: `jq -S .findings` of `applied.json` and `pedantic.json` must be
   equal. A count *below* it means the policy is inert, almost always a member crate missing
   `[lints] workspace = true`. A count *above* it in test code means the written
   `clippy.toml` differs from `$SCRATCH/conf/clippy.toml`. A manifest error here
   (`lint group has the same priority as`) means the `priority = -1` entries are wrong. Fix
   and re-verify; do not report success on an unverified write.
5. **Report the files touched and stop.** Do not commit, stage, or push — the user reviews
   the diff. Say plainly that the working tree is now dirty by design, and name the level
   that was written along with the condition for raising it to `deny`.

## Member `Cargo.toml`

Every workspace member needs, once, anywhere in the file:

```toml
[lints]
workspace = true
```

**This is the step that is easy to skip and silently does nothing when skipped.**
`[workspace.lints]` on its own configures no crate. It is a table members opt into. A
workspace where half the crates lack the opt-in has half a policy, and the missing half looks
clean because nothing is checking it. The foundation check reports every member that lacks
it. Cross-check against `ops about crates` rather than globbing `crates/*`, because path
dependencies outside the members list are common:

```bash
ops about crates --json | jq -r '.crates[] | select(.inTree) | "\(.manifestDir)/Cargo.toml"'
```

`manifestDir` is repo-relative. A member outside the checkout (`inTree: false`) is not this
repository's manifest to edit: report it and leave it alone.

## `msrv`

The rendered `clippy.toml` has no `msrv`, because the scratch crate declares no
`rust-version`. `msrv` is the repository's own value, not part of the baseline, and the check
ignores it. Add it after the rendered keys:

```toml
# Keep equal to `rust-version` in the root Cargo.toml so `clippy::incompatible_msrv`
# fails on any standard-library call newer than the declared floor.
msrv = "<rust-version from the root Cargo.toml>"
```

`msrv` **must** be copied from the root `Cargo.toml`'s `rust-version` (or
`[workspace.package]`), not invented. If the manifest declares none, omit the key and say so
in the report. A guessed floor turns `incompatible_msrv` into noise in both directions. An
existing `msrv` that disagrees with `rust-version` is reported, not rewritten.

## The test opt-outs do not generalise

The foundation's `allow-*-in-tests` keys cover exactly four lints: `unwrap_used`,
`expect_used`, `panic` and `indexing_slicing`. The sweep runs under those keys
([above](#the-sweeps-clippytoml)), so Clippy leaves those four out of `#[test]` functions and
`#[cfg(test)]` modules in the sweep exactly as it will under the applied policy. That is the
whole test exemption, and Step 4 adds nothing to it.

No other lint has such a key. There is no `allow-missing-panics-doc-in-tests` and no
`allow-arithmetic-side-effects-in-tests`, and inventing one puts an unknown key in
`clippy.toml`, which Clippy rejects. `arithmetic_side_effects` in a test module fires under
the applied policy, so the sweep files it. On the dbsec run 316 of 1,027 rows were
test-code findings of a lint with no such key. If a lint proves noisy in test code, the fix is the task's to make, at the module:
`#[allow(clippy::arithmetic_side_effects, reason = "…")]` on the `#[cfg(test)]` module.

## Choosing the level

The foundation sets every lint to `warn`. That is the floor, and the right level whenever the
sweep found anything:

| Sweep result | Level | Reasoning |
|--------------|-------|-----------|
| Zero findings | `deny` | The gate holds today, so lock it in. The check accepts `deny` for a `warn` baseline |
| Any findings | `warn`, as rendered | `deny` breaks `cargo build` for everyone on code nobody has fixed yet |

Say in the report which was chosen and why, and note that the level becomes `deny` once the
backlog this run filed is closed. Never propose `deny` alongside a wall of new warnings, and
never soften a level the project already had.

## What not to write

- **Nothing beyond the foundation.** No extra lint group, no restriction lint the foundation
  does not list, no threshold of this skill's own. A lint the project wants on top is the
  project's addition, made by a person. A policy change for every repository is an ops
  change.
- **No blanket "temporary allows" block.** Listing every pre-existing violation as an `allow`
  converts a backlog into policy: it never shrinks on its own, and new code inherits the
  exemption. The findings this run filed are the record. An exception belongs at the call
  site, as `#[allow(clippy::x, reason = "…")]`, next to the code it excuses.
- **No per-crate lint levels.** A member that sets its own levels instead of
  `workspace = true` opts out of the central policy invisibly.
- **No `#![warn(...)]` crate-root attributes.** Same reason, and it puts lint policy in
  source files.
- **No other foundation file.** `deny.toml`, `rustfmt.toml` and `.config/nextest.toml` are
  `ops init --rust`'s to write, when the owner chooses to.
- **Nothing else.** Do not reformat the manifest, reorder dependencies, or bump versions while
  editing. The diff should contain the lint policy and nothing a reviewer has to squint at.
