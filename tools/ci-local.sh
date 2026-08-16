#!/usr/bin/env bash
# Run everything .github/workflows/{ci,worklog}.yml run, locally.
#
# Exists because GitHub Actions stopped producing runs on 2026-08-05 and
# releases needed a verifiable gate in the meantime. Keep it in step with
# the workflows: if you add a CI step there, add it here.
#
# Usage: tools/ci-local.sh          (from the repo root)
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
# CI is an actor. Write paths fail closed without identity.
export SECOND_BRAIN_IDENTITY="${SECOND_BRAIN_IDENTITY:-claude-code/lumenfield-detector}"

pass=0; fail=0
step() {
  local name="$1"; shift
  if out=$("$@" 2>&1); then
    printf '  ok    %s\n' "$name"; pass=$((pass+1))
  else
    printf '  FAIL  %s\n' "$name"; printf '%s\n' "$out" | sed 's/^/          /' | tail -15
    fail=$((fail+1))
  fi
}

BUNDLE=sample-knowledge
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

echo "== unit tests =="
step "test_pkc.py" python3 tests/test_pkc.py
step "test_isolation.py" python3 tests/test_isolation.py

echo "== compile =="
step "py_compile all scripts" bash -c 'python3 -m py_compile scripts/pkc_*.py scripts/brain_session.py'

echo "== bundle health =="
step "validate $BUNDLE"  python3 scripts/pkc_validate.py --bundle "$BUNDLE"
step "doctor $BUNDLE"    python3 scripts/pkc_doctor.py --bundle "$BUNDLE"

echo "== golden pack =="
step "pack >=5 nodes" bash -c "
  python3 scripts/pkc_pack.py features/user-authentication.md --bundle $BUNDLE --hops 2 --json > $TMP/pack.json
  python3 -c \"import json;d=json.load(open('$TMP/pack.json'));assert d['node_count']>=5,d\""
step "tiny <=8 nodes, 1 hop" bash -c "
  python3 scripts/pkc_pack.py features/user-authentication.md --bundle $BUNDLE --tiny --json > $TMP/tiny.json
  python3 -c \"import json;d=json.load(open('$TMP/tiny.json'));assert d['node_count']<=8 and d['hops']==1,d\""
step "mermaid emits flowchart" bash -c "
  python3 scripts/pkc_pack.py features/user-authentication.md --bundle $BUNDLE --mermaid | grep -q flowchart"

echo "== ingestion fixtures =="
step "action items" bash -c "
  python3 scripts/pkc_action_items.py meetings/2026-08-03-auth-design.md --bundle $BUNDLE \
    | grep -qi 'implement\|document'"
step "transcript scrub" bash -c "
  python3 scripts/pkc_transcript.py --file tests/fixtures/transcript_speakers.txt --json \
    | python3 -c \"import json,sys;d=json.load(sys.stdin);assert d['redactions'] or 'REDACTED' in d['notes']\""
step "PR fixture" python3 scripts/pkc_pr_capture.py --json-file tests/fixtures/pr.json \
    --repo "$TMP/pr" --implements user-authentication

echo "== query surfaces =="
step "search" bash -c "
  python3 scripts/pkc_search.py JWT --bundle $BUNDLE --json \
    | python3 -c \"import json,sys;assert json.load(sys.stdin)['count']>=1\""
step "digest" bash -c "
  python3 scripts/pkc_digest.py --bundle $BUNDLE --days 3650 --json \
    | python3 -c \"import json,sys;assert 'open_questions' in json.load(sys.stdin)\""
step "release notes" bash -c "python3 scripts/pkc_release_notes.py --bundle $BUNDLE | grep -qi release"
step "thread capture" bash -c "
  python3 scripts/pkc_thread.py --file tests/fixtures/thread_slack.txt --json \
    | python3 -c \"import json,sys;assert json.load(sys.stdin)['attendees']\""
step "ADR import" bash -c "
  python3 scripts/pkc_adr_import.py --from tests/fixtures/adr --repo $TMP/adr --dry-run | grep -q proposed"

echo "== auto-context hook =="
# Two jobs: inject on a Feature, stay silent otherwise. Silence is the half a
# regression breaks invisibly, so it is asserted rather than assumed.
step "injects a tiny pack on a Feature" bash -c "
  python3 scripts/pkc_auto_context.py --bundle $BUNDLE \
    --prompt 'recap features/user-authentication.md' > $TMP/inject.json
  python3 -c \"import json; c=json.load(open('$TMP/inject.json'))['hookSpecificOutput']; \
    assert c['hookEventName']=='UserPromptSubmit', c; \
    assert 'User authentication' in c['additionalContext']\""
step "silent on an unrelated prompt" bash -c "
  test -z \"\$(python3 scripts/pkc_auto_context.py --bundle $BUNDLE \
    --prompt 'run the tests and fix what breaks')\""

echo "== materialize idempotency =="
step "second run reports 0 created" bash -c "
  python3 scripts/pkc_materialize.py --repo $TMP/mat --bundle knowledge --fold tests/fixtures/fold.json >/dev/null
  python3 scripts/pkc_materialize.py --repo $TMP/mat --bundle knowledge --fold tests/fixtures/fold.json \
    | grep -q '0 created'"
# `0 created` was true before incremental materialize existed. `unchanged`
# (short-circuited on fingerprint) vs `skipped` (rendered, then discarded) is
# the distinction that actually proves nothing was rendered.
step "re-materialize renders nothing" bash -c "
  python3 scripts/pkc_materialize.py --repo $TMP/mat --bundle knowledge \
    --fold tests/fixtures/fold.json --json > $TMP/mat3.json
  python3 -c \"import json; r=json.load(open('$TMP/mat3.json'))['results']; \
    a={x['action'] for x in r}; assert a == {'unchanged'}, a\""

echo "== worklog invariants =="
step "hooks/pre-commit" env WORKLOG_SKIP_BRANCH_GUARD=1 hooks/pre-commit
step "commit-msg on commits vs origin/main" bash -c '
  for sha in $(git rev-list --no-merges origin/main..HEAD); do
    git log -1 --format=%B "$sha" > "'"$TMP"'/msg"
    hooks/commit-msg "'"$TMP"'/msg" || { echo "bad message on $sha"; exit 1; }
  done'

echo
echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ] || exit 1
