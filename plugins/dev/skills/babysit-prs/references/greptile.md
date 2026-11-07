# Greptile

Read this when a PR in the snapshot has a non-null `greptile`, or an open thread whose
`last_author` is `greptile-apps`.

## Where Greptile writes

- **Summary**: Greptile edits its summary into the PR description, between
  `<!-- greptile_comment -->` and `<!-- /greptile_comment -->`, and rewrites it after
  every review. The script reads two things from it: the confidence score
  (`<!-- greptile_confidence_score:N -->`, out of 5) and the "Last reviewed commit" link.
  It never posts the summary as a comment, so do not look for one. The skill never
  edits the PR body, and this block above all, because Greptile overwrites it anyway.
- **Findings**: inline review threads, one per finding, by `greptile-apps`. Each opens
  with a severity badge that the script turns into `severity` (`P0`–`P3`) and strips from
  the text, followed by a bold title and the reasoning.
- **Reviews**: `COMMENTED` reviews with empty bodies, one per reviewed commit. They carry no
  content of their own. Greptile never approves or requests changes, so its findings
  do not move `reviewDecision`.

## Acting on findings by severity

Greptile's findings are claims about behaviour, often specific and sometimes wrong.
Check each claim against the code in the worktree before deciding.

| Severity | Treat as | Default |
|----------|----------|---------|
| `P0`, `P1` | A correctness or safety claim | Verify it. If it holds, fix it (Step 3c). If it does not, draft a reply that says why, concretely enough that a reader can check it |
| `P2`, `P3` | Style, clarity, a nit | Fix it when the change is small and clearly better. Otherwise draft a one-line reply. Never let it hold a PR back from `ready` in the report |

A finding can be real and still not worth fixing in this PR. Example: a race window that
cannot be closed, only moved. Say so in the draft, and name the trade-off rather than
just declining.

## Replies and re-reviews

- Greptile reads replies in its own threads and may answer. Its answer becomes the last
  comment, so the thread comes back as undrafted on the next pass. That is intended.
  But if Greptile has answered the user's pushback twice in the same thread, stop
  drafting. Report the thread as needing the user, because a third round with a bot
  rarely settles anything.
- Greptile reviews every push on its own. When the checks are done but `greptile.reviewed_head`
  is false, the PR classifies as `wait-bot`: check back in a few minutes. Do not post a
  mention or open the summary's "Retrigger" link to force a review. Both act under
  the user's name, and the review is usually already on its way.
- Report the score next to the state, for example `ready · Greptile 4/5`. A score of 3 or
  lower with no open threads usually means the summary itself names a concern.
  Quote that concern's one-line reason in the report.
