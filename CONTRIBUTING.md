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
Bumping a tool means editing `.tool-versions`; nothing else hardcodes a version.

## Make a change

Skills live under `skills/<skill-name>/`. Then:

```bash
make lint             # rewrites files: rumdl fmt + check --fix
make ci               # the exact non-mutating gate CI runs
```

Run `make lint` while iterating and `make ci` before pushing. CI runs `fmt-check`,
`lint-check` and `validate` — all non-mutating, so anything `make lint` would have fixed
is a failure there instead.

Validation is `--strict`: warnings fail. Common ones are a `description` that reads as a
keyword list rather than prose, and files placed outside the standard skill layout.

## Commits

Conventional commits: `type(scope): imperative description`, where type is one of `feat`,
`fix`, `docs`, `perf`, `refactor`, `style`, `test`, `build`, `ci`, `chore`. Scope is the
skill name or the affected area. Group related files into one commit rather than staging
everything at once.

## Pull requests

`main` is protected. A pull request needs `Lint`, `Validate` and `Install` green, all
review threads resolved, and signed commits — set up commit signing before your first PR:

```bash
git config commit.gpgsign true
```

Branches must be current with `main` before merging, and history is linear: rebase rather
than merge `main` into your branch.
