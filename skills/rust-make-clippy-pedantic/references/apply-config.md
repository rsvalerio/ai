# Applying the Lint Policy

Templates and rules for Step 7, which turns the flags used during the sweep into checked-in
configuration. This is the only part of the skill that writes to the repository, and it
does so only when the run was invoked with `--apply`.

## What gets written

| File | Content | Why |
|------|---------|-----|
| Root `Cargo.toml` | `[workspace.lints.rust]` and `[workspace.lints.clippy]` | One central lint policy for the workspace (ARCH-11) |
| Every member `Cargo.toml` | `[lints]` with `workspace = true` | Without it the workspace table is inert — see below |
| Root `clippy.toml` | Thresholds, `msrv`, and the test opt-outs | Configuration the lint levels cannot express |

A single-crate project has no workspace: write `[lints.rust]` and `[lints.clippy]` directly
in its `Cargo.toml` and skip the member step. The `[lints]` table needs Cargo 1.74 or newer;
below that, stop and report rather than falling back to crate-root `#![warn(...)]`
attributes, which spread the policy across source files this skill has no business editing.

## Root `Cargo.toml`

```toml
# Centralized lint policy. Every workspace member opts in with
# `[lints] workspace = true`; no crate sets its own lint levels.
[workspace.lints.rust]
elided_lifetimes_in_paths = "warn"
unsafe_op_in_unsafe_fn = "warn"
unused_lifetimes = "warn"

[workspace.lints.clippy]
all = { level = "warn", priority = -1 }
pedantic = { level = "warn", priority = -1 }
nursery = { level = "warn", priority = -1 }
cargo = { level = "warn", priority = -1 }

# Panics and silent wrap-around in production code. Test code opts out through
# the `allow-*-in-tests` keys in clippy.toml.
unwrap_used = "warn"
expect_used = "warn"
panic = "warn"
todo = "warn"
unimplemented = "warn"
unreachable = "warn"
panic_in_result_fn = "warn"
indexing_slicing = "warn"
string_slice = "warn"
arithmetic_side_effects = "warn"
as_conversions = "warn"
exit = "warn"
```

The `cargo` group is there because the sweep enables it (`-W clippy::cargo`). Omitting it
would leave the applied policy quieter than the run that produced the findings, and Step 7's
verification — which requires the configured run to reproduce the sweep's finding set —
would fail on exactly the manifest-hygiene lints this file exists to configure. If the
sweep suppressed `clippy::multiple_crate_versions`, carry that across as
`multiple_crate_versions = "allow"` rather than dropping the group.

**`priority = -1` is mandatory on the four group entries.** Cargo rejects a manifest where
a lint group and an individual lint share a priority — `unwrap_used` sits inside
`clippy::all`, so without the negative priority the build fails with *"lint `clippy::all`
has the same priority as `clippy::unwrap_used`"*. The negative value makes the groups apply
first and the named lints override them.

The `[workspace.lints.rust]` entries are not Clippy at all — they are rustc lints that pair
naturally with a pedantic policy. Do **not** add `rust_2018_idioms`: it implies
`unused_extern_crates`, which fires on the deliberate `extern crate` lines that keep
link-time-only crates (a `linkme` registry, for instance) from being dropped by the linker.

## Member `Cargo.toml`

Every workspace member needs, once, anywhere in the file:

```toml
[lints]
workspace = true
```

**This is the step that is easy to skip and silently does nothing when skipped.**
`[workspace.lints]` on its own configures no crate; it is a table members opt into. A
workspace where half the crates lack the opt-in has half a policy, and the missing half
looks clean because nothing is checking it. Enumerate members from `cargo metadata` rather
than globbing `crates/*` — path dependencies outside the members list are common:

```bash
cargo metadata --no-deps --locked --format-version 1 \
  | jq -r '.packages[].manifest_path'
```

## Root `clippy.toml`

```toml
cognitive-complexity-threshold = 25
too-many-arguments-threshold = 5
type-complexity-threshold = 250

# Keep equal to `rust-version` in the root Cargo.toml so `clippy::incompatible_msrv`
# fails on any standard-library call newer than the declared floor, and the
# declaration cannot silently drift. MSRV-aware lints also gate their suggestions
# on this value.
msrv = "<rust-version from the root Cargo.toml>"

# Panic-adjacent lints are denied in production code but fine in tests.
allow-unwrap-in-tests = true
allow-expect-in-tests = true
allow-panic-in-tests = true
allow-indexing-slicing-in-tests = true
```

`msrv` **must** be copied from the root `Cargo.toml`'s `rust-version`, not invented. If the
manifest declares none, omit the key entirely and say so in the report — a guessed floor
turns `incompatible_msrv` into noise in both directions.

The `allow-*-in-tests` keys are what make the panic-adjacent lints tolerable, and they cover
exactly four lints: `unwrap_used`, `expect_used`, `panic`, and `indexing_slicing`. For those,
Step 4's decision to drop test-only findings matches the policy written here — the configured
run genuinely does not fire on them in test code.

**It does not generalise.** There is no `allow-missing-panics-doc-in-tests` key, or any
equivalent for the other lints Step 4 excludes from filing; inventing one puts an unknown key
in `clippy.toml`, which Clippy rejects. A `pub fn` inside a `#[cfg(test)]` module can still
raise `missing_panics_doc` under the applied policy even though the sweep declined to file
it. Expect that gap when comparing the counts in Step 7's verification, and close it at the
call site with `#[allow(clippy::missing_panics_doc, reason = "…")]` if it proves noisy —
never with a `clippy.toml` key that does not exist.

## Choosing the level

| Sweep result | Level | Reasoning |
|--------------|-------|-----------|
| Zero findings | `deny` | The gate holds today, so lock it in |
| Any findings | `warn` | `deny` breaks `cargo build` for everyone on code nobody has fixed yet |

Say in the report which was chosen and why, and note that the level becomes `deny` once the
backlog this run filed is closed. Never propose `deny` alongside a wall of new warnings, and
never soften a level the project already had — if the root manifest already denies a lint,
keep it denied.

## What not to write

- **No blanket "temporary allows" block.** Listing every pre-existing violation as an
  `allow` at the top of the manifest converts a backlog into policy: it never shrinks on its
  own, and new code inherits the exemption. The findings this run filed are the record. An
  exception belongs at the call site, as `#[allow(clippy::x, reason = "…")]`, next to the
  code it excuses.
- **No per-crate lint levels.** A member that sets its own levels instead of
  `workspace = true` opts out of the central policy invisibly.
- **No `#![warn(...)]` crate-root attributes.** Same reason, and it puts lint policy in
  source files.
- **Nothing else.** Do not reformat the manifest, reorder dependencies, or bump versions
  while editing. The diff should contain the lint policy and nothing a reviewer has to
  squint at.
