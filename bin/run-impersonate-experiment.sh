#!/usr/bin/env bash
# 2026-05-19 02:30 JST 比較実験: 旧 (Windows 02:00 通常 run) と
# 新 (Mac 02:30 chrome124 impersonation) を同条件で並走させ、
# TLS/HTTP fingerprint 差が kyujinbox の応答に効くか確定する。
#
# 旧との比較条件:
#   --category cleaning  (旧と同一カテゴリ)
#   --employment-type 2  (旧と同一 e=2 アルバイトのみ)
#   --impersonate chrome124  (本物 Chrome 126 相当の TLS handshake + HTTP/2)
#   filter ON (cleaning にも off_topic_title 適用 = noise 除去)
#
# 比較指標 (DB の kyujinbox_v2 + 旧 kyujinbox を突合):
#   (title, recruiting_company_name, area) 完全一致率
#   今日の vanilla scrapy ベースライン: 旧 15% / 新 73% との差分
set -euo pipefail

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

cd "$(dirname "$0")/.."

LOG_DIR="log/$(date +%Y-%m-%d)-impersonate"
mkdir -p "$LOG_DIR"
exec >>"$LOG_DIR/cleaning_e2_chrome124.log" 2>&1

echo "=== impersonate experiment started at $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "PATH=$PATH"
echo "uv path: $(command -v uv || echo NOT_FOUND)"
caffeinate -i uv run python -m helloworks_scraper.main \
    --category cleaning \
    --employment-type 2 \
    --impersonate chrome124
echo "=== finished at $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
