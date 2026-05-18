#!/usr/bin/env bash
# Wrapper that only fires on 2026-05-19 to limit the experiment to ONE day.
# After the experiment fires once, the user can `launchctl unload` the plist.
# (Or this guard prevents accidental daily re-run if plist is left loaded.)
set -euo pipefail

TARGET_DATE="2026-05-19"
TODAY="$(date +%F)"

if [[ "$TODAY" != "$TARGET_DATE" ]]; then
    echo "[guard] today=$TODAY != target=$TARGET_DATE, skipping experiment." \
        >> /Users/tatsu/Dropbox/happy_project/ON/HelloWorksScraper/log/launchd-impersonate.err.log
    exit 0
fi

exec /Users/tatsu/Dropbox/happy_project/ON/HelloWorksScraper/bin/run-impersonate-experiment.sh
