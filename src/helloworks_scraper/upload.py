"""Supabase batch upsert into kyujinbox_v2 with hard-coded safety guards."""

import logging
import os

from supabase import Client, create_client

_log = logging.getLogger(__name__)

# 既存 kyujinbox への誤書き込みを物理的に防ぐためのハードコード
TABLE_NAME = "kyujinbox_v2"
RUNS_TABLE_NAME = "kyujinbox_v2_runs"

# 新 Supabase プロジェクトの ref。旧 (rqvncvzxzvbnzokckbfg) への誤接続を防ぐ
_REQUIRED_URL_PREFIX = "https://nxkoudpxvmodmadrrgqq."


def assert_safe_supabase_url() -> None:
    url = os.environ.get("SUPABASE_URL", "")
    assert url.startswith(_REQUIRED_URL_PREFIX), (
        f"想定外 Supabase 接続先 ({url!r}). 期待: {_REQUIRED_URL_PREFIX}* "
        f"旧 Supabase rqvncvzxzvbnzokckbfg への誤接続を防ぐためここで停止します。"
    )


def _make_client() -> Client:
    assert_safe_supabase_url()
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)


def upload_rows(rows: list[dict], batch_size: int = 500) -> int:
    """Batch upsert into kyujinbox_v2. Returns number of rows uploaded."""
    if not rows:
        return 0
    # kyujinbox_v2.url は PRIMARY KEY。70 area × 2 雇用形態の巡回で同一 URL が
    # 必ず複数回出るため、同一バッチに重複が入ると Postgres が 21000
    # (ON CONFLICT DO UPDATE cannot affect row a second time) を返して全停止する。
    # 事前に url で dedup (後勝ち)。
    deduped: dict[str, dict] = {}
    skipped_no_url = 0
    for row in rows:
        url = row.get("url")
        if not url:
            skipped_no_url += 1
            continue
        deduped[url] = row
    unique_rows = list(deduped.values())
    dropped = len(rows) - len(unique_rows) - skipped_no_url
    if dropped or skipped_no_url:
        _log.info(
            "upload dedupe: input=%d unique=%d duplicates_dropped=%d no_url_dropped=%d",
            len(rows), len(unique_rows), dropped, skipped_no_url,
        )
    if not unique_rows:
        return 0
    client = _make_client()
    table = client.table(TABLE_NAME)
    total = 0
    for i in range(0, len(unique_rows), batch_size):
        batch = unique_rows[i : i + batch_size]
        table.upsert(batch).execute()
        total += len(batch)
    return total


def insert_run_start(run_id: str, started_at: str, category_top: str = "legacy_all") -> None:
    client = _make_client()
    client.table(RUNS_TABLE_NAME).insert({
        "run_id": run_id,
        "started_at": started_at,
        "status": "running",
        "category_top": category_top,
    }).execute()


def update_run_finish(
    run_id: str,
    finished_at: str,
    status: str,
    parsed_count: int,
    inserted_count: int,
    rejected_count: int,
    rejected_reasons: dict,
    error_text: str | None = None,
) -> None:
    client = _make_client()
    client.table(RUNS_TABLE_NAME).update({
        "finished_at": finished_at,
        "status": status,
        "parsed_count": parsed_count,
        "inserted_count": inserted_count,
        "rejected_count": rejected_count,
        "rejected_reasons": rejected_reasons,
        "error_text": error_text,
    }).eq("run_id", run_id).execute()
