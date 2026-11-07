#!/usr/bin/env python3
"""Run `claude plugin validate` over the marketplace and every plugin; fail on anything not allowlisted.

The Makefile loop this replaces passed as long as the validator exited 0, so its
warnings scrolled by on every run and a new one was indistinguishable from the
expected ones. This script reads the validator's --json report instead: every
warning (manifest warnings and plugin-directory findings alike) must match an
ALLOWED entry, and an entry that stops firing fails the build too, so the
allowlist cannot outlive the reason for it.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

VERSION = 'No version specified. Consider adding a version following semver (e.g., "1.0.0")'

# (target, warning) pairs accepted as warnings. The target is "marketplace" or the
# plugin directory name; the warning is the manifest message, or the finding code
# for a plugin-directory check.
#
# No version: deliberate. Installs track the commit SHA, so pushing to main is the
# release (AGENTS.md, Publishing); a version field would have to be bumped by hand
# on every push and would be wrong whenever someone forgot.
#
# ICON_MISSING: deferred, not unfixable. The plugin directory takes a plugin's icon
# only the first time it is submitted, so a placeholder could become the permanent
# listing icon. Add a real .claude-plugin/icon.png before submitting; this entry then
# stops firing and must be removed.
ALLOWED: set[tuple[str, str]] = {
    ("marketplace", VERSION),
    ("dev", VERSION),
    ("product", VERSION),
    ("dev", "ICON_MISSING"),
    ("product", "ICON_MISSING"),
}


def validate(path: Path) -> dict | None:
    # --json needs a claude-code recent enough to have it (2.1.312 does, 2.1.235 does
    # not); ci.yml pins one.
    proc = subprocess.run(
        ["claude", "plugin", "validate", "--json", str(path)], capture_output=True, text=True
    )
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError:
        print(f"{path}: could not parse validator output", file=sys.stderr)
        print(proc.stdout or proc.stderr, file=sys.stderr)
        return None
    report["exit"] = proc.returncode
    return report


def main() -> int:
    targets = [("marketplace", REPO)] + [
        (p.name, p) for p in sorted(REPO.glob("plugins/*/")) if p.is_dir()
    ]
    failed: list[str] = []
    stale = set(ALLOWED)

    for name, path in targets:
        report = validate(path)
        if report is None:
            # No report means no warnings were seen, not that they stopped firing;
            # keep this target's entries out of the stale check so the real error
            # is not buried under "remove it" noise.
            stale -= {entry for entry in stale if entry[0] == name}
            failed.append(name)
            continue
        manifest = report.get("manifest") or {}
        directory = report.get("directory") or {}
        problems = [("error", e.get("path", ""), e.get("message", "")) for e in manifest.get("errors", [])]
        warnings = [(w.get("message", ""), f"{w.get('path')}: {w.get('message')}")
                    for w in manifest.get("warnings", [])]
        warnings += [(f.get("code", ""), f"{f.get('code')}: {f.get('message')}")
                     for f in directory.get("findings", [])]

        for key, text in warnings:
            if (name, key) in ALLOWED:
                stale.discard((name, key))
                print(f"{name}: allowed — {text.splitlines()[0][:100]}")
            else:
                problems.append(("warning", "", text))

        for level, where, message in problems:
            print(f"{name}: {level} — {where + ': ' if where else ''}{message}", file=sys.stderr)
        if problems or report["exit"] != 0 or not report.get("success", False):
            failed.append(name)

    for name, key in sorted(stale):
        print(f"{name}: allowlist entry no longer fires, remove it — {key}", file=sys.stderr)
    if stale:
        return 1

    if failed:
        print(f"\nmarketplace validation failed: {', '.join(failed)}", file=sys.stderr)
        return 1

    print(f"marketplace and all {len(targets) - 1} plugins valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
