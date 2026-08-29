# Extracting Findings from Clippy JSON

Why the Step 4 `jq` pipeline is shaped the way it is. Each rule below exists because the
obvious alternative silently corrupts the finding set rather than failing.

## The row

- **`startswith("clippy::")`** — the same JSON stream carries plain rustc warnings
  (`dead_code`, `unused_variables`, …), which are not Clippy findings and have no entry in
  the lint catalog. Count them and mention the total in the report, but do not file them as
  `PED-` tasks. Stripping the prefix once here keeps `<lint_name>` consistent across the
  task title, the labels, and the `backlog search "clippy::<lint_name>"` duplicate check.
- **`package_id` and `target.name`** — the crate and target (lib, bin, test) the diagnostic
  belongs to. These live on the `compiler-message` record, not inside `.message`, which is
  why the filter binds `$m` before descending. Without them the `(lint, crate)` aggregation
  in Step 5 has no crate to key on. `package_id` is opaque but stable; `cargo metadata`
  maps it to a readable name for the task title.
- **`column_start`** — two different findings of the same lint on one line are two
  findings. Keying on `file:line` alone silently collapses them under `sort -u`.
- **The `// "-"` and `// 0` fallbacks** — a diagnostic with no primary span (a crate-level
  lint, most `clippy::cargo` findings) must still produce a row. The earlier
  `.spans[] | select(.is_primary)` form emitted *nothing* for those, which shortened the
  array and shifted every later column into the wrong field. Fixed arity means a spanless
  finding is filed against the crate rather than lost.

**Resolve the `-` file placeholder before filing.** It is a marker inside the pipeline, not
a path: `**File**: \`-\`` tells a reader nothing and `--modified-file "-"` puts a file that
does not exist into the wave scope `code-review-triage` computes. Map the row's
`package_id` to its manifest and make it repo-relative:

```bash
ROOT="$(git rev-parse --show-toplevel)"
cargo metadata --no-deps --locked --format-version 1 \
  | jq -r --arg root "$ROOT/" '.packages[] | [.id, (.manifest_path | ltrimstr($root))] | @tsv'
```

A spanless finding is then filed against that crate's `Cargo.toml` — which is genuinely the
file to edit for a `clippy::cargo` lint — keeping `line 0` to record that the diagnostic
had no span.

- **The message, verbatim** — `@tsv` already escapes tabs, newlines and backslashes, so a
  multi-line Clippy message stays one row without any rewriting. Do not `gsub` it: the
  message is part of the finding's identity (below), and collapsing whitespace throws away
  the detail that distinguishes two diagnostics sharing a location.
