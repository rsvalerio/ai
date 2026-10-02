# UI rules

shadcn/ui (Radix primitives) and Tailwind CSS with the design tokens Lovable defines in
`src/index.css` and `tailwind.config.ts`. Grounded in the shadcn/ui docs, the Radix Primitives
docs and the Tailwind CSS docs.

## Design tokens & Tailwind (typical severity: Low--Medium)

**Detection heuristics** — search for: raw palette classes in feature components
(`bg-(blue|gray|slate|red|green)-\d+`, `text-white`, `text-black`); arbitrary colours
(`bg-[#`, `text-[#`); template-literal classes (`` `bg-${`` / `` `text-${``); `className={a + ' ' + b}`
on a component that accepts `className`.

- **UI-1.** Feature components use the semantic tokens (`bg-background`, `text-foreground`,
  `bg-primary`, `text-muted-foreground`, `border-border`, and so on). Raw palette colours and
  hex values bypass the theme and break dark mode. A new colour becomes a token (an HSL variable
  in `index.css` mapped in `tailwind.config.ts`) and is then used by name.
  **Scanning guidance:** raw colours inside `src/components/ui/` variants and one-off
  illustrations are acceptable. File a single finding per component that repeats the pattern,
  not one per class.
- **UI-2.** Never build class names dynamically (`` `bg-${color}-500` ``). Tailwind's compiler only
  sees complete class strings in source, so the class is never generated. Map values to full
  class strings with a lookup object or a `cva` variant.
  — v3.tailwindcss.com/docs/content-configuration#dynamic-class-names (the scaffold's v3),
  tailwindcss.com/docs/detecting-classes-in-source-files#dynamic-class-names (v4)
- **UI-3.** Components that accept `className` merge it with `cn()` (clsx + tailwind-merge) so
  that caller overrides win. Plain concatenation leaves conflicting utilities whose winner depends
  on stylesheet order.

## shadcn / Radix composition (typical severity: Medium)

- **UI-4.** `src/components/ui/` is vendored shadcn source. Change behaviour there through
  `cva` variants that stay generic, and keep app logic, data fetching and copy out of it. Do not
  fork copies (`button-2.tsx`, `CustomDialog.tsx` reimplementing Dialog) beside it.
- **UI-5.** `Dialog`, `Sheet`, `AlertDialog` and `Drawer` content include a `…Title` (visually
  hidden if the design has none) so that the dialog has an accessible name. Without one, screen
  readers announce an unnamed dialog. A `…Description` is optional, but how to omit it depends
  on the `@radix-ui/react-dialog` version. Before 1.1.20, the content always points
  `aria-describedby` at a description ID, so omitting the description needs
  `aria-describedby={undefined}` or the reference is broken. Up to 1.1.16 Radix also logs a
  console warning for it, while 1.1.17 to 1.1.19 are silent but still broken. From 1.1.20 there
  are no warnings and no broken references. File the missing Title on any version. File the
  missing description opt-out only below 1.1.20.
  — radix-ui.com/primitives/docs/components/dialog#accessibility
- **UI-6.** Use `asChild` to render a primitive as another element (`<Button asChild><Link …/></Button>`)
  instead of nesting interactive elements (`<Link><Button/></Link>`, a `<button>` inside a
  `DropdownMenuItem` that is already a button). An `asChild` slot takes exactly one child element.
- **UI-7.** One toast system. The scaffold mounts both the shadcn `<Toaster />` and sonner's
  `<Sonner />`. Pick one, remove the other provider and its hook, and route every call through
  the survivor. Mixed usage gives two stacks, two styles and duplicate announcements.
  *(Typical severity: Low. File once, at `App.tsx`.)*
