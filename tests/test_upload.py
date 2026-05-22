# tests/test_upload.py
import os
from unittest.mock import MagicMock

import pytest

from helloworks_scraper import upload


def test_table_name_hardcoded():
    """TABLE_NAME must be kyujinbox_v2 to prevent accidental writes to kyujinbox."""
    assert upload.TABLE_NAME == "kyujinbox_v2"


def test_assert_supabase_url_rejects_old_project(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://rqvncvzxzvbnzokckbfg.supabase.co")
    with pytest.raises(AssertionError, match="想定外"):
        upload.assert_safe_supabase_url()


def test_assert_supabase_url_accepts_new_project(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://nxkoudpxvmodmadrrgqq.supabase.co")
    upload.assert_safe_supabase_url()


def test_assert_supabase_url_missing(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    with pytest.raises(AssertionError):
        upload.assert_safe_supabase_url()


def test_upload_batches(mocker):
    mock_client = MagicMock()
    mock_table = mock_client.table.return_value
    mocker.patch.object(upload, "_make_client", return_value=mock_client)

    rows = [{"url": f"https://example.com/{i}"} for i in range(7)]
    upload.upload_rows(rows, batch_size=3)

    # 7 rows / batch_size 3 = 3 calls (3 + 3 + 1)
    assert mock_table.upsert.call_count == 3
    assert mock_client.table.call_args_list[0][0] == ("kyujinbox_v2",)


def test_upload_empty(mocker):
    mock_client = MagicMock()
    mocker.patch.object(upload, "_make_client", return_value=mock_client)
    upload.upload_rows([])
    mock_client.table.assert_not_called()


def test_upload_dedupes_duplicate_urls(mocker):
    # 70 area × 2 employment type 巡回で同一 URL が複数回現れる前提を再現
    mock_client = MagicMock()
    mock_table = mock_client.table.return_value
    mocker.patch.object(upload, "_make_client", return_value=mock_client)

    rows = [
        {"url": "https://example.com/a", "title": "first"},
        {"url": "https://example.com/b", "title": "B"},
        {"url": "https://example.com/a", "title": "second"},  # 重複
        {"url": "https://example.com/c", "title": "C"},
    ]
    inserted = upload.upload_rows(rows, batch_size=10)

    # 3 unique URL → 1 バッチ
    assert mock_table.upsert.call_count == 1
    sent = mock_table.upsert.call_args[0][0]
    assert len(sent) == 3
    assert inserted == 3
    # 後勝ち: url=a は title="second" であるべき
    by_url = {r["url"]: r for r in sent}
    assert by_url["https://example.com/a"]["title"] == "second"


def test_upload_skips_rows_without_url(mocker):
    mock_client = MagicMock()
    mock_table = mock_client.table.return_value
    mocker.patch.object(upload, "_make_client", return_value=mock_client)

    rows = [
        {"url": "https://example.com/a"},
        {"title": "no url"},
        {"url": None, "title": "explicit null"},
    ]
    inserted = upload.upload_rows(rows, batch_size=10)

    assert mock_table.upsert.call_count == 1
    sent = mock_table.upsert.call_args[0][0]
    assert len(sent) == 1
    assert inserted == 1
