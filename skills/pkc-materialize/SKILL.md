---
name: pkc-materialize
description: Materialize WikiTicket worklog fold and docs/ artifacts into OKF concepts (Features, TicketLinks, Designs, DecisionRecords, Releases, Specs). Use when syncing work items into the knowledge graph or after major planning/docs updates.
---

# PKC Materialize (WikiTicket → OKF)

Batch-emit OKF concepts from WikiTicket without making PKC the system of record for status.

## When to use

- Project uses WikiTicket SDD (`.work/todo.jsonl`, `bin/worklog`)
- User asks to “sync tickets into knowledge”, “materialize the worklog”, “import ADRs/designs”

## Mapping (normative)

| WikiTicket source | OKF type(s) |
|-------------------|-------------|
| Work item epic/story | `Feature` + `TicketLink` |
| Work item task/subtask | `TicketLink` (+ parent Feature link when possible) |
| Plan (`docs/plans/*.md`) | `Specification` |
| Design / walkthrough | `Design` |
| ADR | `DecisionRecord` |
| Release notes | `Release` |
| Significant PR page | `CodeChange` |

## Process

1. Confirm knowledge root and ensure bundle:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_common.py" init-bundle --repo . --bundle knowledge
   ```

2. Obtain worklog fold (repo-local CLI — not part of this plugin):
   ```bash
   bin/worklog fold > /tmp/fold.json
   # or pipe:
   bin/worklog fold | python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_materialize.py" \
     --repo . --bundle knowledge --from-docs
   ```

3. Or from a saved fold / fixture:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_materialize.py" \
     --repo . \
     --fold /tmp/fold.json \
     --include features,decisions,designs,releases,tickets,specs \
     --from-docs
   ```

4. **Respect truth_state**
   - Do not overwrite `snapshot` / `superseded` / `archived` with current data unless `--force` or user requests.

5. **Idempotency**
   - Re-run updates in place; report `created` / `updated` / `skipped`.

6. Preserve `wiki_key`, `worklog_id`, `external_id`, `external_system` when present.

7. Present the materialize report to the user. Offer okf validation if available.

## Config (optional)

`.pkc/config.yml` or under `pkc:` in `.work/config.yml`:

```yaml
pkc:
  enabled: true
  knowledge_root: knowledge
  materialize:
    from_worklog: true
    from_docs: true
    include: [features, decisions, designs, releases, tickets, specs]
```

## Rules

- Never hand-edit `.work/todo.jsonl` — use `bin/worklog` only.
- PKC does not publish to wiki (WikiTicket wiki-publish remains the publishing plane).
- Generated concepts set `generated: true`.

## Done when

- Report lists created/updated/skipped counts
- TicketLinks exist for open work items
- Features exist for epic/story items
- Catalogs refreshed
