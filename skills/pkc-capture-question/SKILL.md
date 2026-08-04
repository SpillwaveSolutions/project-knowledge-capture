---
name: pkc-capture-question
description: Capture an open Question that may block a Feature until answered. Use for unresolved design questions and research gaps.
---

# Capture Question

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_capture.py" question \
  --title "Need distributed revoke list?" \
  --question "Do we need a JWT denylist in v1?" \
  --context "Compliance unknown" \
  --blocks user-authentication
```

Edges: `blocks` → Feature. Resolve with Decision/Discovery + `answers`.
