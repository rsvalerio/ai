#!/usr/bin/env python3
"""Check the review skills' rule corpus is internally consistent.

Two invariants, both of which fail silently in the skill rather than loudly anywhere:

1. **Index parity** — every rule in `references/rules/<CAT>.md` has a line in
   `references/rules/index.md`, and vice versa. The index is maintained by hand
   (AGENTS.md explains why), so drift is a matter of someone forgetting.

2. **Category reachability** — a scan reads tier 1 then tier 3, so a category is
   reachable only if `scan-checklist.md` names one of its rule IDs in the signal
   table, or lists it in the Sweep section. A category in neither is invisible to a
   review: its file is never opened and its rules are never applied. A category in
   both is a stale Sweep entry.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = ("code-review-rust", "code-review-web")

RULE_ID = re.compile(r"\*\*([A-Z][A-Z0-9]*)-(\d+)\.?\*\*")
CHECKLIST_ID = re.compile(r"\b([A-Z][A-Z0-9]*)-(\d+)(?:--(\d+))?\b")
SWEEP_ENTRY = re.compile(r"^- \[`rules/([A-Z][A-Z0-9]*)\.md`\]")
SWEEP_HEADING = re.compile(r"^##\s+Sweep\b")


def rule_ids(text: str) -> set[str]:
    return {f"{p}-{n}" for p, n in RULE_ID.findall(text)}


def parse_sweep(checklist: str) -> set[str]:
    """Categories listed under the Sweep heading, up to the next heading."""
    out: set[str] = set()
    in_sweep = False
    for line in checklist.splitlines():
        if line.startswith("## "):
            in_sweep = bool(SWEEP_HEADING.match(line))
            continue
        if in_sweep:
            m = SWEEP_ENTRY.match(line)
            if m:
                out.add(m.group(1))
    return out


def signal_categories(checklist: str) -> set[str]:
    """Categories named by a rule ID in the signal table (outside the Sweep section)."""
    table, in_sweep = [], False
    for line in checklist.splitlines():
        if line.startswith("## "):
            in_sweep = bool(SWEEP_HEADING.match(line))
            continue
        if not in_sweep:
            table.append(line)
    return {p for p, _a, _b in CHECKLIST_ID.findall("\n".join(table))}


def check(skill: str, problems: list[str]) -> None:
    refs = REPO / "skills" / skill / "references"
    rules_dir, index, checklist = refs / "rules", refs / "rules" / "index.md", refs / "scan-checklist.md"

    for required in (rules_dir, index, checklist):
        if not required.exists():
            problems.append(f"{skill}: missing {required.relative_to(REPO)}")
            return

    category_files = sorted(p for p in rules_dir.glob("*.md") if p.name != "index.md")
    if not category_files:
        problems.append(f"{skill}: no category files in {rules_dir.relative_to(REPO)}")
        return

    # 1 — index parity
    in_rules = set().union(*(rule_ids(p.read_text()) for p in category_files))
    in_index = rule_ids(index.read_text())
    if not in_rules or not in_index:
        problems.append(f"{skill}: parsed no rule ids — check the '**<CAT>-<N>**' format")
        return
    for rid in sorted(in_rules - in_index):
        problems.append(f"{skill}: {rid} is in rules/ but missing from rules/index.md")
    for rid in sorted(in_index - in_rules):
        problems.append(f"{skill}: {rid} is in rules/index.md but no such rule in rules/")

    # 2 — category reachability
    categories = {p.stem for p in category_files}
    text = checklist.read_text()
    signalled, swept = signal_categories(text) & categories, parse_sweep(text)
    for cat in sorted(swept - categories):
        problems.append(f"{skill}: scan-checklist Sweep lists rules/{cat}.md, which does not exist")
    for cat in sorted(categories - signalled - swept):
        problems.append(
            f"{skill}: rules/{cat}.md is unreachable — no scan-checklist signal names a "
            f"{cat}-* rule and it is not in the Sweep list, so a scan never opens it")
    for cat in sorted(signalled & swept):
        problems.append(
            f"{skill}: rules/{cat}.md has both a scan-checklist signal and a Sweep entry — "
            f"remove the Sweep entry")


def main() -> int:
    problems: list[str] = []
    for skill in SKILLS:
        check(skill, problems)
    if problems:
        for line in problems:
            print(line, file=sys.stderr)
        print(f"\nrule corpus invalid: {len(problems)} problem(s)", file=sys.stderr)
        return 1
    print(f"rule corpus consistent: index parity and category reachability for {', '.join(SKILLS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
