---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
tags: [trigger]
---

Review this Rust function and tell me what is wrong with it.

```rust
pub async fn fetch_user(pool: &Pool, raw_id: &String) -> User {
    let row = sqlx::query(&format!("SELECT * FROM users WHERE id = {}", raw_id))
        .fetch_one(pool)
        .await
        .unwrap();
    User::from(row)
}
```
