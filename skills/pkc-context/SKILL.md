---
name: pkc-context
description: Build a progressive-disclosure context pack for a Feature (or any concept). Supports --tiny (1 hop / 8 nodes) for chat focus and mermaid graphs. Auto-run when starting work on a Feature.
---

# PKC Context Pack

**Auto-inject rule:** When the user opens or starts work on a Feature path, run a pack first (tiny in chat; full 2-hop for deep work). Lead with DecisionRecords + originating Meetings/Experiments.

```bash
# Standard (2 hops, ~20 nodes)
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_pack.py" features/<slug>.md --repo . --hops 2

# Tiny / ADHD / chat (1 hop, 8 nodes)
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_pack.py" features/<slug>.md --tiny

# Mermaid only
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_pack.py" features/<slug>.md --mermaid
```

Prefer okf-plugin pack when installed. Never invent edges.

**Token budget.** Default is 1/4 of `SECOND_BRAIN_WINDOW_TOKENS` (128000 → 32000).
Override with `--max-tokens` or `SECOND_BRAIN_PACK_MAX_TOKENS`. Over budget exits
1 and writes nothing. `--max-nodes` / `--tiny` clip the walk; they are not a
token budget. Bodies stay off unless that node is the pack root.

