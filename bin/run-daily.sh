#!/usr/bin/env bash
set -euo pipefail

# launchd は最小限の PATH (/usr/bin:/bin:...) で起動するため、uv や caffeinate を
# 確実に解決するためインタラクティブシェルと同じ PATH を再構築する。
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

# HTTPCACHE を Dropbox 外に逃がす (Dropbox 配下で蓄積すると数十万ファイルが毎朝
# 同期され他 scraper を巻き込んで詰まる、memory: 2026-05-20)。/tmp は再起動で消える
# が、Scrapy が起動時に存在しなければ自動作成するので問題なし。
export HELLOWORKS_HTTPCACHE_DIR="/tmp/.scrapy-helloworks/httpcache"

cd "$(dirname "$0")/.."

LOG_DIR="log/$(date +%Y-%m-%d)"
mkdir -p "$LOG_DIR"

exec >>"$LOG_DIR/run.log" 2>&1

echo "=== run started at $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "PATH=$PATH"
echo "uv path: $(command -v uv || echo NOT_FOUND)"
caffeinate -i uv run python -m helloworks_scraper.main
echo "=== run finished at $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
