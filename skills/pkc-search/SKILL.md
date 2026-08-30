---
name: pkc-search
description: Full-text search over the knowledge bundle (AND terms, type filters). Use when finding decisions, meetings, or features by keyword.
---

# PKC Search

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_search.py" "JWT refresh" --repo .
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_search.py" JWT --type DecisionRecord,Feature --json
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_search.py" JWT --rg
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_search.py" JWT --no-rg
```

AND semantics across terms. Scores title > description > tags > body.

When `rg` is on PATH (or `PKC_RG_PATH`), search prefilters candidate files with ripgrep then ranks in Python — ranking is identical to a full scan. Missing rg is not an error; the linear walk still runs. See `/pkc-setup`.

After hits on a Feature, offer `/pkc-context --tiny`.
