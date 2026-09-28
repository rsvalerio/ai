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
| `$FND/clippy.toml` | The `clippy.toml` Step 7 writes, plus `msrv` (below) |

Step 3 renders it before the sweep, so the flags and the applied policy come from the same ops
binary and cannot disagree. The comments in the rendered files explain each value (why
`priority = -1` is on the groups, why `rust_2018_idioms` is absent, what the four
`allow-*-in-tests` keys cover). Copy them along with the values.

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
only what the foundation check reports. Run it from the repository root. It is read-only, so
it also feeds the preview a run without `--apply` prints:

```bash
ops init --rust --check
```

Each `drift` line names one location. Act on these three forms only:

| Drift location | Fix |
|----------------|-----|
| `clippy.toml:<key>` | Set the key to the rendered value, with its comment |
| `Cargo.toml:workspace.lints.<tool>.<lint>` (`Cargo.toml:lints.…` for a single crate) | Add the lint, or raise its level to the rendered one |
| `<member>/Cargo.toml:lints.workspace` | Add the member opt-in |

Keys and lints the repository adds are its own. The check accepts them, and so does this
skill: never remove one. A stricter level than the foundation's (`deny` where it has `warn`)
also passes; never lower it.

Drift in `deny.toml`, `rustfmt.toml` or `.config/nextest.toml`, and anything already listed
under `[foundation.waivers]` in `.ops.toml`, is not this skill's to change. List it in the
report as found, and point at `ops init --rust` for the rest of the foundation.

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
`expect_used`, `panic` and `indexing_slicing`. For those, Step 4's decision to drop test-only
findings matches the applied policy, because the configured run does not fire on them in test
code.

No other lint has such a key. There is no `allow-missing-panics-doc-in-tests` and no
`allow-arithmetic-side-effects-in-tests`, and inventing one puts an unknown key in
`clippy.toml`, which Clippy rejects. A `pub fn` inside a `#[cfg(test)]` module can still
raise `missing_panics_doc` under the applied policy even though the sweep declined to file
it. Expect that gap when comparing counts in Step 7's verification, and close it at the call
site with `#[allow(clippy::missing_panics_doc, reason = "…")]` if it proves noisy.

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
