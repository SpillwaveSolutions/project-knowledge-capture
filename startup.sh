#!/bin/sh
set -eu
cd /workspace
if curl -sf -o /dev/null --max-time 2 http://127.0.0.1:8080/; then
  exit 0
fi
node scripts/serve-preview.mjs >>/tmp/app-startup.log 2>&1 &
# brief wait so revive health checks pass
for i in 1 2 3 4 5 6 7 8 9 10; do
  if curl -sf -o /dev/null --max-time 1 http://127.0.0.1:8080/; then
    exit 0
  fi
  sleep 0.3
done
exit 0
