# Jurisdiction

Whose law a product's vendor answers to. These are properties of the **company**, so they
live in the vendor record and never on a product record. Evidence requirements come from
[evidence-contract.md](evidence-contract.md); what the project does with the answer comes
from the profile's jurisdiction policy.

## Four Facts, Not One

| Fact | Source | Why it differs |
|------|--------|----------------|
| **Legal entity** | Registry, legal imprint, the contracting party in the terms | The trade name is not the company |
| **HQ country** | Registry address of the entity | Where the company sits |
| **Governing law** | Terms of service / customer agreement, dated | What law the contract is under; often not the HQ's |
| **Parent** | Registry, acquisition announcement, annual filing | A subsidiary inherits its parent's exposure |

Record all four with sources. A company whose customer agreement differs by region
(one entity for EU customers, another elsewhere) is recorded per region.

**Data location is not jurisdiction.** "EU data residency" says where bytes are stored,
not which government can compel the company that holds them. Record it separately, as a
product-level fact where it is a product setting.

## Classes

Each entity, and its parent, falls into one class for EU data-protection purposes:

| Class | Meaning |
|-------|---------|
| **EU** | Established in an EU member state. Name the country. |
| **EEA** | Established in Iceland, Liechtenstein or Norway: EEA, not EU. |
| **adequacy** | Outside the EEA, in a country with a current European Commission adequacy decision. Name the country and check the Commission's list on the day. Adequacy decisions are granted, reviewed and struck down, so the list is never hardcoded. |
| **third country** | Outside the EEA, no adequacy decision. |

The class describes the entity. A vendor in the EU with a parent in a third country is
recorded as both, and the parent's class is the one that bounds what the entity can
promise.

**Never write "EU-based" or "European" without the country**, and never for Switzerland,
the UK or Canada, which are not in the EU or EEA (whatever their adequacy status).

## Extraterritorial Reach

Record laws that can compel the entity regardless of where data is stored, when they
apply to it or its parent. The common one: the **US CLOUD Act** (2018), which lets US
authorities compel providers under US jurisdiction to disclose data in their possession,
custody or control, wherever it is stored. It reaches US companies and, through control,
can reach their subsidiaries.

State reach as the fact it is: which law, which entity it applies to, and why (HQ,
parent, US presence). Do not grade it as a risk. The profile's jurisdiction policy decides
what it means for the project.

## Changes

Acquisitions change jurisdiction without changing the product. Record:

- The date of any change of control, and the classes before and after.
- Product records affected, so they can be re-checked. The product records themselves do
  not change; the vendor record does.
