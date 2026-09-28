# Business Model

What of a product is open, what is paid, and whether a customer can run all of it
themselves. License classes come from [license-taxonomy.md](license-taxonomy.md);
evidence requirements from [evidence-contract.md](evidence-contract.md).

## Per-Component Split

A business model is recorded per **component**, never as one word for the product. For
each component that exists:

| Component | Examples |
|-----------|----------|
| Client / agent | The thing installed on user devices or hosts |
| Server / data plane | What processes the traffic or data |
| Control plane / coordination | Key distribution, policy, identity brokering, orchestration |
| Management UI / API | Admin console, provisioning API |
| Enterprise features | SSO, SCIM, audit log export, RBAC, HA, support SLAs |
| SDKs / integrations | Libraries and plugins other software links against |

For each component, record:

- **License class** and SPDX id, at a pinned ref.
- **Availability** — `open` (source under an OSI license), `source-available`, `paid`
  (only in a paid plan), `hosted-only` (runs only as the vendor's service), or `unknown`.
  A component can be `open` and also sold as a hosted service; record both.
- **Paid plan it first appears in**, from the pricing page, with the date checked.

## Patterns

Name the pattern the split matches. When none fits, say so and describe the split; do not
force it.

| Pattern | Shape | Illustration |
|---------|-------|--------------|
| **open-core** | The core is open; enterprise features are paid, often under a separate license in the same repository | An `ee/` directory under a commercial license |
| **open client, closed control plane** | Endpoints are open source; the coordination service is the vendor's hosted, closed product | Tailscale: open clients, a closed coordination server, and Headscale as a community rebuild of that server |
| **fully self-hostable + paid cloud** | Every component is open and deployable; the vendor sells hosting, support or scale | NetBird: self-hostable management, signal and relay, alongside a paid cloud |
| **SaaS-only** | No deployable component; the product is the service | — |
| **dual license** | The same code under a copyleft license or a commercial license, the buyer's choice | AGPL-3.0 or commercial |
| **source-available relicense** | Formerly open, now source-available, usually to restrict competing hosted offerings | BSL, SSPL or Elastic License adopted after an OSI-licensed history |

The illustrations are patterns, not facts to copy into a record: licenses and components
change, so a record cites its own sources at its own refs.

## Self-Hostability

One line per product, from the per-component split:

| Grade | Meaning |
|-------|---------|
| **full** | Every component needed for the product to work can be deployed by the customer, from published artifacts, without a vendor account |
| **partial** | Some components self-host; at least one required component is hosted-only or paid-only. Name it. |
| **enterprise-only** | Self-hosting exists only under a paid contract |
| **none** | SaaS-only |
| **unknown** | The docs do not settle it. Name the component in doubt. |

"Contact sales for on-prem" is `unknown` until a document or artifact settles it; it is
not `enterprise-only` evidence on its own.

## Forks and Rebuilds

Community projects that change the answer to "can I run this without the vendor" are
part of the product's record, not separate trivia:

- **Fork** — continues the vendor's code, usually from the last ref before a relicense
  (OpenTofu from Terraform; OpenBao from Vault).
- **Rebuild** — an independent implementation of a closed component, compatible with the
  open ones (Headscale for Tailscale's coordination server).

Record for each: name, repository, license at a pinned ref, governance (foundation,
company, individuals), the component it replaces, and a compatibility note sourced to its
own docs. Whether a fork or rebuild gets its own product record is a scope question for
the profile. The link from the original's record is recorded either way.

## Pricing

Pricing is the most volatile fact in a record. Record:

- The plan names and the feature or component boundary between them, not the prices.
- Prices only if the profile asks for them, and always with the currency, billing unit
  and date checked.
- A "free" tier's limits (users, devices, nodes), since they often define who can use the
  open part in practice.
