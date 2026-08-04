---
name: pkc-capture-experiment
description: Capture experiment or spike results into an OKF Experiment concept with hypothesis, method, results, conclusion, and typed informs links. Use for spikes, A/B tests, POC write-ups, and engineering experiments.
---

# PKC Capture Experiment

Record what was tried, what was learned, and what it informs.

## Process

1. Resolve knowledge root (`pkc_common.py resolve-root`).
2. Collect: title, hypothesis, method, results, conclusion, related code paths.
3. Write `experiments/<slug>.md` using template or:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_capture.py" experiment \
     --repo . \
     --title "JWT vs session-cookie spike" \
     --hypothesis "JWT will simplify horizontal scaling" \
     --result "Both workable; JWT slightly simpler ops" \
     --conclusion "Proceed with JWT" \
     --informs user-authentication
   ```
4. Typed edges:
   - Experiment → Feature/Design/Requirement: `rel: informs`
   - Decision that followed → Experiment: `rel: originates_from` (on the DecisionRecord)
5. Refresh `experiments/index.md` and `log.md`.
6. Offer to capture a follow-on DecisionRecord via **pkc-capture-decision**.

## Frontmatter essentials

```yaml
type: Experiment
title: …
hypothesis: …
result: …
conclusion: …
status: completed   # or running | abandoned
verified: true
links:
  - target: /features/….md
    rel: informs
```

## Done when

- Experiment concept written with hypothesis + conclusion
- At least one `informs` link when a target feature/design is known
- Catalog + log updated
