#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

LOG_DIR="log/$(date +%Y-%m-%d)"
mkdir -p "$LOG_DIR"

exec >>"$LOG_DIR/run.log" 2>&1

echo "=== run started at $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
caffeinate -i uv run python -m helloworks_scraper.main
echo "=== run finished at $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
