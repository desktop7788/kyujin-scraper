#!/usr/bin/env bash
# 旧スクレイパー (SetagayaLab) との同時刻突合テスト用。
# 旧と完全一致条件: --category cleaning --employment-type 2 (e=2 only)
# 並列度・filter は main.py / classify.py で既に旧と一致済 (CONCURRENT_REQUESTS=16, 2 段階フィルタ)
set -euo pipefail

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

cd "$(dirname "$0")/.."

LOG_DIR="log/$(date +%Y-%m-%d)-sync"
mkdir -p "$LOG_DIR"

exec >>"$LOG_DIR/cleaning_e2_sync.log" 2>&1

echo "=== sync test started at $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "PATH=$PATH"
echo "uv path: $(command -v uv || echo NOT_FOUND)"
caffeinate -i uv run python -m helloworks_scraper.main --category cleaning --employment-type 2
echo "=== sync test finished at $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
