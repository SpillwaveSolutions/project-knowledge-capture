---
name: pkc-init
description: Scaffold a Project Knowledge Capture OKF bundle with all PKC catalogs (meetings, experiments, discoveries, decisions, features, …), root index.md, and log.md. Use when starting knowledge capture in a repo or creating knowledge/ / .okf for PKC.
---

# PKC Init

Create a knowledge root ready for capture and materialization.

## Process

1. Confirm target directory (default `knowledge/`; accept `.okf/` or existing OKF bundle).
2. Scaffold:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_common.py" init-bundle \
     --repo . \
     --bundle knowledge \
     --title "Project Knowledge"
   ```
3. Optionally write `.pkc/config.yml`:
   ```yaml
   pkc:
     enabled: true
     knowledge_root: knowledge
     okf_bundle: true
     materialize:
       from_worklog: true
       from_docs: true
       include: [features, decisions, designs, releases, tickets, specs]
     capture:
       auto_create_ticketlinks: true
     bridge:
       wikiticket: true
       worklog_bin: bin/worklog
   ```
4. If the repo has WikiTicket data, offer **pkc-materialize**.
5. Point the user at sample chain in this plugin’s `sample-knowledge/` for demos.
6. Run **pkc-setup --check**. If ripgrep is missing, offer `/pkc-setup` (consent-gated). Do not install packages during init unless the user asks.

## Directory layout

```
knowledge/
├── index.md
├── log.md
├── meetings/
├── experiments/
├── discoveries/
├── decisions/
├── features/
├── requirements/
├── specs/
├── designs/
├── releases/
├── code/
├── packages/
└── tickets/
```

## Done when

- Root `index.md` has `okf_version` and catalog links
- All catalog dirs have `index.md`
- `log.md` initialized
