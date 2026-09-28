---
id: TASK-0004
title: 'Restructure the repo into a multi-plugin monorepo: plugins/dev (was dev-skills) and plugins/product'
status: To Do
assignee: []
created_date: '2026-09-27 14:02'
labels:
  - monorepo
  - plugins
dependencies: []
modified_files:
  - .claude-plugin/marketplace.json
  - .claude-plugin/plugin.json
  - Makefile
  - scripts/validate-skills.py
  - scripts/validate-rules.py
  - .github/workflows/ci.yml
  - README.md
  - AGENTS.md
  - CONTRIBUTING.md
priority: medium
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**What**: Turn the repo from "the root is one plugin" into a multi-plugin monorepo: the marketplace stays at the root and each plugin lives under `plugins/<name>/`. The existing `dev-skills` plugin becomes `dev`. A second plugin, `product`, gets an empty scaffold so the new-skill task has somewhere to land.

**Why**: `~/Projects/ai` is the home for all AI tooling (plugins, skills, agents), not only the Rust/frontend review set. Today `.claude-plugin/plugin.json` sits at the root with `"source": "./"`, so every directory under `skills/` ships inside `dev-skills`. A second plugin can't exist without cutting into the first.

**Backward compatibility is out of scope.** The owner will uninstall `dev-skills@rsvalerio` and install the new plugins by hand. Don't add aliases, redirects or a `dev-skills` shim.

**Target layout**

```text
ai/
├── .claude-plugin/marketplace.json   # only manifest at the root; lists dev + product
├── plugins/
│   ├── dev/
│   │   ├── .claude-plugin/plugin.json
│   │   ├── skills/                   # the nine current skills, moved from skills/
│   │   └── evals/                    # moved from evals/
│   └── product/
│       ├── .claude-plugin/plugin.json
│       └── skills/                   # empty until the product-research task lands
├── skills/  agents/                  # optional: standalone items that belong to no plugin (create only if needed)
├── docs/  scripts/  Makefile  AGENTS.md  README.md  CONTRIBUTING.md
```

**Things that hard-code the old layout**:
- `Makefile`: `SKILLS_DIR := skills`, and the `link`/`unlink`/`eval` targets.
- `scripts/validate-skills.py` and `scripts/validate-rules.py`, which uses `REPO / "skills" / skill`.
- `.github/workflows/ci.yml`: the validate and link steps loop over `skills/*/`.
- `evals/`: `claude plugin eval .` resolves the root `plugin.json`. It must run per plugin, e.g. `claude plugin eval plugins/dev`.
- The string `dev-skills` in `README.md`, `AGENTS.md` and both manifests.
- The README's `agent-skills install …/tree/main/skills/<name>` URLs.

The validators and link targets should discover skills with the glob `plugins/*/skills/*/` (plus top-level `skills/*/` if that folder exists), so a third plugin needs no Makefile edit.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Root holds only .claude-plugin/marketplace.json, listing two plugins: dev (source ./plugins/dev) and product (source ./plugins/product)
- [ ] #2 The nine existing skills live under plugins/dev/skills/ and their evals under plugins/dev/evals/; no skill content changes beyond path fixes
- [ ] #3 plugins/product/.claude-plugin/plugin.json exists, with a description for product and market research skills
- [ ] #4 No reference to dev-skills remains anywhere in the repo
- [ ] #5 Makefile validate/link/unlink/eval, scripts/validate-skills.py, scripts/validate-rules.py and CI discover skills with the plugins/*/skills/*/ glob
- [ ] #6 make ci passes, claude plugin validate passes for the marketplace and both plugins, and make link symlinks every skill
- [ ] #7 README and AGENTS.md describe the monorepo layout, how to add a plugin, and the install commands dev@rsvalerio and product@rsvalerio
<!-- AC:END -->
