---
name: grok-bot-project-knowledge-capture
description: Bind a Grok Bot agent to Project Knowledge Capture. Isolation, identity, deterministic capture.
---

# Grok Bot / Project Knowledge Capture

Read `docs/ONBOARDING.md` first, then follow `docs/GROK_BOT.md`.

1. Identity: `grok-bot/project-knowledge-capture`
2. Open an isolation session before writes (`scripts/brain_session.py open`) unless the human already pointed `SECOND_BRAIN_ROOT` at a session worktree.
3. Pack 2 hops, then write owned types only via `scripts/pkc_*.py`.
4. Close the session to PR. Report path + validation result.
5. Never document a private remote. Never write raw Markdown into the tree.
