# Traceability

_The evidence chain: plan → item → ticket → code → release, forward and backward. Generated from `docs/.index/_graph.json`; do not edit._

### pkc_pack misses concepts that point at the seed
`01KZD6QRF62XDCPBDH5BN0H1RD` · status: todo

### Re-materialize with no changes still churns catalogs and log
`01KZD15ZR0JEKW6FA0HXM7W9CG` · status: todo

### Add tools/ci-local.sh mirroring both CI workflows
`01KZCA0DK74YQW82H4HZ1DJ8Q8` · status: done

### Release v0.4.2
`01KZC789NPHSTEVC7D6BEKGY4D` · status: done

### Author User-Guide, Design-Doc, and Worklog-Spec
`01KZC6JVCDDSH3CYMX1KAGZQRQ` · status: done

### Release v0.4.1
`01KZC4FVRKYYY0P76RW251H4R1` · status: done

### Resolve worklog IA gate warnings before they harden
`01KZ75VWSERRKEZE957R1MBE9B` · status: done
- references: [github#18](https://github.com/SpillwaveSolutions/project-knowledge-capture/issues/18)

### Adopt WikiTicket SDD in the PKC repo
`01KZ75R3YBQAH47CYTF06A4WF0` · status: done
- targets: release/v0.5.0

### Expose capture over MCP
`01KZ75R3S2X1G4PCTGMMSR8BWA` · status: todo
- belongs-to: MCP server mode
- references: [github#17](https://github.com/SpillwaveSolutions/project-knowledge-capture/issues/17)
- targets: release/v0.5.0

### Expose validate over MCP
`01KZ75R3M6BYQ643NKDCCSEEZC` · status: todo
- belongs-to: MCP server mode
- references: [github#16](https://github.com/SpillwaveSolutions/project-knowledge-capture/issues/16)
- targets: release/v0.5.0

### Expose pack over MCP
`01KZ75R3EXEG4GVGRP2S9CCKZ4` · status: todo
- belongs-to: MCP server mode
- references: [github#15](https://github.com/SpillwaveSolutions/project-knowledge-capture/issues/15)
- targets: release/v0.5.0

### Cover Risk and Acceptance in sample-knowledge
`01KZ75R39PENN65G92HKA108H3` · status: done
- belongs-to: Risk and Acceptance concepts
- references: [github#14](https://github.com/SpillwaveSolutions/project-knowledge-capture/issues/14)
- targets: release/v0.5.0

### Add Acceptance type with verified_by edge
`01KZ75R34PGN7WH6HCP44B85A2` · status: done
- belongs-to: Risk and Acceptance concepts
- references: [github#13](https://github.com/SpillwaveSolutions/project-knowledge-capture/issues/13)
- targets: release/v0.5.0

### Add Risk type with mitigates and exposes edges
`01KZ75R2ZJGMNBHD82WZXPCNX4` · status: done
- belongs-to: Risk and Acceptance concepts
- references: [github#12](https://github.com/SpillwaveSolutions/project-knowledge-capture/issues/12)
- targets: release/v0.5.0

### Assert zero-write re-materialize in CI
`01KZ75R2TEF13SKZYZ3DSBS5BZ` · status: done
- belongs-to: Incremental materialize
- references: [github#11](https://github.com/SpillwaveSolutions/project-knowledge-capture/issues/11)
- targets: release/v0.5.0

### Skip unchanged ULIDs without rewriting
`01KZ75R2NDYVCGERRTKE9XCRM2` · status: done
- belongs-to: Incremental materialize
- references: [github#10](https://github.com/SpillwaveSolutions/project-knowledge-capture/issues/10)
- targets: release/v0.5.0

### Fingerprint worklog items on materialize
`01KZ75R2FPH92VY79KNR6MP59E` · status: done
- belongs-to: Incremental materialize
- references: [github#9](https://github.com/SpillwaveSolutions/project-knowledge-capture/issues/9)
- targets: release/v0.5.0

### Gate injection behind pack.auto_inject_on_feature
`01KZ75R2ADREHM3JD22V5C5HE7` · status: todo
- belongs-to: Agent auto-context injection
- references: [github#8](https://github.com/SpillwaveSolutions/project-knowledge-capture/issues/8)
- targets: release/v0.5.0

### Inject tiny pack for the detected Feature
`01KZ75R254CS97W8MNX9CV3SNF` · status: todo
- belongs-to: Agent auto-context injection
- references: [github#7](https://github.com/SpillwaveSolutions/project-knowledge-capture/issues/7)
- targets: release/v0.5.0

### Detect Feature path or ULID in agent context
`01KZ75R1ZYFEZVPWDY73CK4P4N` · status: todo
- belongs-to: Agent auto-context injection
- references: [github#6](https://github.com/SpillwaveSolutions/project-knowledge-capture/issues/6)
- targets: release/v0.5.0

### MCP server mode
`01KZ75NQCMYGFYRCVJATEBVBRB` · status: todo
- references: [github#5](https://github.com/SpillwaveSolutions/project-knowledge-capture/issues/5)
- contains: Expose pack over MCP
- contains: Expose validate over MCP
- contains: Expose capture over MCP

### Risk and Acceptance concepts
`01KZ75NQ7VFPF3YESB5P90DR29` · status: todo
- references: [github#4](https://github.com/SpillwaveSolutions/project-knowledge-capture/issues/4)
- contains: Add Risk type with mitigates and exposes edges
- contains: Add Acceptance type with verified_by edge
- contains: Cover Risk and Acceptance in sample-knowledge

### Incremental materialize
`01KZ75NQ2VDVFD3R9F0SV38YEN` · status: todo
- references: [github#3](https://github.com/SpillwaveSolutions/project-knowledge-capture/issues/3)
- contains: Fingerprint worklog items on materialize
- contains: Skip unchanged ULIDs without rewriting
- contains: Assert zero-write re-materialize in CI

### Agent auto-context injection
`01KZ75NC58VJD8E219BYAYPBPA` · status: todo
- references: [github#2](https://github.com/SpillwaveSolutions/project-knowledge-capture/issues/2)
- contains: Detect Feature path or ULID in agent context
- contains: Inject tiny pack for the detected Feature
- contains: Gate injection behind pack.auto_inject_on_feature

