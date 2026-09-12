---
name: pkc-retrieve
description: Spawn the knowledge-retriever sub-agent to search and pack project memory without contaminating parent context. Use before answering from the OKF tree, or when starting work that needs Feature/Decision context.
---

# PKC Retrieve

Parent-facing. The parent must **not** run `pkc_search` / `pkc_pack` itself for retrieval. Spawn the `knowledge-retriever` sub-agent (Claude Code Task/Agent tool, or host equivalent) and consume only the Retrieval card.

## Do not pull raw packs into the parent

- Do **not** run `pkc_search.py` or `pkc_pack.py` in the parent turn for retrieval.
- Do **not** paste search hit lists, mermaid graphs, or ranked pack bodies into the parent working context.
- Progressive disclosure (`--tiny`, hop caps) clips the graph; it does **not** isolate the parent. Isolation is the child agent.

## Spawn

Pass the child:

| Input | Required | Notes |
|-------|----------|-------|
| query | one of query / seed | Free-text question or keywords |
| seed path | one of query / seed | Absolute in-bundle path, e.g. `/features/user-authentication.md` |
| type filters | no | e.g. `DecisionRecord,Feature` |
| bundle / repo | no | Default `--repo .` |
| deepen allowed | no | Default yes; cap is the child's 2 deepen steps |

The child walks, scores, and returns **only**:

```markdown
## Retrieval card
- Query: …
- Seed: `/path` (`Type`) — why chosen
- Fit: high|medium|low — one sentence
- Engine: index|rg|scan
- Pack: hops=N nodes=N tokens=N/budget
- Lead nodes: (5–8 bullets: title · type · path · one-line why)
- Open gaps: (Questions / missing edges / thin pack) or none
- Next: stay|deepen-2hop|try-alt-seed `/other`
```

Answer from that card. If the card says `deepen-2hop` or `try-alt-seed` and the user still needs more, spawn again with that instruction — still do not pull raw packs into the parent.

## Orthogonal fan-out

If the question also needs **architecture topology** (runtime units, deploy nodes, SAC Package as a build artifact), tell the parent to also spawn SAC `architecture-retriever`. Do not implement SAC here. PKC `Package` is project-memory (what shipped).

## Done when

- The parent has a Retrieval card (or a second card after one re-spawn).
- No search hit list or full pack markdown is in the parent context.
- The parent has not written knowledge nodes as a side effect of retrieval.
