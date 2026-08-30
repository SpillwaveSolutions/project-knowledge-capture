---
wiki_key: design/retrieval-ladder
doc_type: design
truth_state: current
---

# Retrieval ladder

Git + Markdown is the source of truth on every rung. Everything above Git is
a disposable accelerator you can delete and rebuild. That is the same
philosophy research-graph already states (`rg_project.py`: "the index can be
destroyed and rebuilt"). This note finishes that sketch for PKC.

Each rung attacks a different cost, buys roughly an order of magnitude of
scale, and keeps the rung below it as a runtime fallback:

```
index present  →  use it
else rg on PATH  →  prefilter
else             →  pure Python scan
```

Three tiers, one behavior. `--no-rg` / `--no-index` force a lower rung.

## Rung 1 — ripgrep prefilter (now)

**Cost it attacks:** reading and lowercasing files that cannot possibly match.

**Mechanics:** `find_rg()` / `rg_list_files()` in `pkc_common.py`. Search
AND-intersects `rg -l` per term, then runs the existing Python scorer
(`title×10 / description×5 / tags×4 / min(body,8)`) over only those
candidates. Pack inbound discovery is `rg -lF` of the concept path.
Override with `PKC_RG_PATH` / `OKF_RG_PATH`. Missing rg is not an error.

**Why scores stay identical:** rg only decides which files get read.
Over-selection is harmless (Python re-checks). It cannot under-select for
plain substring terms.

**Why it is first:** no state on disk, so no cache-staleness class of bugs.
Zero new dependencies. Claude Code / Grok hosts usually ship `rg`.

**Ceiling:** still an O(corpus) scan per query — compiled, parallel,
memory-mapped. It only accelerates "which files contain X." Anything that
needs parsed frontmatter from every file is untouched:

| Hot path | Rung 1 helps? | Why |
|---|---|---|
| `pkc_search.py` | yes | candidate prefilter |
| `pkc_pack.py` inbound | yes | reverse index via literal path |
| `okf-graph.py backlinks` | yes | same |
| `pkc_auto_context.py` | partially | detection is narrow (`features/` path or ULID glob); pack inbound is now rg |
| `pkc_validate.py` (PostToolUse via `pkc-curate.sh`) | **no** | must parse frontmatter + resolve links on every concept |
| orphans / type listings / digest / doctor | **no** | need the parsed graph |
| `pkc-curate.sh` catalog refresh | no | directory listing, already cheap |

Those parsed-graph commands are exactly what the per-edit hook runs. That
is what forces rung 2.

Shipped: PKC [#58](https://github.com/SpillwaveSolutions/project-knowledge-capture/issues/58),
okf-plugin [#68](https://github.com/SpillwaveSolutions/okf-plugin/issues/68),
SAC [#31](https://github.com/SpillwaveSolutions/system-architecture-capture/issues/31),
research-graph [#1](https://github.com/SpillwaveSolutions/research-graph/issues/1).

## Rung 2 — stdlib SQLite + FTS5 incremental index (~1k concepts)

**Cost it attacks:** re-parsing files that have not changed since the last
invocation. Today every command rebuilds the graph and throws it away.

**Why SQLite:** `sqlite3` is in the stdlib. FTS5 is compiled into CPython
(doctor already reports it). Honors the hard "no pip dependencies" rule.
One file, atomic transactions, concurrent readers, trivially deletable.

**Do not copy DEKC's `.index/`.** DEKC writes JSON inventory + inverted
tokens and rebuilds the whole thing. That is a full scan plus a JSON parse,
and it has already been committed by accident. The PKC index is SQLite,
incremental, gitignored, and self-healing.

**Shape:**

| Table | Role |
|---|---|
| `meta(schema_version)` | drop-rebuild on mismatch |
| `nodes(path, type, title, description, status, tags, mtime, size)` | concept cards |
| `edges(src, dst, rel)` | indexed both directions — backlinks become a lookup |
| `fts` (FTS5 over title / description / tags / body) | lexical retrieval |

Path: `knowledge/.pkc/index.sqlite`. Gitignore `**/.pkc/`. Never a hook
install, never a pip dep.

**Incremental refresh is the whole trick.** On each invocation the reader
stats the tree (10k stats ≈ tens of milliseconds), compares `mtime+size`
against stored rows, re-parses only what changed, deletes vanished files.
Every reader does this sweep itself rather than trusting `pkc-curate.sh`
to have kept the index fresh — that makes it self-healing against hand
edits, `git checkout`, branch switches, and a disabled hook. Cold rebuild
costs one full scan (what every command pays today). Steady-state queries
are 1–10 ms.

**Scoring identity.** FTS5 `bm25()` with column weights is *not* the same
function as `title.count×10`. Do not pretend it is. Same pattern as rg:

- FTS5 (or `MATCH`) decides candidate files.
- The existing Python scorer ranks them, so `--no-index` and index paths
  stay score-identical.
- A later `--engine fts` can expose raw `bm25()` as an opt-in.

**Why wait for ~1k concepts.** Below that, a full scan is 40–150 ms — under
the Python-startup noise floor — so the index's real cost (invalidation
logic, a second artifact to reason about, a gitignore entry) buys nothing.
working-knowledge is currently ~540 concepts. The rung earns its keep
exactly when the hooks start costing a visible fraction of a second per
edit and per prompt.

**Trigger:** doctor already prints FTS5 availability. Build the index when
`iter_concepts()` ≥ 1000 *or* validate/pack exceeds ~200 ms on a cold
bundle. Until then, leave the module unwritten.

## Rung 3 — okfcli (if ever)

The fast-native slot is already assigned by okf-plugin working rule #1:
prefer `okf` / `okfcli` when installed, else `python3`. A single static
binary (Rust/Go) with the Python scripts as the portable fallback. Do not
invent a second runtime (Ruby closed-won't-do, PKC #60).

## Runtime degradation (load this, do not skip it)

```
def retrieve(bundle, query):
    if index_ok(bundle):          # rung 2
        return from_index(bundle, query)
    if find_rg():                 # rung 1
        return from_rg(bundle, query)
    return from_scan(bundle, query)  # rung 0
```

Git remains the only durable store. `rm -rf knowledge/.pkc` is always a
valid recovery.
