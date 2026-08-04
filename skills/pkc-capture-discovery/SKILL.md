---
name: pkc-capture-discovery
description: Capture research, competitive scans, user findings, and discovery notes as OKF Discovery concepts with source, confidence, and informs links. Use for research dumps, market scans, and exploratory findings.
---

# PKC Capture Discovery

Make research durable and linkable without pretending it is a formal requirement yet.

## Process

1. Resolve knowledge root.
2. Extract: title, source (URL/doc/person), confidence (`low|medium|high`), findings, implications.
3. Write `discoveries/<slug>.md`:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pkc_capture.py" discovery \
     --repo . \
     --title "Auth competitor scan" \
     --source "https://example.com/blog" \
     --confidence medium \
     --notes "Most SaaS peers use short-lived JWT + refresh" \
     --links-to user-authentication
   ```
4. Links: Discovery → Feature/Requirement with `rel: informs`.
5. For atomic findings that need their own nodes, create child notes and use `rel: discovered_in` from finding → Discovery.
6. Offer **pkc-promote** when findings mature into Requirement/Feature/ADR.

## Frontmatter essentials

```yaml
type: Discovery
title: …
source: …
confidence: medium
status: active
verified: false
links:
  - target: /features/….md
    rel: informs
```

## Done when

- Discovery file written with source + confidence + findings
- Catalog + log updated
- Promotion path suggested if findings are decision-ready
