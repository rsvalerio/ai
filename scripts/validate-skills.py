#!/usr/bin/env python3
"""Run skill-validator over every skill and fail on anything not allowlisted.

Every skill directory (plugins/*/skills/*/ and skills/*/) is validated, not only those that already
contain a SKILL.md: filtering on SKILL.md would let a skill directory missing its
manifest pass by being skipped, which is the same silent-pass bug this script exists
to remove.

`skill-validator --strict` exits 1 on warnings as well as errors, but the loop it
replaces in the Makefile discarded every per-skill exit code except the last one,
so `make validate` reported success while four skills were failing. This script
propagates failures and carries the single exception the corpus genuinely cannot
satisfy (see ALLOWED below).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Skills live in plugins/<plugin>/skills/<skill>/, plus an optional top-level
# skills/<skill>/ for standalone skills that belong to no plugin. Globbing both means
# a new plugin needs no change here.
SKILL_GLOBS = ("plugins/*/skills/*", "skills/*")

# (skill name, exact validator message) pairs that are accepted as warnings.
#
# deep nesting / references/rules/: unfixable, and verified so. Flattening the
# rule corpus to references/rules-<CAT>.md turns these files into counted
# top-level references, which trips a hard error from the same validator:
#
#     total reference files: 74055 tokens — reduce content or split into a
#     skill with fewer references
#
# That error fails even without --strict. The nesting is what keeps ~50k tokens
# of rule text out of the counted budget, so the warning and the error cannot
# both be satisfied without deleting rules. Nesting is the cheaper of the two.
ALLOWED: set[tuple[str, str]] = {
    ("code-review-rust", "deep nesting detected: references/rules/"),
    ("code-review-web", "deep nesting detected: references/rules/"),
}


def main() -> int:
    skills = sorted(p for g in SKILL_GLOBS for p in REPO.glob(g) if p.is_dir())
    if not skills:
        print(f"no skill directories matching {', '.join(SKILL_GLOBS)}", file=sys.stderr)
        return 1
    names = [p.name for p in skills]
    clashes = sorted({n for n in names if names.count(n) > 1})
    if clashes:
        # `make link` installs every skill into one flat ~/.claude/skills/, so two
        # plugins shipping the same skill name would overwrite each other there.
        print(f"skill names must be unique across plugins: {', '.join(clashes)}", file=sys.stderr)
        return 1
    failed: list[str] = []
    stale = set(ALLOWED)

    for skill in skills:
        proc = subprocess.run(
            ["skill-validator", "validate", "structure", "--strict", "-o", "json", str(skill)],
            capture_output=True,
            text=True,
        )
        try:
            report = json.loads(proc.stdout)
        except json.JSONDecodeError:
            print(f"{skill.name}: could not parse validator output", file=sys.stderr)
            print(proc.stdout or proc.stderr, file=sys.stderr)
            failed.append(skill.name)
            continue

        problems = [
            r for r in report.get("results", []) if r.get("level") in ("error", "warning")
        ]
        unexpected = []
        for r in problems:
            key = (skill.name, r.get("message", ""))
            if r["level"] == "warning" and key in ALLOWED:
                stale.discard(key)
                print(f"{skill.name}: allowed — {r['message']}")
            else:
                unexpected.append(r)

        for r in unexpected:
            print(f"{skill.name}: {r['level']} — {r.get('message', '')}", file=sys.stderr)
        if unexpected:
            failed.append(skill.name)

    # An allowlist entry that no longer fires is a rule someone fixed; drop it
    # rather than leaving a licence to regress.
    for name, message in sorted(stale):
        print(f"{name}: allowlist entry no longer fires, remove it — {message}", file=sys.stderr)
    if stale:
        return 1

    if failed:
        print(f"\nvalidation failed: {', '.join(failed)}", file=sys.stderr)
        return 1

    print(f"all {len(skills)} skills valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
