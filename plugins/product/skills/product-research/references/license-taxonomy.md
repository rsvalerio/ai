# License Taxonomy

How to classify a component's license, and how to read it. Evidence requirements come from
[evidence-contract.md](evidence-contract.md).

## Classes

| Class | Meaning | Common examples (SPDX) |
|-------|---------|------------------------|
| **permissive** | OSI-approved; redistribution and modification with notice only | `MIT`, `BSD-2-Clause`, `BSD-3-Clause`, `Apache-2.0`, `ISC` |
| **weak copyleft** | OSI-approved; changes to the licensed files must be shared, larger works need not be | `MPL-2.0`, `LGPL-2.1`, `LGPL-3.0`, `EPL-2.0` |
| **strong copyleft** | OSI-approved; derived works must be shared under the same license, and for network copyleft that includes offering it as a service | `GPL-2.0`, `GPL-3.0`, `AGPL-3.0` |
| **source-available** | Source is published, but the license is not OSI-approved: use, competition or hosting is restricted | `BUSL-1.1` (BSL), `SSPL-1.0`, `Elastic-2.0`, Commons Clause riders, fair-source licenses such as FSL, PolyForm |
| **proprietary** | No source published, or published with no license granting use | Closed binaries, SaaS-only backends, source with "all rights reserved" |
| **unknown** | No license could be established at a pinned ref | A repo with no LICENSE file; conflicting license statements |

Rules:

- **`unknown` is never treated as permissive.** Code with no license grants no rights. An
  `unknown` component is recorded as `unknown`, with the check that would settle it.
- **Source-available is not open source.** Record the class, and say what the license
  restricts: competing offerings, hosting, production use, or a use threshold. Where the
  license converts after a delay (BSL's change date and change license, FSL's
  conversion), record both the current terms and the conversion.
- Record the **SPDX identifier** where there is one. Otherwise record the license name and
  the path of the file.
- **Dual license** — both are recorded, with who gets which (for example, "AGPL-3.0 or a
  commercial license").

## Reading a License Per Component

A product is rarely one license. Read each component separately: client, agent, server,
control plane, SDKs, and enterprise directory.

1. **Pin the ref.** Resolve the latest release tag to a commit (`git ls-remote --tags`, or
   `gh api repos/<o>/<r>/releases/latest`). Record the tag and the commit.
2. **Read the LICENSE at that ref.** Use `gh api repos/<o>/<r>/contents/LICENSE?ref=<sha>`,
   or the `/blob/<sha>/LICENSE` URL. Not the default branch, which moves; not the badge;
   not GitHub's detected-license label.
3. **Check for split licensing inside one repository.** Look for per-directory LICENSE
   files, an `ee/` or `enterprise/` directory with its own terms, license headers that
   differ from the root file, and a README section on licensing. Monorepos that are open
   at the root and source-available under `ee/` are common.
4. **Components with no published source** — a closed server with an open client often
   has no server repository at all. There is no LICENSE file to read, so the evidence is
   the one the [evidence contract](evidence-contract.md) sets for unpublished components:
   the vendor's own statement that the component is closed or hosted-only, **and** a
   search showing no source is published. With both, record the class `proprietary`; with
   either missing, `unknown`. Availability (`hosted-only`, `paid`) is recorded separately in
   the business model; it is not what establishes the license class.
5. **Package-registry metadata** (crates.io, npm, PyPI, Docker Hub) is a cross-check. When
   it disagrees with the LICENSE file, record the disagreement as an unknown; do not pick
   one.

## License History

Relicensing is the fact most often missed, and the one that most often makes a record
wrong. Every run checks for it:

- Search the vendor's blog and the repository's history for "license" around major
  releases. Diff the LICENSE file between the oldest and newest tags you can reach.
- Record each change with its **date**, the **last ref under the old license**, the new
  license, and the announcement.
- Record **forks triggered by the change**, with their governance (foundation, company,
  individuals). For example, after HashiCorp moved Terraform and Vault from MPL-2.0 to
  BSL 1.1 in 2023, OpenTofu and OpenBao forked from the last MPL releases. Fork facts go
  through [business-model.md](business-model.md) § Forks and rebuilds.

A product with no license change found says so: `License history: no change found in
<refs checked>, checked <date>`. Silence is not the same as a clean history.
