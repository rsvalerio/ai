# LOV rules

The Lovable scaffold and the residue of prompt-driven iteration. These rules are about the
**project**, not a line of code, so most of them are filed once, at a config or root file.

## Baseline & build (typical severity: Medium)

**Detection heuristics** — search for: `"strict": false`, `"strictNullChecks": false`,
`"noImplicitAny": false` in `tsconfig*.json`; `"@typescript-eslint/no-unused-vars": "off"`;
`componentTagger()` in `vite.config.ts`; `lovable-tagger` in `dependencies`; more than one of
`bun.lockb` / `bun.lock` / `package-lock.json` / `pnpm-lock.yaml`.

- **LOV-1.** The type and lint baseline is real. The scaffold disables `strict`,
  `strictNullChecks` and `noImplicitAny` and turns off `no-unused-vars`, so the class of bugs
  `code-review-web` assumes `tsc` catches goes unchecked. File **one** finding at
  `tsconfig.app.json` with a staged plan: `strictNullChecks` first (it finds the most real bugs),
  then `noImplicitAny`, then `strict`, then re-enable unused-variable linting. Each stage keeps
  `ops typecheck` green. Note the measured error count per stage if you can run `tsc`.
- **LOV-2.** `lovable-tagger`'s `componentTagger()` runs only in development (`mode ===
  'development' && componentTagger()`) and the package is a `devDependency`. Unconditional, it
  injects source-location attributes into the production DOM.
- **LOV-3.** One package manager, one lockfile, committed. Two lockfiles mean CI and the Lovable
  builder can resolve different trees. *(Typical severity: Low.)*

## Generated code (typical severity: Medium)

- **LOV-4.** Files Lovable regenerates (`src/integrations/supabase/client.ts`,
  `src/integrations/supabase/types.ts`) are not hand-edited. Edits are overwritten on the next
  sync. Extend in a sibling module, such as typed helpers in `src/lib/db.ts`. Use
  `git log -p` on these paths to confirm hand edits before filing.

## Iteration residue (typical severity: Medium--High)

- **LOV-5.** Remove dead and duplicate artefacts left by iteration: pages and components not
  reachable from the router or any import, near-copies (`Dashboard.tsx` / `DashboardNew.tsx` /
  `Dashboard2.tsx`), unused shadcn primitives in `src/components/ui/` together with their
  `@radix-ui/*` dependencies, and unused hooks such as `use-mobile`. Dead code still ships
  dependencies and misleads the next prompt. *(Typical severity: Low--Medium.)*
- **LOV-6.** No placeholder behaviour on a reachable path that looks real: a submit handler
  that only `console.log`s or `toast`s "Saved!", a `setTimeout` faking latency, a hardcoded
  `mockUsers` / `sampleData` array rendered as live data, `const isAuthenticated = true`, or a
  "Pay" button with no backend. A user believes the action happened. File it **High** when data
  the user entered is silently discarded.
- **LOV-7.** Ship project metadata, not scaffold defaults: the `index.html` `<title>`,
  `description`, `og:*` / `twitter:*` tags and favicon describe this app. Scaffold leftovers name
  the builder in every link preview. *(Typical severity: Low.)*
