---
type: tool_used
name: no-websearch
tool: WebSearch
min: 0
max: 0
---

Step 0 comes before any research: without a profile there is nothing to score against,
and the privacy wall has not been drawn. A run that reaches for the web before it asks
for a profile has skipped the stop gate, even if it asks later.

`WebSearch` and `WebFetch` are gated tools: without `--allow-tools` they are withheld
from both arms and this count passes vacuously. `make eval` grants them.
