#!/usr/bin/env bash
# Post-edit hook: refresh catalog indexes + light validate after PKC knowledge edits.
# Mirrors okf-curate.sh style — silent no-op outside a knowledge bundle.
set -euo pipefail

FILE="${1:-}"
if [[ -z "$FILE" ]]; then
  FILE="$(python3 -c 'import json,sys
try:
    print(json.load(sys.stdin).get("tool_input", {}).get("file_path", ""))
except Exception:
    pass' 2>/dev/null || true)"
fi

if [[ -z "$FILE" ]]; then
  exit 0
fi
case "$FILE" in
  *.md|*.markdown) ;;
  *) exit 0 ;;
esac

find_bundle_root() {
  local dir
  dir="$(cd "$(dirname "$FILE")" 2>/dev/null && pwd)" || return 1
  while [[ "$dir" != "/" ]]; do
    if [[ -f "$dir/index.md" ]] && grep -q 'okf_version' "$dir/index.md" 2>/dev/null; then
      echo "$dir"
      return 0
    fi
    if [[ -d "$dir/.okf" && -f "$dir/.okf/index.md" ]]; then
      echo "$dir/.okf"
      return 0
    fi
    if [[ -d "$dir/knowledge" && -f "$dir/knowledge/index.md" ]]; then
      echo "$dir/knowledge"
      return 0
    fi
    dir="$(dirname "$dir")"
  done
  return 1
}

BUNDLE_ROOT="$(find_bundle_root || true)"
if [[ -z "${BUNDLE_ROOT:-}" ]]; then
  exit 0
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# Prefer plugin root when installed
PLUGIN_SCRIPTS="${CLAUDE_PLUGIN_ROOT:-$ROOT}/scripts"

echo "pkc-curate: bundle $BUNDLE_ROOT (touched: $FILE)"

# Refresh catalog for the directory of the edited file when it is a catalog concept
CAT="$(basename "$(dirname "$FILE")")"
case "$CAT" in
  meetings|experiments|discoveries|decisions|features|requirements|specs|designs|releases|code|packages|tickets)
    python3 "${PLUGIN_SCRIPTS}/pkc_common.py" resolve-root --repo "$(dirname "$BUNDLE_ROOT")" >/dev/null 2>&1 || true
    python3 - <<PY
from pathlib import Path
import sys
sys.path.insert(0, "${PLUGIN_SCRIPTS}")
from pkc_common import refresh_catalog_index
refresh_catalog_index(Path("${BUNDLE_ROOT}"), "${CAT}")
print("pkc-curate: refreshed ${CAT}/index.md")
PY
    ;;
esac

# Light validate (warnings ok)
python3 "${PLUGIN_SCRIPTS}/pkc_validate.py" --bundle "$BUNDLE_ROOT" || true
