# Risk and Acceptance concepts

`01KZ75NQ7VFPF3YESB5P90DR29` · epic/feature · **done**

Two kinds of project knowledge have no home in the graph today: risks (things that might go wrong, and what mitigates them) and acceptance criteria (the atomic conditions that decide whether a Feature is actually done).

## Children

- [[Ticket-01KZ75R2ZJGMNBHD82WZXPCNX4]] Add Risk type with mitigates and exposes edges — Add a Risk concept type with mitigates and exposes edges, wired through TYPE_TO_DIR, CATALOGS, a template, and the curate hook's catalog list. (done)
- [[Ticket-01KZ75R34PGN7WH6HCP44B85A2]] Add Acceptance type with verified_by edge — Add an Acceptance concept type carrying one atomic, checkable condition, linked to its Feature and to whatever proves it via verified_by. (done)
- [[Ticket-01KZ75R39PENN65G92HKA108H3]] Cover Risk and Acceptance in sample-knowledge — Extend sample-knowledge with a Risk and an Acceptance node on the auth chain so the new types are covered by validate, doctor and the golden pack assertions like every other type. (done)

Progress: 3/3 done

## Related tickets

- [github #4](https://github.com/SpillwaveSolutions/project-knowledge-capture/issues/4)
