# TS rules

Rules are grounded in the official React docs (react.dev), the React 19 / 19.2 release posts, the React Compiler v1.0 docs (stable Oct 2025), `eslint-plugin-react-hooks` v7, the TypeScript handbook, `typescript-eslint`, and MDN. Where a rule is fully enforced by configured tooling, file only for the unenforced nuance (see [rules.md](../rules.md)).

## TypeScript — Type Safety (typical severity: Medium--High)

- **TS-1.** Avoid `any`; use `unknown` for values of unknown shape and narrow before use. Every `any` is a hole that disables checking transitively. *(Enforced by `@typescript-eslint/no-explicit-any` when configured.)*
  **Scanning guidance:** exclude `.d.ts` shims, generated types, and test mocks. A single documented `any` at a typed third-party boundary with a narrowing guard immediately after is lower severity than `any` that flows through business logic. — typescript-eslint.io/rules/no-explicit-any
- **TS-2.** Avoid type assertions (`as T`) and especially the double-cast `as unknown as T`; they silence the checker and let invalid values masquerade as valid. Prefer narrowing, type guards, or `satisfies`.
  **Scanning guidance:** a cast with an adjacent comment documenting a missing upstream brand or nominal marker (e.g. `as unknown as readonly RemoteExcalidrawElement[]`) is a justified compile-time-only marker, not a finding (see [classification notes](../rules-classification.md)). `as const` is not a type assertion in this sense — never flag it. — typescript-eslint.io/rules/no-unnecessary-type-assertion
- **TS-3.** Avoid the non-null assertion `!`; it asserts non-null without proof and crashes at runtime if wrong. Narrow with a guard, optional chaining, or an early return instead. — typescript-eslint.io/rules/no-non-null-assertion
- **TS-4.** Prefer the `satisfies` operator to validate a value against a type while keeping its narrow inferred type, rather than a widening `: T` annotation that erases literal/narrow information. — typescriptlang.org/docs/handbook/release-notes/typescript-4-9.html
- **TS-5.** Model mutually-exclusive states as a **discriminated union** (`{ status: "loading" } | { status: "error"; error: E } | { status: "success"; data: D }`) instead of several independent boolean/optional flags — invalid combinations (loading *and* error) become unrepresentable. — typescriptlang.org/docs/handbook/2/narrowing.html#discriminated-unions

## TypeScript — Modeling & Strictness (typical severity: Low--Medium)

- **TS-6.** Mark data that should not mutate as `readonly` / `ReadonlyArray<T>` and lock literal config with `as const`; immutability documents intent and prevents accidental mutation (and feeds discriminated-union/literal derivation). — typescriptlang.org/docs/handbook/2/objects.html#readonly-properties
- **TS-7.** Use branded/nominal types (`type UserId = string & { readonly __brand: "UserId" }`) for IDs and validated values so structurally-identical-but-semantically-different values cannot be swapped (room IDs vs scene IDs, raw vs sanitized strings). — community pattern; see effectivetypescript.com
- **TS-8.** Prefer union string literals (or `as const` objects) over `enum` in new code; unions avoid `enum` runtime artifacts and `const enum` cross-module pitfalls. — typescriptlang.org/docs/handbook/enums.html
- **TS-9.** Use `import type` for type-only imports so bundlers/transpilers erase them, avoiding accidental runtime side-effects and easing circular-import issues. *(Enforced by `@typescript-eslint/consistent-type-imports`.)* — typescript-eslint.io/rules/consistent-type-imports
- **TS-10.** Constrain generics with `extends` rather than leaving them open, and return the narrowest accurate type from functions — broad returns push the checking burden onto every caller. — typescriptlang.org/docs/handbook/2/generics.html#generic-constraints
- **TS-11.** Add a `default` branch that assigns the value to `never` when switching over a discriminated union (`const _exhaustive: never = x;`) so adding a variant later becomes a compile error instead of a silent fall-through. — typescriptlang.org/docs/handbook/2/narrowing.html#exhaustiveness-checking
- **TS-12.** Enable strict typing in `tsconfig`: `"strict": true` at minimum, and prefer also enabling `noUncheckedIndexedAccess` (array/index access returns `T | undefined`) and `exactOptionalPropertyTypes` (distinguishes missing key from `undefined`) — both are *outside* the `strict` preset and catch real bugs. Flag a `tsconfig` missing `strict`. — typescriptlang.org/tsconfig#strict
