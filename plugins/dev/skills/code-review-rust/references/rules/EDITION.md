# EDITION rules

## Rust 2024 Edition Reference

> These are **not finding-generating rules** — they document edition behavior changes for context. The compiler and `cargo fix --edition` enforce edition migration. Reviewers should understand these changes but should not flag them as findings.

- **EDITION-1.** Reserved keyword: `gen` (for future generators); use raw identifier `r#gen` if needed
- **EDITION-2.** In **return position** (`-> impl Trait`), Rust 2024 captures all in-scope lifetimes and type parameters by default; use `+ use<'a, T>` to state the captures explicitly and narrow them. This is a return-position rule only — argument-position `impl Trait` (`fn f(x: impl Trait)`) is an anonymous generic parameter and is unaffected by the capture change.
- **EDITION-3.** Match ergonomics restrictions: in Rust 2024, you cannot mix implicit match ergonomics (compiler-inserted `ref`/`ref mut`) with explicit `mut` or `ref` on the same binding — it's a hard error. Fix: either let the compiler handle binding modes entirely, or write fully explicit patterns. Patterns that already specify all binding modes are unaffected
- **EDITION-4.** Shortened temporary lifetimes: `if let` temporaries drop at branch end, not statement end
- **EDITION-5.** Apply edition migration fixes before updating `edition = "2024"` in Cargo.toml

> Choosing the edition for a **newly added** crate is a project-setup decision rather than an edition-behavior note, and it *is* finding-generating — it lives in ARCH-17.
