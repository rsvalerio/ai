# Contributing

This repository publishes [Agent Skills](https://agentskills.io/specification). Conventions
for authoring skills live in [AGENTS.md](AGENTS.md); this file covers how a change gets
from your checkout to `main`.

## Set up

```bash
mise install         # or: make install-tools (Homebrew)
make check-tools     # confirm they match .tool-versions
```

`mise install` is the portable path and reads `.tool-versions` directly;
`make install-tools` is a Homebrew convenience and installs whatever brew has as
current, so `check-tools` may tell you to pin it back.

`.tool-versions` pins the versions CI runs. If `check-tools` fails, your local gates are
not the gates that will run on your pull request — fix that before trusting a green run.
Bumping a tool means editing `.tool-versions`; nothing else hardcodes a version. The one
exception is `claude-code`, pinned only in the `ops qa` job of
`.github/workflows/ci.yml` — mise's registry does not know the tool, so a `.tool-versions`
entry would fail `mise install` in CI. Locally, manage it with asdf instead, outside this
repo's `.tool-versions` for the same reason:

```bash
asdf plugin add claude-code https://github.com/wguilherme/asdf-claude-code.git
asdf install claude-code 2.1.235 && asdf set --home claude-code 2.1.235
```

Any recent `claude-code` on PATH also works — the CI pin is for reproducible validation,
not a documented minimum for marketplace plugins.

## Make a change

Skills live under `skills/<skill-name>/`. Then:

```bash
make lint             # rewrites files: rumdl fmt + check --fix
ops verify            # fast offline gate: fine as a pre-commit hook
ops qa                # the full gate: verify, plus the marketplace and the install path
```

Run `make lint` while iterating, `ops verify` as often as you like, and `ops qa` before
pushing. CI runs both, as the `ops verify` and `ops qa` checks. `.ops.toml` is the one list
of their steps:

| Gate | Steps |
|------|-------|
| `ops verify` | `check-tools`, `validate` (skills), `validate-rules`, `lint-actions` (ops built-in: SHA pins with a version comment, no `secrets: inherit`), `fmt-check`, `lint-check` |
| `ops qa` | `verify`, plus `validate-marketplace` (needs `claude-code` on PATH) and `check-install` |

Every step is a Makefile target and non-mutating, so anything `make lint` would have fixed
is a failure there instead. `make ci` runs the `ops qa` checks without
[ops](https://github.com/rsvalerio/ops) or the tool-version check.

Validation is `--strict`: warnings fail. Common ones are a `description` that reads as a
keyword list rather than prose, and files placed outside the standard skill layout.

## Commits

Conventional commits: `type(scope): imperative description`, where type is one of `feat`,
`fix`, `docs`, `perf`, `refactor`, `style`, `test`, `build`, `ci`, `chore`. Scope is the
skill name or the affected area. Group related files into one commit rather than staging
everything at once.

## Pull requests

`main` is protected. A pull request needs `ops verify` and `ops qa`
green, all review threads resolved, and signed commits — set up commit signing before
your first PR:

```bash
git config commit.gpgsign true
```

Branches must be current with `main` before merging, and history is linear: rebase rather
than merge `main` into your branch.
