---
name: pkc-context
description: Build a progressive-disclosure context pack for a Feature or concept (Meetings, Experiments, Decisions that shaped it).
---

Build a context pack using the **pkc-context** skill.

User request: `$ARGUMENTS`

Follow `${CLAUDE_PLUGIN_ROOT}/skills/pkc-context/SKILL.md`. Prefer okf-plugin pack when available; else:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_pack.py" <concept> --repo . --hops 2 --write <bundle>/packs/
```
