# HelloWorks Scraper v2

Multi-industry kyujinbox.com scraper for HelloWorks. Writes to `kyujinbox_v2` table in Supabase project `nxkoudpxvmodmadrrgqq`.

## Setup

    uv sync
    cp .env.example .env  # fill in SUPABASE_SERVICE_ROLE_KEY

## Run

    uv run python -m helloworks_scraper.main

## Run a subset (manual smoke test)

    uv run python -m helloworks_scraper.main --category security_cleaning_inspection --area 東京都

## Test

    uv run pytest

## Schedule (macOS launchd)

    cp ops/HelloWorksScraper.plist ~/Library/LaunchAgents/
    launchctl load ~/Library/LaunchAgents/HelloWorksScraper.plist
