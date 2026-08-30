---
name: pkc-index
description: Refresh, inspect, or drop the disposable SQLite/FTS5 knowledge index. Use when search/pack/validate is slow, after a large git checkout, or when the user asks about the PKC index.
---

# PKC index

Git + Markdown is the source of truth. `knowledge/.pkc/index.sqlite` is a
disposable accelerator. Deleting it is always valid recovery.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_index.py" status --repo .
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_index.py" refresh --repo .
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_index.py" refresh --force --repo .
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_index.py" drop --repo .
```

Search, pack, and validate refresh the index themselves on each call
(mtime+size, not the curate hook). You do not need to run `refresh` first.

Ladder: index → ripgrep → full scan. `--no-index` on search/pack/validate
skips this rung. `PKC_NO_INDEX=1` disables it for the process.

Never commit `*.sqlite`. Never install packages. Missing FTS5 is not a
failure — the lower rungs still run.
