---
name: pkc-capture-assumption
description: Capture an Assumption (weaker than a Decision) linked to Features. Promote to DecisionRecord when validated. Use for working hypotheses and unproven beliefs.
---

# Capture Assumption

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_capture.py" assumption \
  --title "Users accept 15m token refresh" \
  --statement "Short access TTL will not hurt UX" \
  --rationale "Industry peers use similar TTL" \
  --for user-authentication
```

Edges: `assumes` → Feature. When proven, `/pkc-promote` or `/pkc-capture-decision` + `validates`.
