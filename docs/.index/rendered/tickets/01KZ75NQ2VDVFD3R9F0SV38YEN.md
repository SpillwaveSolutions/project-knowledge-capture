# Incremental materialize

`01KZ75NQ2VDVFD3R9F0SV38YEN` · epic/feature · **done**

Re-materializing a large worklog rewrites every concept file even when nothing changed, which churns git diffs and makes the operation O(all work) instead of O(changed work).

## Children

- [[Ticket-01KZ75R2FPH92VY79KNR6MP59E]] Fingerprint worklog items on materialize — Compute a stable fingerprint per worklog item from the fields that actually affect the rendered concept: title, body, status, parent, wiki_key. (done)
- [[Ticket-01KZ75R2NDYVCGERRTKE9XCRM2]] Skip unchanged ULIDs without rewriting — When an item's fingerprint matches the one recorded in its concept, skip it before reading or rendering the file. (done)
- [[Ticket-01KZ75R2TEF13SKZYZ3DSBS5BZ]] Assert zero-write re-materialize in CI — CI already asserts a second materialize run reports '0 created'. (done)

Progress: 3/3 done

## Related tickets

- [github #3](https://github.com/SpillwaveSolutions/project-knowledge-capture/issues/3)
