# FORM rules

react-hook-form + zod + the shadcn `<Form>` wrapper. Grounded in the react-hook-form docs, the
zod docs and the shadcn/ui Form component docs.

## Validation (typical severity: Medium--High)

**Detection heuristics** — search for: `useForm(` without `resolver:`; `useState` per field
with a manual `onSubmit` validator; `<form onSubmit` with no pending guard; `z.number()` on an
`<Input type="number">`; `.insert(` / `.update(` fed straight from `form.getValues()`.

- **FORM-1.** Forms validate with a zod schema through `zodResolver`, and the form's TypeScript
  type is `z.infer<typeof schema>`. Hand-rolled per-field `useState` plus ad-hoc checks drift from
  the payload the database receives. — react-hook-form.com/docs/useform#resolver
- **FORM-2.** Every rule the schema enforces that protects data (length, range, required, format,
  enum) is also enforced server-side, in a DB constraint (RLS-9) or in the Edge Function's
  validation (EDGE-4). The anon key can call the API without the form.
- **FORM-3.** Coerce inputs to the schema's types: `z.coerce.number()` or `valueAsNumber` for
  numeric inputs, and `z.coerce.date()` or explicit parsing for dates. Empty optional fields map to
  `null`, not `""`. Otherwise strings land in numeric columns, and `""` violates or bypasses
  constraints.

## Submit lifecycle (typical severity: Medium)

- **FORM-4.** Submission disables the submit control while pending (`formState.isSubmitting` or
  the mutation's `isPending`), surfaces server errors to the user (`setError('root', …)` or a
  toast that includes the failure), and resets or navigates only on success. A double-click must
  not double-insert.
- **FORM-5.** Fields use the shadcn `FormField` / `FormItem` / `FormLabel` / `FormControl` /
  `FormMessage` composition (or equivalent wiring), so labels and error messages are linked with
  `htmlFor` / `aria-describedby` / `aria-invalid`. A bare `<Input {...register('x')}>` with a
  sibling `<p>` error has neither. — ui.shadcn.com/docs/components/form
