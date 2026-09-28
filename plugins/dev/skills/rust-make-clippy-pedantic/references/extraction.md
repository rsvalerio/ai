# Extracting Findings from Clippy

`ops clippy-findings --schema-version 2` (ops 0.74.0 or newer) turns Clippy's JSON stream into one normalized row
per diagnostic. This skill used to do that with a hand-written `jq` pipeline. Each rule
below is one that pipeline had to get right, because the obvious alternative silently
corrupts the finding set rather than failing. ops now implements them. The list is kept
so a reader knows what the report guarantees, and what would break if the skill ever went
back to raw `cargo clippy` output.

## What each row guarantees

| Field | Guarantee | The defect it prevents |
|-------|-----------|------------------------|
| `lint` | Clippy lints only, `clippy::` prefix stripped. Plain rustc warnings (`dead_code`, `unused_variables`, …) are counted in `rustcWarnings`, not listed | Filing rustc warnings as `PED-` tasks with no catalog entry, and an inconsistent `<lint_name>` across title, labels and key |
| `package` | `name@version`, never Cargo's raw `package_id` | A raw `package_id` embeds the absolute checkout path (`path+file:///home/alice/proj#my-crate@0.4.1`), so the same finding gets a different identity from another clone or a `git worktree` and is filed again. Cargo also documents that id's format as unstable |
| `manifestDir`, `file` | Repo-relative, `/`-separated | Absolute paths in `**File**:` and `--modified-file`, which put files the repository does not contain into the wave scope `code-review-triage` computes |
| `target`, `targetKind` | The crate target (lib, bin, test, …) | Without the crate, the `(lint, crate)` aggregation in Step 5 has nothing to key on. `targetKind` `test` is also a quick way to spot findings in `tests/` |
| `line`, `column` | 1-based; `0`/`0` for a diagnostic with no span | Two findings of one lint on one line collapsing into one. A spanless diagnostic (a crate-level lint, most `clippy::cargo` findings) is attributed to its crate's `Cargo.toml` at line 0 instead of being dropped. The old pipeline once lost those and shifted every later column into the wrong field |
| `message` | Verbatim | Two distinct problems at one span sharing a task. The message is part of the finding's identity (Step 5), so it must never be rewritten or whitespace-collapsed |

At report level:

- **`schemaVersion`** must be `2`. v2 is the default since ops 0.72.0, but every pass
  still pins it with `--schema-version 2`. The v1 report uses snake_case keys
  (`manifest_dir`, …), which this skill would read as `null`, and a pinned version cannot
  be changed underneath the skill by a future default. If a report says anything else,
  stop and say so.
- **`droppedOutOfTree`** counts diagnostics whose span is outside the repository:
  registry sources, the toolchain, a build script's `OUT_DIR`. They are dependency or
  generated code, so they are never filed. Report the count.
- **Members outside the checkout** (`path = "../shared"`) are out of tree by the same rule,
  so their findings are dropped too, not filed with absolute paths.
- **Rows are sorted and de-duplicated**, so the same commit gives a byte-identical report
  from any checkout path. That is what makes the baseline diff in Step 4 and the
  `--unless-exists` key in Step 5 stable.

## What the report does not do

- **In-tree generated files** (a checked-in `include!`d module) are still listed. Recognize
  and skip them in Step 4, and report the count.
- **Test-only findings** are still listed. The test-code exclusion in Step 4 is a judgement
  about `#[cfg(test)]` modules and `#[test]` functions that no row field fully captures.
- **Feature coverage** is whatever the survey built: `--all-features` by default,
  `--no-all-features` or an explicit `--features` list when the workspace's features
  conflict. Steps 2, 3 and 7 must use the same choice.
