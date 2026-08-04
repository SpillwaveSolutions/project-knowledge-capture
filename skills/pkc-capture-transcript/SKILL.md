---
name: pkc-capture-transcript
description: Ingest Fireflies, Otter, Granola, or plain speaker-labeled transcripts into a Meeting concept. Always scrubs secrets/PII. Use when user pastes or provides a transcript export.
---

# Capture Transcript

```bash
# Normalize only
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_transcript.py" --file transcript.json --json

# Write Meeting
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_transcript.py" --file transcript.json \
  --capture --repo . --title "Auth design" --date 2026-08-03
```

Supports: fireflies JSON, otter-ish JSON, granola-ish JSON, speaker lines, plain text.
Always runs secret/PII scrub before write. Then offer decision extraction + action items.
