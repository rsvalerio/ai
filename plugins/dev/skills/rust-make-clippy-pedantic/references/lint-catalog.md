# Clippy Lint Catalog

What the pedantic pass turns on, what it deliberately leaves off, and which effort class
each lint family falls into. Effort classes feed [estimation.md](estimation.md).

## The flag set

Everything is passed on the command line, after `--`, so the repository is never modified.
`ops clippy-findings` hands the lint flags to Clippy and runs Cargo with
`--workspace --all-features --all-targets --locked`.

The lint flags are not listed here. SKILL.md Step 3 derives them from the lint policy of ops's
Rust foundation, rendered by the running `ops` ([apply-config.md](apply-config.md)), so the
sweep enables exactly what `--apply` writes. With the foundation rendered at `$FND`, this
writes the flags, one per line, to `$SCRATCH/lint-flags`:

```bash
python3 - "$FND/Cargo.toml" > "$SCRATCH/lint-flags" <<'EOF'
import sys, tomllib

# Rendered foundation lints -> clippy flags. Groups carry priority -1 and come
# first, so the named lints after them win. rustdoc lints are not clippy's.
lints = tomllib.load(open(sys.argv[1], "rb"))["lints"]
rows = []
for tool, prefix in (("rust", ""), ("clippy", "clippy::")):
    for name, spec in lints.get(tool, {}).items():
        spec = spec if isinstance(spec, dict) else {"level": spec}
        flag = "-A" if spec["level"] == "allow" else "-W"  # a survey never denies
        rows.append((spec.get("priority", 0), flag, prefix + name))
for _, flag, lint in sorted(rows, key=lambda r: r[0]):
    print(flag, lint)
EOF
```

Read the flag list off the run. It is recorded in the report. In shape it is:

| Part of the foundation policy | Flags | Effect |
|-------------------------------|-------|--------|
| Clippy groups (`all`, `pedantic`, `nursery`) | `-W clippy::<group>` | Idiom, clarity, numeric-cast discipline, and newer, less-settled lints. `nursery` findings carry lower confidence |
| Named Clippy lints (`unwrap_used`, `indexing_slicing`, `arithmetic_side_effects`, …) | `-W clippy::<lint>` | Individual `restriction` lints: panics and silent wrap-around in production code |
| rustc lints (`unused_lifetimes`, …) | `-W <lint>` | Compiler lints that pair with a pedantic policy |

`--locked` is on by default in `ops clippy-findings`: Cargo fails instead of writing
`Cargo.lock`. Both passes carry it, because a lint run that resolves dependencies has
modified the tree, which this skill promises not to do. Never pass `--no-locked`.

Deliberately **not** enabled:

| Flag | Why not |
|------|---------|
| `-D warnings` | Denying aborts at the first warning and truncates the survey |
| `-W clippy::restriction` | Not a lint group to enable wholesale. It contains mutually contradictory lints (`clippy::else_if_without_else` alongside `clippy::implicit_return`). The foundation names the restriction lints it wants one by one |
| `-W clippy::cargo` | Not part of the foundation policy. Manifest hygiene findings would be filed that the applied policy never enforces |
| `--fix` | Mutates the tree. This skill never does |

`clippy::correctness`, `suspicious`, `style`, `complexity`, and `perf` are on by default and
so appear in the baseline run too. Findings from them are labelled `clippy-default`.

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
`missing_docs_in_private_items` is **not** listed: it is a `restriction` lint the foundation
does not name, so it cannot appear in a run.

### Class J — judgement (~15 min per instance)

Each instance is a real decision that a human has to make, and getting it wrong changes
behaviour. Never batch-apply these.

`cast_possible_truncation`, `cast_sign_loss`, `cast_precision_loss`, `cast_lossless`,
`cast_possible_wrap`, `checked_conversions`, `float_cmp`, `similar_names`,
`unreadable_literal` (where the grouping is domain-meaningful), `struct_excessive_bools`,
`fn_params_excessive_bools`, `option_if_let_else` (nursery — often less readable after).

The foundation's named `restriction` lints are Class J too, with the exceptions below. Each
instance replaces a panic, an index or an unchecked operation with an error path or a checked
one, and choosing what the failure should do is the decision: `unwrap_used`, `expect_used`,
`panic`, `indexing_slicing`, `string_slice`, `arithmetic_side_effects`, `as_conversions`,
`unchecked_time_subtraction`, `unreachable`, `exit`. The exceptions are `todo` and
`unimplemented`, which are Class S, because each marks missing code, not a missing check.
`panic_in_result_fn` is Class S when the fix changes the function's error type. A named lint
this list does not cover is Class J until someone classifies it here.

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
   CRATE_DIR='<manifestDir from the finding row>'   # repo-relative
   PAT='\b<fn_name>\s*(::<[^>]*>)?\s*\('
   calls=$(rg -o --glob '!target/' "$PAT" "$CRATE_DIR" | wc -l)
   decls=$(rg -o --glob '!target/' '\bfn +<fn_name>\b' "$CRATE_DIR" | wc -l)
   echo $(( calls - decls ))
   ```

   More than three → **Class S**; three or fewer → **Class M**.

   Scan the whole crate directory, not just `src/`: the sweep runs `--all-targets`, so the
   lint fires on code in `tests/`, `examples/` and `benches/` too, and those call sites have
   to be fixed alongside the rest. The pattern allows a turbofish (`f::<T>()`), which a
   fixed-string search silently misses — and every miss pushes the count *down*, toward the
   cheaper class, which is the wrong direction for an estimate to be wrong in.

   The number is still a heuristic: `rg` matches inside comments, string literals and doc
   examples, a method call on an unrelated type shares the name, and calls generated by a
   macro appear nowhere. **Read the matches whenever the count lands at three or four, or
   whenever any of them sit in a comment or a doc block** — the threshold decides an effort
   class, and a wrong class quietly skews the estimate for every instance of that lint.

Do not classify this lint on whether the type is `Copy`. Clippy fires it on non-`Copy`
types by design (`trivially_copy_pass_by_ref` is the `Copy` counterpart), so a
`Copy`/non-`Copy` split would leave most instances unassigned.

## Aggregation

A lint firing more than 20 times inside one crate is a pattern, not twenty findings. File it
as one aggregate task listing every `file:line` (see the volume guard in `SKILL.md`). Class M
and Class D lints hit this threshold constantly on a first run; Class S almost never does,
and a Class S lint that *does* fire 20+ times in one crate is itself the headline finding —
the crate needs a structural review, not twenty tasks.
