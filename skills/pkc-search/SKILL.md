---
name: pkc-search
description: Full-text search over the knowledge bundle (AND terms, type filters). Use when finding decisions, meetings, or features by keyword.
---

# PKC Search

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_search.py" "JWT refresh" --repo .
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_search.py" JWT --type DecisionRecord,Feature --json
```

AND semantics across terms. Scores title > description > tags > body.
After hits on a Feature, offer `/pkc-context --tiny`.
