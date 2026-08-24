---
doc_type: guide
slug: noun-ownership-migration
title: Noun-ownership migration (PKC)
truth_state: current
---

# Noun-ownership migration (PKC 0.8.0)

Family runbook: [okf-plugin noun-ownership migration](https://github.com/SpillwaveSolutions/okf-plugin/blob/main/docs/user_guide/noun-ownership-migration.md).

This page is the PKC-shaped half: existing `knowledge/` trees, TicketLink emission, and work types that used to live in okf-plugin.

## What you received

These `type:` values are **PKC nouns** as of 0.8.0. Keep the files. Install this plugin so `okf-graph.py validate --strict` merges the schemas.

`Meeting`, `Experiment`, `Discovery`, `Assumption`, `Question`, `Feature`, `Requirement`, `Specification`, `Design`, `Release`, `CodeChange`, `Package`, `Risk`, `Acceptance`, `DecisionRecord`, `TicketLink`, `Epic`, `Story`, `Task`, `Subtask`, `Bug`, `Branch`, `Project`, `Playbook`, `Runbook`, `Reference`.

`Catalog` and `ContextPack` stay in okf-plugin. Do not move those schemas here.

## Upgrade

1. Install **okf-graph-eng v0.8.0**, then **project-knowledge-capture v0.8.0**.
2. Point `SECOND_BRAIN_ROOT` at the existing bundle (do not copy it).
3. Replace TicketLink emission:

```bash
# old (okf-plugin ≤0.7.x) — now a stub, exit 2
bin/worklog fold | python3 path/to/okf-plugin/scripts/okf-ticket-link.py emit --bundle knowledge --open-only

# new
bin/worklog fold | python3 path/to/project-knowledge-capture/scripts/pkc_ticket_link.py emit --bundle knowledge --open-only
```

4. Validate:

```bash
python3 scripts/pkc_validate.py --bundle knowledge
python3 path/to/okf-plugin/scripts/okf-graph.py validate knowledge --strict
```

## Catalogs you own

`catalog_ownership` for this plugin includes `meetings`, `experiments`, `discoveries`, `decisions`, `assumptions`, `questions`, `features`, `requirements`, `specs`, `designs`, `releases`, `code`, `packages`, `tickets`, `epics`, `stories`, `tasks`, `subtasks`, `bugs`, `branches`, `projects`, `risks`, `acceptance`, `playbooks`, `runbooks`.

You may rewrite those indexes. Do not rewrite `packs/` (okf-plugin) or SAC/DEKC/AGER catalogs.

There is no `references/` ownership row yet for `Reference`. Putting Reference files under `knowledge/` or an existing owned catalog is fine for this cut.

## What not to do

- Do **not** retype `TicketLink` / `DecisionRecord` / work types. They already have the right names.
- Do **not** emit `Runbook` from SAC wiki ingest and then “claim” it as a SAC type. The file is PKC; SAC classify still returns `Runbook` in a mixed bundle.
- `Question` stays PKC. RKC `ResearchQuestion` is a different noun.
- `Package` here is project-memory (what shipped). SAC `Package` is a build unit. One tree, one meaning.
- `Risk` here is project-memory risk, not executive-coordination company risk.
- `Experiment` here is a spike, not a GTM experiment.

## Done when

- `pkc_ticket_link.py` is what CI / hooks / skills call.
- `validate --strict` no longer reports PKC types as unknown.
- `log.md` notes the 0.8.0 plugin pin.
