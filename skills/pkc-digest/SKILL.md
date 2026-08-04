---
name: pkc-digest
description: Weekly/daily knowledge digest — recent captures, decisions, open questions, unvalidated assumptions, needs-verification queue, doctor highlights.
---

# PKC Digest

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_digest.py" --repo . --days 7
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_digest.py" --days 7 --write knowledge/packs/digest-weekly.md
```

One-screen brief. Good Monday kickoff or end-of-week review.
