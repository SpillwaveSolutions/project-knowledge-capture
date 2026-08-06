# Skip unchanged ULIDs without rewriting

`01KZ75R2NDYVCGERRTKE9XCRM2` · story/feature · **done**

When an item's fingerprint matches the one recorded in its concept, skip it before reading or rendering the file.

## Hierarchy

- epic: [[Ticket-01KZ75NQ2VDVFD3R9F0SV38YEN]] Incremental materialize — Re-materializing a large worklog rewrites every concept file even when nothing changed, which churns git diffs and makes the operation O(all work) instead of O(changed work).

## Release

- [[Release-v0.5.0]]

## Related tickets

- [github #10](https://github.com/SpillwaveSolutions/project-knowledge-capture/issues/10)
