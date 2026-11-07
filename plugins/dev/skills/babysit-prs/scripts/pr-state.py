#!/usr/bin/env python3
"""Snapshot the user's open PRs, with the one next step each needs.

"The user's PRs" means every open PR they authored, plus open Dependabot PRs in
repos that have a local clone (a Dependabot PR in a repo with no checkout is
usually an abandoned fork or archive, and nothing can be done about it here)
and the user can push to (a read-only clone of an upstream project is not theirs
to babysit).

Usage:
    pr-state.py                    # query GitHub through `gh`
    pr-state.py --from FILE.json   # classify a saved snapshot (tests, replays);
                                   # its optional "clones"/"state" keys replace the
                                   # clone scan and the state file
    pr-state.py --save FILE.json   # also write the raw snapshot for --from
    pr-state.py --record drafted OWNER/REPO#N THREAD_ID COMMENT_ID < reply.md
    pr-state.py --record ci-attempt OWNER/REPO#N CHECK_NAME HEAD_OID
    pr-state.py --record bot-rebase OWNER/REPO#N - HEAD_OID

Prints one JSON document: {"login", "generated_at", "prs": [...]}. Each PR carries
`clone` (local checkout or null), `failing_checks`, `pending_checks`,
`open_threads` (unresolved, last word not the user's), `merge_state` and
`next`, the classification SKILL.md acts on. A thread whose reply is already
recorded carries `drafted: true` and the saved `draft` text, so a /loop pass
re-presents it instead of drafting it twice, and
each failing check carries `attempts`: how many fixes this skill already pushed
for it, so a pass can stop instead of retrying forever.

Bot fields: `kind` is "own" or "dependabot"; a Dependabot PR carries
`bot_managed` (every commit is Dependabot's, so `@dependabot rebase` is still
safe) and `rebase_requested` (a `@dependabot rebase` was already posted at
this head, so the pass waits for Dependabot's push). `greptile` is null unless Greptile reviewed the PR, else its confidence
score, the commit it last reviewed and whether that is the head. A Greptile
thread carries `severity` ("P0".."P3") from its badge, with the badge markup
stripped from the comment bodies.

Clone roots come from $BABYSIT_PRS_ROOTS (colon-separated), default ~/projects.
State lives in ${XDG_STATE_HOME:-~/.local/state}/babysit-prs/state.json.
"""

import argparse
import datetime
import fcntl
import json
import os
import pathlib
import re
import subprocess
import sys

QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    viewerPermission
    pullRequest(number: $number) {
      number title url isDraft state body
      author { login }
      headRefName headRefOid baseRefName
      headRepository { nameWithOwner }
      mergeable mergeStateStatus reviewDecision
      commits(last: 1) { nodes { commit { statusCheckRollup { contexts(first: 100) { nodes {
        __typename
        ... on CheckRun { name status conclusion detailsUrl }
        ... on StatusContext { context state targetUrl }
      } } } } } }
      history: commits(last: 50) { nodes { commit { author { name } } } }
      reviews(last: 50) { nodes { author { login } commit { oid } } }
      reviewThreads(first: 100) { nodes {
        id isResolved isOutdated path line
        comments(last: 20) { nodes { databaseId author { login } body createdAt url } }
      } }
    }
  }
}
"""

FAILED = {"FAILURE", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED", "STARTUP_FAILURE", "ERROR"}
MAX_ATTEMPTS = 2  # fixes pushed for one check before the pass hands it to the user
WRITERS = {"ADMIN", "MAINTAIN", "WRITE"}
GREPTILE = "greptile-apps"
DEPENDABOT = "dependabot"  # GraphQL login of the app; commits say "dependabot[bot]"
PENDING = {"QUEUED", "IN_PROGRESS", "PENDING", "WAITING", "REQUESTED", "EXPECTED"}


def gh(*args):
    out = subprocess.run(["gh", *args], check=True, capture_output=True, text=True)
    return json.loads(out.stdout)


def fetch(clones):
    login = gh("api", "user")["login"]
    found = gh("search", "prs", "--author=@me", "--state=open", "--limit", "100",
               "--json", "repository,number")
    owners = sorted({slug.split("/")[0] for slug in clones})
    if owners:
        bot = gh("search", "prs", "--author=app/dependabot", "--state=open", "--limit", "100",
                 *[f"--owner={o}" for o in owners], "--json", "repository,number")
        found += [h for h in bot if h["repository"]["nameWithOwner"].lower() in clones]
    prs = []
    for hit in found:
        owner, name = hit["repository"]["nameWithOwner"].split("/")
        data = gh("api", "graphql", "-f", f"query={QUERY}", "-F", f"owner={owner}",
                  "-F", f"name={name}", "-F", f"number={hit['number']}")
        repo = data["data"]["repository"]
        pr = repo["pullRequest"]
        if pr["author"]["login"] == DEPENDABOT and repo["viewerPermission"] not in WRITERS:
            continue  # a clone of someone else's repo: their dependency PRs, not ours
        pr["repo"] = f"{owner}/{name}"
        prs.append(pr)
    return {"login": login, "clones": clones, "prs": prs}


def clone_index():
    roots = os.environ.get("BABYSIT_PRS_ROOTS", str(pathlib.Path.home() / "projects"))
    index = {}
    for root in filter(None, roots.split(":")):
        root = pathlib.Path(root).expanduser()
        if not root.is_dir():
            continue
        for d in [root, *sorted(p for p in root.glob("*") if p.is_dir()),
                  *sorted(p for p in root.glob("*/*") if p.is_dir())]:
            if not (d / ".git").exists():
                continue
            url = subprocess.run(["git", "-C", str(d), "remote", "get-url", "origin"],
                                 capture_output=True, text=True).stdout.strip()
            slug = url.removesuffix(".git").replace(":", "/").split("/")[-2:]
            if len(slug) == 2:
                index.setdefault("/".join(slug).lower(), str(d))
    return index


def state_path():
    base = os.environ.get("XDG_STATE_HOME", str(pathlib.Path.home() / ".local/state"))
    return pathlib.Path(base) / "babysit-prs" / "state.json"


def load_state():
    try:
        return json.loads(state_path().read_text())
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as e:
        # Starting empty forgets drafts and attempt counts; say so rather than silently.
        print(f"pr-state: ignoring unreadable {state_path()}: {e}", file=sys.stderr)
        return {}


def record(kind, ref, key, value):
    # Two /loop passes can record at once: hold a lock across read-modify-write, and
    # replace the file atomically so a crash never leaves a truncated state behind.
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    body = sys.stdin.read() if kind == "drafted" else None
    with open(path.with_suffix(".lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = load_state()
        update(state, kind, ref, key, value, body)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2))
        os.replace(tmp, path)


def update(state, kind, ref, key, value, body):
    repo, number = ref.rsplit("#", 1)
    pr = state.setdefault(repo, {}).setdefault(number, {})
    if kind == "drafted":
        pr.setdefault("drafted", {})[key] = {"comment_id": int(value), "body": body}
    elif kind == "bot-rebase":
        if value not in pr.setdefault("rebase_requested", []):
            pr["rebase_requested"].append(value)
    else:
        oids = pr.setdefault("ci_attempts", {}).setdefault(key, [])
        if value not in oids:
            oids.append(value)


def checks(pr):
    nodes = pr["commits"]["nodes"]
    ctx = nodes[0]["commit"]["statusCheckRollup"] if nodes else None
    failing, pending = [], []
    for c in (ctx or {}).get("contexts", {}).get("nodes", []):
        if c["__typename"] == "CheckRun":
            row = {"name": c["name"], "url": c.get("detailsUrl")}
            if c["status"] != "COMPLETED":
                pending.append(row)
            elif c.get("conclusion") in FAILED:
                failing.append(row)
        else:
            row = {"name": c["context"], "url": c.get("targetUrl")}
            if c["state"] in PENDING:
                pending.append(row)
            elif c["state"] in FAILED:
                failing.append(row)
    return failing, pending


BADGE = re.compile(r'<a [^>]*>\s*<img alt="(P\d)"[^>]*>\s*</a>\s*|<img alt="(P\d)"[^>]*>\s*')


def debadge(body):
    """Greptile prefixes each finding with a severity badge; return (severity, text)."""
    m = BADGE.search(body)
    return (m.group(1) or m.group(2) if m else None), BADGE.sub("", body).strip()


def greptile(pr):
    reviews = [r for r in pr.get("reviews", {}).get("nodes", [])
               if (r.get("author") or {}).get("login") == GREPTILE]
    body = pr.get("body") or ""
    if not reviews and "greptile_comment" not in body:
        return None
    score = re.search(r"greptile_confidence_score:(\d)", body)
    last = re.search(r"Last reviewed commit:.*?/commit/([0-9a-f]{40})", body)
    last = last.group(1) if last else (reviews[-1]["commit"]["oid"] if reviews else None)
    return {"confidence": int(score.group(1)) if score else None,
            "last_reviewed": last, "reviewed_head": last == pr["headRefOid"]}


def open_threads(pr, login, drafted):
    out = []
    for t in pr["reviewThreads"]["nodes"]:
        comments = t["comments"]["nodes"]
        if t["isResolved"] or not comments or comments[-1]["author"]["login"] == login:
            continue
        last = comments[-1]
        saved = drafted.get(t["id"]) or {}
        fresh = saved.get("comment_id") == last["databaseId"]
        severity, _ = debadge(comments[0]["body"])
        out.append({
            "id": t["id"], "path": t["path"], "line": t["line"], "outdated": t["isOutdated"],
            "url": last["url"], "last_author": last["author"]["login"],
            "severity": severity if comments[0]["author"]["login"] == GREPTILE else None,
            "comments": [{"author": c["author"]["login"], "body": debadge(c["body"])[1]}
                         for c in comments],
            "drafted": fresh, "draft": saved.get("body") if fresh else None,
            "last_comment_id": last["databaseId"],
        })
    return out


def classify(pr):
    """The single most useful next step; SKILL.md 'Step 3' acts on it."""
    if pr["kind"] == "dependabot" and pr["merge_state"] in ("DIRTY", "BEHIND") \
            and pr["bot_managed"]:
        return "wait-bot" if pr["rebase_requested"] else "dependabot-rebase"
    if pr["merge_state"] == "DIRTY":
        return "rebase"
    if any(c["attempts"] < MAX_ATTEMPTS for c in pr["failing_checks"]):
        return "fix-ci"
    if any(not t["drafted"] for t in pr["open_threads"]):
        return "address-review"
    if pr["failing_checks"]:
        return "stuck"
    if pr["merge_state"] == "BEHIND":
        return "rebase"
    if pr["pending_checks"]:
        return "wait-ci"
    if pr["greptile"] and not pr["greptile"]["reviewed_head"]:
        return "wait-bot"
    if pr["open_threads"]:
        return "await-approval"
    if pr["isDraft"]:
        return "draft"
    if pr["reviewDecision"] in ("REVIEW_REQUIRED", "CHANGES_REQUESTED"):
        return "wait-review"
    return "ready"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src")
    ap.add_argument("--save")
    ap.add_argument("--record", nargs=4, metavar=("KIND", "REPO#N", "KEY", "VALUE"))
    args = ap.parse_args()
    if args.record:
        if args.record[0] not in ("drafted", "ci-attempt", "bot-rebase"):
            ap.error("--record KIND is drafted, ci-attempt or bot-rebase")
        record(*args.record)
        return

    raw = json.loads(pathlib.Path(args.src).read_text()) if args.src else fetch(clone_index())
    if args.save:
        pathlib.Path(args.save).write_text(json.dumps(raw, indent=2))

    clones = raw.get("clones") or clone_index()
    state = raw["state"] if "state" in raw else load_state()
    prs = []
    for pr in raw["prs"]:
        failing, pending = checks(pr)
        saved = state.get(pr["repo"], {}).get(str(pr["number"]), {})
        drafted = saved.get("drafted", {})
        for c in failing:
            c["attempts"] = len(saved.get("ci_attempts", {}).get(c["name"], []))
        is_bot = (pr.get("author") or {}).get("login") == DEPENDABOT
        authors = {n["commit"]["author"]["name"] for n in pr.get("history", {}).get("nodes", [])}
        row = {
            "kind": "dependabot" if is_bot else "own",
            "bot_managed": is_bot and authors <= {"dependabot[bot]"},
            "rebase_requested": pr["headRefOid"] in saved.get("rebase_requested", []),
            "greptile": greptile(pr),
            "repo": pr["repo"], "number": pr["number"], "title": pr["title"], "url": pr["url"],
            "isDraft": pr["isDraft"], "head": pr["headRefName"], "head_oid": pr["headRefOid"],
            "base": pr["baseRefName"],
            "head_repo": (pr.get("headRepository") or {}).get("nameWithOwner", pr["repo"]),
            "clone": clones.get(pr["repo"].lower()),
            "merge_state": pr["mergeStateStatus"], "reviewDecision": pr["reviewDecision"],
            "failing_checks": failing, "pending_checks": pending,
            "open_threads": open_threads(pr, raw["login"], drafted),
        }
        row["next"] = classify(row)
        prs.append(row)

    json.dump({"login": raw["login"],
               "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "prs": prs}, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
