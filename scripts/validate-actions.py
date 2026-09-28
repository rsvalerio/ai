#!/usr/bin/env python3
"""Fail if a workflow uses a third-party action that is not SHA-pinned.

Mirrors forge's `ci/lint.sh pinned-actions` (forge README design rule 6): every
third-party `uses:` names a full 40-hex commit SHA followed by its version tag in a
comment, e.g. `actions/checkout@<sha> # v7.0.1`. A tag ref can be moved to point at
unreviewed code; a SHA cannot. Local (`./`) and forge's own (`rsvalerio/forge/`) refs
are exempt, as they are in forge. Dependabot (.github/dependabot.yml) moves the SHA
and its comment together, so a bump PR still passes.

forge's check is repo-local; replace this copy with the shared lint once forge
ships one that consumers can call.
"""

import pathlib
import re
import sys

USES = re.compile(r"^\s*(?:-\s+)?uses:\s*(.+?)\s*$")
PINNED = re.compile(r"^[^@\s]+@[0-9a-f]{40}\s+#\s*v[0-9]\S*")
EXEMPT = ("./", "rsvalerio/forge/")


def main() -> int:
    files = sorted(pathlib.Path(".github/workflows").glob("*.y*ml"))
    files += sorted(pathlib.Path(".").glob("actions/*/action.yml"))
    failed = False
    for path in files:
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            match = USES.match(line)
            if not match:
                continue
            ref = match.group(1).replace('"', "").replace("'", "")
            if ref.startswith(EXEMPT) or PINNED.match(ref):
                continue
            print(f"{path}:{lineno}: not SHA-pinned with a version comment: {ref}")
            failed = True
    if not failed:
        print(f"all actions SHA-pinned ({len(files)} file(s))")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
