#!/usr/bin/env bash
WORK="/home/seo/.openclaw/workspace"
LOG="$WORK/logs/cron_migration.log"
name="${0##*/}"
name_no_ext="${name%.*}"
src_py="$WORK/src/${name_no_ext}.py"
if [ -f "$src_py" ]; then
  exec /usr/bin/env python3 "$src_py" >> "$LOG" 2>&1
else
  echo "["$(date -Iseconds)"] shim: called $0 but no src script at $src_py" >> "$LOG"
  exit 0
fi
