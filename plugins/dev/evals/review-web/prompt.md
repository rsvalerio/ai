---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
tags: [trigger]
---

Review this React component and tell me what is wrong with it.

```tsx
export function Profile({ id }: { id: string }) {
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    fetch(`/api/users/${id}`)
      .then((r) => r.json())
      .then(setUser);
  });

  return <div dangerouslySetInnerHTML={{ __html: user?.bio }} />;
}
```
