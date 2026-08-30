---
name: pkc-search
description: Full-text search over the knowledge bundle (AND terms, type filters). Use when finding decisions, meetings, or features by keyword.
---

# PKC Search

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_search.py" "JWT refresh" --repo .
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_search.py" JWT --type DecisionRecord,Feature --json
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_search.py" JWT --engine index
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_search.py" JWT --no-index --rg
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_search.py" JWT --engine scan
```

AND semantics across terms. Scores title > description > tags > body.

Ladder: SQLite index → ripgrep → full scan. Ranking stays in Python, so
`--engine scan` and the index path return the same scores. `--engine fts`
uses FTS5 MATCH (prefix tokens; not score-identical). Missing index or rg
is not an error. See `/pkc-index` and `/pkc-setup`.

After hits on a Feature, offer `/pkc-context --tiny`.
