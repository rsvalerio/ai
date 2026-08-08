# Classification and Severity Notes

## Justified Violations

Code with a documented, specific justification should be assigned **one severity level down** from baseline — and is often not a finding at all. The justification must be specific and accurate; a generic "for performance" without data is not valid. Examples that qualify:

- A type assertion or `as unknown as T` with an adjacent comment documenting a missing upstream brand/nominal marker (e.g. `as unknown as readonly RemoteExcalidrawElement[]` because the library omits the brand). Compile-time-only, no runtime risk → not a TS-2 finding.
- A `dangerouslySetInnerHTML` whose input is sanitized by DOMPurify (or equivalent) immediately before → not a SEC-1 finding (verify the sanitizer actually runs on this path).
- A deliberate `void asyncFn()` for genuine fire-and-forget (best-effort telemetry, an intentionally non-awaited broadcast) → not an ASYNC-1/ASYNC-7 finding.
- An `// eslint-disable-next-line react-hooks/exhaustive-deps` with a comment proving the dependency is intentionally frozen → downgrade or skip (REACT-4); a bare disable with no rationale stays a finding.
- A `key={index}` on a provably static, append-only list → downgrade (REACT-12).

## Tooling Overlap (do not double-report)

Before filing REACT/TS/ASYNC findings, check whether the project's configured tooling already catches and fails on them:

1. **Caught and failing in `eslint .` or `tsc -b --noEmit`?** → not a finding for this skill; the gate already enforces it. Note it only if the gate is mis-configured.
2. **The rule exists in ESLint/typescript-eslint but the project hasn't enabled it?** → the finding's real value is "enable this rule"; file it as a config recommendation (e.g. "enable `@typescript-eslint/no-floating-promises`") rather than per-occurrence noise.
3. **Not mechanically detectable (design smell, severity nuance, missing test coverage, security reasoning)?** → this is the skill's core value; file it.

## Security vs. Real-Time Classification

When a real-time (socket.io/WebSocket) issue is flagged:

1. **Secret/crypto/XSS in the payload handling?** (key in logs, IV reuse, unsanitized HTML from a message) → file under the SEC rule.
2. **Validation, authorization, or resource-limit concern on the channel?** → file under the RT rule, note the OWASP category.
3. **Both?** File under SEC; note the RT concern in the body.

## Severity Calibration Reminders

- Security findings reachable from untrusted input (network, WebSocket, URL, user input) are Critical/High; the same pattern on fully-trusted, local-only data is lower.
- Correctness bugs that cause silent data loss or wrong-data-to-the-user are High/Critical even if subtle (stale closures, fetch races, IV reuse).
- Style/readability issues are Low unless they obscure a correctness or security concern.
- Missing tests are scored by what's untested: crypto/auth/parsing of untrusted input = High; presentational component = Low.
