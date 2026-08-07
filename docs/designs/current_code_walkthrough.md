---
wiki_key: design/current-code-walkthrough
doc_type: design
truth_state: current
generated_at: 2026-08-06T18:42:39Z
tag: v0.4.1
git_hash: ddcf3c4b71829a6db0742c24a2f742f1d476fe82
branch: docs/user-guide-design-spec
roadmap: docs/roadmap.md
---

# Code Walkthrough — Project Knowledge Capture

Read this after `Design-Doc`. That document explains *why*; this one walks the actual code at `ddcf3c4` (tag `v0.4.1`). Every claim cites `path — symbol(), lines N–M`, verified against the tree rather than recalled.

## Where to start

If you read only one file, read `scripts/pkc_common.py`. It is 616 lines and contains every invariant the other seventeen scripts depend on. The rest of the codebase is variations on "gather some fields, call `write_concept()`".

## 1. The YAML layer

PKC parses and emits YAML frontmatter without PyYAML.

**`_parse_simple_yaml()` — `scripts/pkc_common.py`, lines 170–235.** A hand-written indentation-stack parser. It keeps `stack: list[tuple[int, Any]]` of `(indent, container)` pairs, popping when indentation decreases. It handles three shapes: `- item` list entries, `key:` block openers, and `key: value` scalars. Its one clever move is at the list-under-key case — when a `- ` line arrives and the current container is an empty dict, it retroactively converts that dict into a list in the grandparent (lines 187–197). This is how `links:` followed by `- target: ...` parses correctly.

**`_scalar()` — lines 244–265.** Coerces `true`/`yes`, `false`/`no`, `null`/`~`/`none`, ints, floats, quoted strings, and inline `[a, b]` arrays. Everything else stays a string.

**`dump_frontmatter()` / `_dump_key()` — lines 303–339.** The inverse. `_dump_key()` recurses for dicts, and for lists chooses between inline `[a, b, c]` (when every element is a simple token matching `^[\w./:@+-]+$`) and block form. `_fmt_scalar()` (lines 342–353) quotes anything containing YAML-significant characters.

**Why this matters when editing:** the parser is not general YAML. Multi-line strings, anchors, and flow maps are not supported. If you add a frontmatter field, keep it to scalars, flat lists, or lists of single-level dicts.

## 2. The write path

**`write_concept()` — `scripts/pkc_common.py`, lines 356–396.** Every concept write goes through here. Trace the branches:

- **New file** (lines 393–396): strips the control keys `force` and `stable_timestamp` out of the frontmatter, writes, returns `"created"`.
- **Existing file, `merge=True`** (the default): parses the old frontmatter, then checks the `truth_state` barrier — if the stored state is `snapshot`, `superseded`, or `archived` and the incoming write claims `current`, it returns `"skipped"` unless `force` is set. This is what stops a routine materialize from trampling a frozen snapshot.
- **Merge semantics**: `new_fm = {**old_fm, **incoming}` — old keys survive unless explicitly overwritten.
- **`stable_timestamp`**: when set and the title is unchanged, the *old* timestamp is retained, so re-running capture produces no diff.
- **Content comparison**: the rendered file is compared to the existing bytes; identical content returns `"skipped"` **without writing**. This is the idempotency guarantee, and it is a byte comparison, not a heuristic.

The three-way return value (`created` / `updated` / `skipped`) is consumed by every caller for its summary line, and by CI, which greps for `0 created`.

## 3. Materialization

**`load_fold()` — `scripts/pkc_materialize.py`, lines 37–50.** Normalizes input. `bin/worklog fold` emits a bare JSON array; the test fixture uses `{"meta": ..., "items": [...]}`; some sources use `entities`. All three land as `{"items": [...], "meta": {...}}`. If you are debugging a "no items" report, check here first.

**`item_fingerprint()` — lines 90–95.** Builds a list of `key=repr(value)` strings over `FINGERPRINT_FIELDS` (lines 85–88), appends the external reference, and hashes with `content_fingerprint()`. Using `repr()` rather than `str()` keeps `None` distinguishable from the string `"None"`.

**`fingerprint_matches()` — lines 98–103.** Reads the target file, parses only its frontmatter, compares `source_fingerprint`. Returns `False` for a missing file, which is what makes first-run behavior correct without a special case.

**`materialize_item()` — lines 106–225.** The core mapping. Read it in two halves:

- **Feature half** (lines ~122–190): fires when `level` is in `LEVEL_FEATURE` (`{"epic", "story"}`) and `features` is in the include set. The path slug appends the last six characters of the ULID, so two items with the same title do not collide. The fingerprint guard sits at the top: on a match it appends a `skipped` result and never builds the frontmatter dict or body string.
- **TicketLink half** (lines ~192–224): fires for any item with a ULID. Same fingerprint guard, same shape.

Both halves set `source_fingerprint` in the frontmatter they write. That is the value the *next* run compares against.

**The guard pattern to preserve.** Both halves use `if <path> and not force and fingerprint_matches(...)` / `elif <path>` rather than wrapping the build in a conditional. Keep the short-circuit above the frontmatter construction — putting it below would still write correctly but would forfeit the entire point.

**Why the short-circuit reports `unchanged` and not `skipped`.** `write_concept()` also returns `skipped` for byte-identical content, and did so before fingerprints existed. If both paths shared a label, no observer outside the process could tell whether an item was short-circuited or rendered-then-discarded — and neither could a file-mtime check, since nothing is written in either case. The distinct label is the only external evidence the optimization is working, which is what CI asserts.

## 4. Catalogs and the log

**`ensure_bundle()` — lines 467–496** creates `index.md` with `okf_version`, seeds `log.md`, and ensures a catalog index for every entry in `CATALOGS`.

**`refresh_catalog_index()` — lines 426–444** rebuilds a catalog's `index.md` from the files actually on disk, reading each concept's title from its frontmatter. It is a full regeneration, not an append, so a deleted concept disappears from the index.

**`append_log()` — lines 447–464** appends a timestamped line under today's date heading, creating the heading if absent, and collapses runs of blank lines.

## 5. Typed edges

**`add_typed_link()` — lines 499–530.** Writes the edge in two places: the `links` list in frontmatter, and a Markdown bullet under `## Related` in the body. It dedupes on the `(target, rel)` pair and returns `"exists"` when the edge is already present. Targets are normalized to a leading `/`.

The dual representation is intentional: frontmatter for traversal, body link for a human reading the raw file in a diff.

## 6. The two hook systems in `hooks/`

This directory is deliberately dual-purpose and easy to misread:

- **`hooks/hooks.json`** — the Claude plugin manifest. Fires `scripts/pkc-curate.sh` on `Write|Edit|MultiEdit`.
- **`hooks/pre-commit`, `pre-merge-commit`, `commit-msg`** — git hooks installed by worklog, active because `core.hooksPath` points at this directory.

They coexist because `hooks.json` is not a valid git hook name, so git ignores it.

**`scripts/pkc-curate.sh`.** Reads the edited file path from either `$1` or the JSON on stdin (`tool_input.file_path`). Exits silently for non-Markdown. `find_bundle_root()` walks up looking for an `index.md` containing `okf_version`, or a `.okf/` or `knowledge/` directory. Outside a bundle it exits 0 silently — that silence is required, because a hook that errors blocks the edit.

## 7. Tests

`tests/test_pkc.py` — 27 tests, plain `unittest`, no pytest. Classes are small and each owns a `tempfile.mkdtemp()` bundle in `setUp`.

`TestIncrementalMaterialize` is worth reading as the model for testing this codebase. `test_unchanged_item_skips_without_rendering` monkeypatches `pkc_materialize.write_concept` with a counting wrapper and asserts the call list is empty. That asserts the *behavior* (nothing was rendered) rather than a proxy like file mtime — mtime would have passed before the feature existed, because `write_concept()` already avoided writing identical content.

Run one class: `python3 tests/test_pkc.py TestIncrementalMaterialize`.

## 8. Adding a capability

Four files move in lockstep:

1. `skills/<name>/SKILL.md` — the agent procedure. The frontmatter `description` is what triggers it.
2. `commands/<name>.md` — a thin wrapper passing `$ARGUMENTS`.
3. `scripts/pkc_<name>.py` — the deterministic part. Take `--repo` and `--bundle`; add `--json`.
4. The `typecheck` list in `package.json`, a step in `.github/workflows/ci.yml`, and the tables in `README.md` and `AGENTS.md`.

Skills reference scripts as `"${CLAUDE_PLUGIN_ROOT}/scripts/…"`, never relative paths — the plugin runs from an install directory, not from this repo.

## 9. Traps

| Trap | Detail |
|---|---|
| Bare commands hit `sample-knowledge/` | `resolve_knowledge_root()` (lines 158–167) prefers `knowledge/`, then `sample-knowledge/`. Creating the former silently retargets everything. |
| New rendered field, stale fingerprint | Add it to `FINGERPRINT_FIELDS` or it will never trigger a re-render. |
| `zsh` does not word-split | `worklog add $FLAGS` sends one argument, not several. Write flags literally or run under `bash`. |
| Editing `docs/roadmap.md` | Generated. `hooks/pre-commit` regenerates and diffs, and fails the commit. |
| Hand-editing `.work/*.jsonl` | Breaks the append-only log. Use `bin/worklog`. |
