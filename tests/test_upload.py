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
