#!/usr/bin/env bash
WORKDIR="/home/seo/.openclaw/workspace"
exec python3 "/home/seo/.openclaw/workspace/src/create_daily_partitions.py" "\$@"
