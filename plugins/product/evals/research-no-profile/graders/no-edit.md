---
type: tool_used
name: no-edit
tool: Edit
min: 0
max: 0
---

With no profile the skill writes nothing — not a record, and not the profile itself
until the user has approved it. `Edit` is a gated tool: without `--allow-tools` it is withheld from both arms and this
count passes vacuously. `make eval` grants it.
