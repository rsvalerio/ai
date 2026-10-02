---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
tags: [trigger]
---

This is from my Lovable app (Supabase backend). Review it and tell me what is wrong.

```sql
-- supabase/migrations/20260901_notes.sql
create table public.notes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users not null,
  body text
);
alter table public.notes enable row level security;
create policy "notes are editable" on public.notes for update to authenticated using (true);
```

```tsx
export function useNotes() {
  return useQuery({
    queryKey: ["notes"],
    queryFn: async () => {
      const { data } = await supabase.from("notes").select("*");
      return data;
    },
  });
}
```
