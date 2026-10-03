# OWASP Top 10:2025 Mapping

> **Version note**: This maps to the OWASP Top 10 **2025** edition, final since 2025-12-24 (the release-candidate label was dropped in the OWASP/Top10 repository that day). Source: [top10.owasp.org/2025](https://top10.owasp.org/2025/) (where [owasp.org/Top10](https://owasp.org/Top10/) redirects), checked 2026-10-03. Changes from 2021 that move SEC rules: SSRF is folded into **A01**; **A03** Software Supply Chain Failures supersedes 2021's Vulnerable and Outdated Components; **A10** Mishandling of Exceptional Conditions is new; and Injection, Crypto, Misconfiguration and Insecure Design all changed number. Placements below follow the CWE lists on each category page, so a 2021 id is never a valid citation — re-derive it from the CWE.

- **A01** Broken Access Control → missing authz, IDOR, tenant isolation, path traversal, symlink following, insecure temp files and permissions, version and system-info exposure, SSRF (SEC-14, SEC-17--20, SEC-22, SEC-25, SEC-43)
- **A02** Security Misconfiguration → insecure defaults, active debug code, unvalidated config, permissive cross-origin policy (SEC-23, SEC-29, SEC-30)
- **A03** Software Supply Chain Failures → vulnerable, unmaintained or untrusted dependencies, lockfile drift (SEC-27, SEC-28)
- **A04** Cryptographic Failures → weak algorithms, non-CSPRNG randomness, nonce reuse, hardcoded keys, missing TLS, secret handling (SEC-5--7, SEC-8 for keys, SEC-9, SEC-10, SEC-29 for TLS)
- **A05** Injection → SQL, OS command, argument and regex injection; missing input validation at the boundary (SEC-11--13, SEC-16)
- **A06** Insecure Design → races on shared state, reentrancy, missing rate limits, security decisions on untrusted input (SEC-24, SEC-25, SEC-38, SEC-33 for rate limits)
- **A07** Authentication Failures → hardcoded or default credentials, missing auth, improper certificate validation (SEC-8 for passwords and tokens, SEC-29)
- **A08** Software or Data Integrity Failures → deserializing untrusted data, missing signature or integrity checks, untrusted search paths (SEC-11 when the input is deserialized, SEC-37, SEC-44)
- **A09** Security Logging and Alerting Failures → secrets in logs, missing security-event logging (SEC-5, SEC-21)
- **A10** Mishandling of Exceptional Conditions → failing open, missing cleanup on error paths, sensitive data in error messages, panics on untrusted input (SEC-21, SEC-31, SEC-32)

**No Top 10:2025 home** — cite the CWE instead of forcing a category:

- Memory safety and FFI (SEC-1--4, SEC-34--36, SEC-39--42): CWE-119, -416, -787, -824. The 2025 list maps no memory-corruption CWE.
- Resource exhaustion and DoS (SEC-15 overflow, SEC-16 regex cost, SEC-26 deadlock, SEC-33 size limits): CWE-190, -400, -770, -833, -1333. The editors deliberately classify by root cause and leave symptom categories such as "Denial of Service" out. When a limit is missing by design, A06 is the closest category.

Map each finding to the most relevant 2025 category, by its CWE, when writing SEC-prefixed findings.
