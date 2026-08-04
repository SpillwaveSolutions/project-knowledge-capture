---
name: pkc-federate
description: Multi-repo federated knowledge roots — list remotes, search across them, write shadow federation index. Remotes are read-only; link with maps_to.
---

# Federation

Configure in `.pkc/config.yml`:

```yaml
pkc:
  federation:
    - name: platform
      path: ../platform/knowledge
      readonly: true
```

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_federate.py" list --repo .
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_federate.py" search JWT --repo .
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_federate.py" index --repo . --write
```
