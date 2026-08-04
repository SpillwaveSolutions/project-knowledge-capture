---
name: pkc-release-notes
description: Generate release notes from Release concepts and Feature/CodeChange edges (released_in, lands_in, implements).
---

# PKC Release Notes

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_release_notes.py" --repo .
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_release_notes.py" releases/v0-1-0.md --repo .
```
