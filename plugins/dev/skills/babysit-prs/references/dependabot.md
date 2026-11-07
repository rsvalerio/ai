# Dependabot

Read this when a PR in the snapshot has `kind: "dependabot"`.

## Which PRs

The snapshot includes open Dependabot PRs only in repos the user has a local clone of
and can push to. A read-only clone of someone else's project is not the user's to
babysit, and a Dependabot PR in a repo with no checkout is usually an abandoned
experiment. Both are left out rather than reported as noise.

## Who owns the branch

`bot_managed` is true while every commit on the branch is Dependabot's. That changes
how to rebase:

- **Bot-managed**: Dependabot rebases and regenerates its own branch. Do not rebase or
  force-push it yourself. Ask Dependabot to:

  ```bash
  gh pr comment "$N" -R "$REPO" --body "@dependabot rebase"
  python3 scripts/pr-state.py --record bot-rebase "$REPO#$N" - "$HEAD_OID"
  ```

  This is the one comment a pass may post unattended. It is a command to the user's own
  bot on the user's own repo, not a reply anyone reads. Recording it makes later passes
  classify the PR as `wait-bot` until Dependabot pushes a new head, so the request is
  never repeated.
- **Edited** (`bot_managed` false, because someone pushed a commit): Dependabot stops
  rebasing a branch it no longer owns, and `@dependabot rebase` would be refused.
  Rebase it like any other PR (Step 3a).

## Failing CI on a bump

Read the log first, as for any PR. The cause is usually one of three things:

- **The new version broke something** (an API change, a new lint, an MSRV raise): fix the
  code in the worktree and push to the Dependabot branch, with a commit like
  `fix(deps): adapt to <crate> <version>`. Pushing ends Dependabot's ownership of the
  branch, so say so in the report. When the fix is a migration rather than a patch
  (a major version with renamed APIs across many files), do not attempt it. Report it
  as needing the user, because choosing to take a major upgrade is their call.
- **A lockfile or duplicate-version conflict with another open bump**: report which PR to
  merge first. Do not change either PR to work around the other.
- **Infrastructure**: re-run once, as for any PR.

## What stays with the user

Never post `@dependabot merge`, `squash and merge`, `recreate`, `ignore` or `close`.
Merging is never done unattended. `recreate` discards any commits pushed to the branch.
`ignore` and `close` change which updates the repo receives at all. Each is a policy
decision, not babysitting.

Report a green bot-managed Dependabot PR as `ready`. These are often the quickest merges in
the list, so put them where the user will see them.
