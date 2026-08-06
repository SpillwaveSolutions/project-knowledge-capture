# Assert zero-write re-materialize in CI

`01KZ75R2TEF13SKZYZ3DSBS5BZ` · story/feature · **open**

CI already asserts a second materialize run reports '0 created'.

## Hierarchy

- epic: [[Ticket-01KZ75NQ2VDVFD3R9F0SV38YEN]] Incremental materialize — Re-materializing a large worklog rewrites every concept file even when nothing changed, which churns git diffs and makes the operation O(all work) instead of O(changed work).

## Release

- [[Release-v0.5.0]]

## Related tickets

- [github #11](https://github.com/SpillwaveSolutions/project-knowledge-capture/issues/11)
