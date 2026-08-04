---
name: pkc-capture-thread
description: Capture Slack/Discord/chat thread paste as Meeting or Discovery. Scrubs secrets/PII. Use when user pastes a conversation.
---

# Capture Thread

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_thread.py" --file paste.txt --as meeting --title "Auth discussion" --capture --repo .
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_thread.py" --file paste.txt --as discovery --title "Customer feedback" --capture
```
