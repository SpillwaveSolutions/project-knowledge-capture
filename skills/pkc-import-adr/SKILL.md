---
name: pkc-import-adr
description: Import MADR or adr-tools Architecture Decision Record directories into OKF DecisionRecords.
---

# Import ADRs

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_adr_import.py" --from docs/adr --repo . --dry-run
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_adr_import.py" --from docs/adr --repo .
```
