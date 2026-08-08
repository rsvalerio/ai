# Classification and Severity Notes

## Justified Violations

Code with documented justifications (`// SAFETY:` comments, `#[allow(clippy::...)]` with rationale) should be assigned **one severity level down** from baseline. The justification must be specific and accurate — generic "needed for performance" without data is not valid.

## Unsafe Code Classification

When an `unsafe` block is flagged:

1. **Memory safety violation or exploitable condition?** (use-after-free, data race, bad transmute, unsound Send/Sync) → file under SEC prefix
2. **Idiomatic concern only?** (block too large, missing safety comment, no safe wrapper, edition-specific syntax) → file under EFF prefix
3. **Both?** File under SEC prefix; note idiomatic concerns in the Notes section

## SEC-21 Classification

1. **Sensitive data leaking through error messages, logs, or display output?** → SEC-21 (info disclosure)
2. **Fail-open behavior or missing cleanup on error paths?** → SEC-31/SEC-32 (security error handling)
3. **Idiomatic error handling patterns with no security impact?** → ERR rules

## FFI Boundary Classification

1. **Safety violation?** (null pointer deref, invalid pointer, use of `std::mem::uninitialized()`, incorrect ownership transfer) → SEC-34--36
2. **Idiomatic unsafe concern?** (block too large, missing safety comment, no safe wrapper) → UNSAFE-1--8
3. **Both?** File under SEC prefix; note idiomatic concerns in the Notes section
