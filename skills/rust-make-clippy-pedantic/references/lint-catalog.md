# Clippy Lint Catalog

What the pedantic pass turns on, what it deliberately leaves off, and which effort class
each lint family falls into. Effort classes feed [estimation.md](estimation.md).

## The flag set

Everything is passed on the command line, after `--`, so the repository is never modified:

```bash
cargo clippy --workspace --all-targets --locked --message-format=json --quiet -- \
  -W clippy::pedantic \
  -W clippy::nursery \
  -W clippy::cargo \
  -A clippy::multiple_crate_versions
```

| Flag | Effect |
|------|--------|
| `-W clippy::pedantic` | ~100 lints for idiom, clarity, and numeric-cast discipline. The core of this skill |
| `-W clippy::nursery` | Newer, less-settled lints. Genuinely useful, occasionally noisy — findings from here carry lower confidence and belong in the `nursery` label |
| `-W clippy::cargo` | Manifest hygiene: missing metadata, wildcard dependencies, negative feature names |
| `-A clippy::multiple_crate_versions` | Suppressed: a dependency-graph fact no single task can fix |
| `--locked` | Cargo fails instead of writing `Cargo.lock`. Both invocations carry it — a lint run that resolves dependencies has modified the tree, which this skill promises not to do |

Deliberately **not** enabled by default:

| Flag | Why not |
|------|---------|
| `-D warnings` | Denying aborts at the first warning and truncates the survey |
| `-W clippy::restriction` | Not a lint group to enable wholesale — it contains mutually contradictory lints (`clippy::else_if_without_else` alongside `clippy::implicit_return`). Enable individual restriction lints only when the user names them |
| `--fix` | Mutates the tree. This skill never does |

`clippy::correctness`, `suspicious`, `style`, `complexity`, and `perf` are on by default and
so appear in the baseline run too — findings from them are labelled `clippy-default`.

## Effort classes

Every lint maps to one of four classes. The class, not the lint, drives the estimate.

### Class M — mechanical (~2 min per instance)

A rename or a local rewrite with no design decision. Safe to batch by the dozen.

`redundant_closure_for_method_calls`, `explicit_iter_loop`, `explicit_into_iter_loop`,
`semicolon_if_nothing_returned`, `uninlined_format_args`, `unnested_or_patterns`, `manual_let_else`, `map_unwrap_or`,
`redundant_else`, `match_same_arms`, `single_match_else`, `implicit_clone`,
`inefficient_to_string`, `cloned_instead_of_copied`.

### Class D — documentation (~3 min per instance)

Pure prose. Zero behavioural risk, and the ideal content for a first wave — it makes the
count fall fast without touching semantics.

`missing_errors_doc`, `missing_panics_doc`, `doc_markdown` (all `pedantic`), and
`missing_safety_doc` (`style`, so it reaches the report as `clippy-default`).
`missing_docs_in_private_items` is **not** listed: it belongs to `clippy::restriction`,
which the flag set does not enable, so it cannot appear in a run.

### Class J — judgement (~15 min per instance)

Each instance is a real decision that a human has to make, and getting it wrong changes
behaviour. Never batch-apply these.

`cast_possible_truncation`, `cast_sign_loss`, `cast_precision_loss`, `cast_lossless`,
`cast_possible_wrap`, `checked_conversions`, `float_cmp`, `similar_names`,
`unreadable_literal` (where the grouping is domain-meaningful), `struct_excessive_bools`,
`fn_params_excessive_bools`, `option_if_let_else` (nursery — often less readable after).

### Class S — structural (~90 min per instance)

A refactor with a blast radius beyond the flagged span. These dominate any estimate; call
them out individually in the report.

`too_many_lines`, `cognitive_complexity`, `module_name_repetitions`,
`must_use_candidate` (public API — needs a semver review even though each edit is one word),
`missing_const_for_fn` (nursery — const-correctness ripples through callers),
`items_after_statements`, `large_enum_variant`, `large_types_passed_by_value`,
`unused_self`, `return_self_not_must_use`.

### Context-qualified lints

A few lints span classes because the same warning means different work depending on where
it fires. Each gets a decision rule, applied in order, so every instance lands in exactly
one class:

**`needless_pass_by_value`** — the fix is always the same edit (`T` to `&T` in the
signature); the cost is the call sites it forces you to touch.

1. The flagged parameter is on a `pub` item reachable from the crate root → **Class S**.
   The signature is API surface, so the change is semver-visible and the call sites are
   outside your control.
2. Otherwise, count call sites. Two things make the obvious one-liner wrong: piping into
   `wc -l` counts matching *lines*, so `f(); f(); f();` on one line counts once, and an
   unscoped search sweeps in same-named functions from sibling crates. Scope to the
   defining crate's sources and count matches, then subtract the declaration:

   ```bash
   CRATE_SRC="$(dirname '<manifest_path from cargo metadata>')/src"
   calls=$(rg -F -o '<fn_name>(' "$CRATE_SRC" | wc -l)
   decls=$(rg -o '\bfn +<fn_name>\b' "$CRATE_SRC" | wc -l)
   echo $(( calls - decls ))
   ```

   More than three → **Class S**; three or fewer → **Class M**.

   The number is still a heuristic: `rg` matches inside comments, string literals and doc
   examples, and a method call on an unrelated type shares the name. **Read the matches
   whenever the count lands at three or four, or whenever any of them sit in a comment or a
   doc block** — the threshold decides an effort class, and a wrong class quietly skews the
   estimate for every instance of that lint.

Do not classify this lint on whether the type is `Copy`. Clippy fires it on non-`Copy`
types by design (`trivially_copy_pass_by_ref` is the `Copy` counterpart), so a
`Copy`/non-`Copy` split would leave most instances unassigned.

## Aggregation

A lint firing more than 20 times inside one crate is a pattern, not twenty findings. File it
as one aggregate task listing every `file:line` (see the volume guard in `SKILL.md`). Class M
and Class D lints hit this threshold constantly on a first run; Class S almost never does,
and a Class S lint that *does* fire 20+ times in one crate is itself the headline finding —
the crate needs a structural review, not twenty tasks.
