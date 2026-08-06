# Fingerprint worklog items on materialize

`01KZ75R2FPH92VY79KNR6MP59E` · story/feature · **done**

Compute a stable fingerprint per worklog item from the fields that actually affect the rendered concept: title, body, status, parent, wiki_key.

## Hierarchy

- epic: [[Ticket-01KZ75NQ2VDVFD3R9F0SV38YEN]] Incremental materialize — Re-materializing a large worklog rewrites every concept file even when nothing changed, which churns git diffs and makes the operation O(all work) instead of O(changed work).

## Release

- [[Release-v0.5.0]]

## Related tickets

- [github #9](https://github.com/SpillwaveSolutions/project-knowledge-capture/issues/9)
