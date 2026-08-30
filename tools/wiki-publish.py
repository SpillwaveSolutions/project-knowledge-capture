#!/usr/bin/env python3
"""Publish the worklog publish-manifest to the GitHub wiki. wiki-publish skill sections 0,3,4,5."""
import hashlib, json, os, pathlib, subprocess, sys

REPO = pathlib.Path(__file__).resolve().parents[1]
CHECKOUT = REPO / ".work/wiki-checkout"
LEDGER = REPO / ".work/published.json"
BROWSE = "https://github.com/SpillwaveSolutions/project-knowledge-capture/wiki/"
COMMIT_MSG = os.environ.get("WIKI_COMMIT_MSG", "publish: wiki pages")


def sha12(text):
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def strip_frontmatter(text):
    """Gollum renders YAML frontmatter as raw text. Strip it in the copy only (section 3)."""
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---", 4)
    if end == -1:
        return text
    nl = text.find("\n", end + 1)
    return text[nl + 1:].lstrip("\n") if nl != -1 else text


manifest = json.load(open(REPO / "docs/.index/publish-manifest.json"))
pages = list(manifest["pages"] if isinstance(manifest, dict) and "pages" in manifest else manifest)
if isinstance(manifest, dict) and manifest.get("sidebar"):
    sb = manifest["sidebar"]
    pages.append({
        "source": sb["source"],
        "wiki_key": "sidebar",
        "page_name": "_Sidebar",
        "render": "as-is",
        "render_hash": sb.get("render_hash"),
        "frozen": False,
    })
ledger = json.load(open(LEDGER)) if LEDGER.exists() else {}

published, skipped, missing, frozen_violation = [], [], [], []
CHECKOUT.mkdir(parents=True, exist_ok=True)

for p in pages:
    src = REPO / p["source"]
    key = p.get("wiki_key") or p["page_name"]
    if not src.is_file():
        missing.append(p["source"])
        continue
    raw = src.read_text(encoding="utf-8")
    src_hash = sha12(raw)
    entry = ledger.get(key, {})

    # section 0: frozen guards the SOURCE. A changed frozen source is a frozen-doc edit.
    if p.get("frozen") and entry.get("source_hash") and entry["source_hash"] != src_hash:
        frozen_violation.append(p["source"])
        continue

    # section 0: skip on render_hash, not source_hash — a banner can change with a frozen source.
    if entry.get("render_hash") and entry["render_hash"] == p.get("render_hash"):
        skipped.append(p["page_name"])
        continue

    out = strip_frontmatter(raw)
    if p.get("render") == "doc+banner" and p.get("banner"):
        out = p["banner"] + "\n\n" + out

    name = "_Sidebar" if key == "sidebar" else p["page_name"]
    (CHECKOUT / f"{name}.md").write_text(out, encoding="utf-8")
    updated = dict(entry)
    updated.update({
        "source": p["source"],
        "url": BROWSE + name,
        "page_id": name,
        "source_hash": src_hash,
        "render_hash": p.get("render_hash"),
    })
    ledger[key] = updated
    published.append(name)

if frozen_violation:
    print("FROZEN SOURCE CHANGED — refusing to publish:", *frozen_violation, sep="\n  ")
    sys.exit(1)

if published:
    subprocess.run(["git", "add", "-A"], cwd=CHECKOUT, check=True)
    # A metadata-only change (frontmatter is stripped) leaves page bytes identical.
    # That is a successful no-op publish, not an error — still record the render_hash.
    dirty = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=CHECKOUT).returncode != 0
    if dirty:
        subprocess.run(["git", "commit", "-q", "-m", COMMIT_MSG], cwd=CHECKOUT, check=True)
        subprocess.run(["git", "push", "-q", "origin", "HEAD"], cwd=CHECKOUT, check=True)
    else:
        print("(page bytes unchanged — ledger updated, nothing pushed)")
    rev = subprocess.run(["git", "rev-parse", "HEAD"], cwd=CHECKOUT,
                         capture_output=True, text=True, check=True).stdout.strip()
    for k, v in ledger.items():
        if v.get("page_id") in published:
            v["rev"] = rev

LEDGER.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"published={len(published)} skipped={len(skipped)} missing={len(missing)}")
for n in published:
    print("  +", n)
if missing:
    print("missing sources:", *missing, sep="\n  - ")
