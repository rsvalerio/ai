# Duplication Rules

## Code Duplication (typical severity: Medium--High)

### Detection

> Thresholds below are sensible defaults; adjust per project if justified (e.g., generated code may raise the line threshold).

- **DUP-1.** Flag identical code blocks of 5+ lines (direct copy-paste, same match branches); threshold is configurable — lower for critical code, higher for generated or boilerplate-heavy modules
- **DUP-2.** Flag 3+ functions with similar structure differing only in types, literals, or field names; threshold is configurable per project
- **DUP-3.** Flag 3+ occurrences of repeated patterns: error mapping, `From`/`Into`/`TryFrom` impls, similar trait implementations across different types, struct initialization, builder setup, conversion functions
- **DUP-4.** Flag identical or near-identical match arms within the same function

### Refactoring

- **DUP-5.** Extract shared logic into helper functions or methods
- **DUP-6.** Use generics or trait-based dispatch to unify type-varying duplicates
- **DUP-7.** Use `Default` + struct update syntax (`..Default::default()`) to reduce initialization duplication
- **DUP-8.** Use `From`/`Into` blanket impls or macros to reduce boilerplate conversions

### Red Flag Examples

```rust
// Similar fns differing only in type/literal
fn process_user_event(...) { }
fn process_admin_event(...) { }  // Nearly identical

// Repeated error mapping (use anyhow::Context instead)
let x = op1().map_err(|e| Error::Custom(e.to_string()))?;
let y = op2().map_err(|e| Error::Custom(e.to_string()))?;

// Similar struct init (extract defaults/builder)
let c1 = Config { a: default(), b: default(), c: val1 };
let c2 = Config { a: default(), b: default(), c: val2 };
```

### Judgment

- **DUP-9.** Context matters: some duplication is better than the wrong abstraction; don't DRY prematurely
- **DUP-10.** Test code has a higher duplication tolerance than production code; prefer clarity over DRY in tests. Test duplication judgment is owned by TEST-12; DUP rules still apply to production code duplication found within test helper modules
