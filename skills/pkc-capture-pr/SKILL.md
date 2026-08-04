---
name: pkc-capture-pr
description: Capture a GitHub PR as an OKF CodeChange concept via gh pr view (or JSON fixture). Use when documenting significant merges.
---

# Capture PR → CodeChange

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_pr_capture.py" 12 \
  --repo . --implements user-authentication

# Offline / CI fixture
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_pr_capture.py" \
  --json-file tests/fixtures/pr.json --implements user-authentication
```

Sets `implements` edges to Features/Designs. Scrubs PR body secrets.
