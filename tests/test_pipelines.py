# tests/test_pipelines.py
import json
import os
import tempfile
from unittest.mock import MagicMock

import pytest
from scrapy.exceptions import DropItem

from helloworks_scraper.items import KyujinboxV2Item
from helloworks_scraper.pipelines import ClassifyPipeline, JsonLinesPipeline, RunStats


def make_item(**overrides):
    base = {
        "url": "https://example.com/jb/abc",
        "category_top": "security_cleaning_inspection",
        "category_keywords": "警備-清掃-点検",
        "area": "東京都",
        "employment_type": 2,
        "title": "ホテル清掃スタッフ",
        "recruiting_company_name": "Acme",
        "media_name": "Indeed",
        "job_type": "アルバイト",
        "salary_type": "時給",
        "wage_text": "時給1200円",
        "wage_numbers": 1200,
        "address": "東京都新宿区",
        "pref": "東京都",
        "city": "新宿区",
        "category": "cleaning",
        "category_match": "清掃",
        "scrape_run_id": "00000000-0000-0000-0000-000000000000",
    }
    base.update(overrides)
    item = KyujinboxV2Item()
    for k, v in base.items():
        item[k] = v
    return item


def test_classify_pipeline_accepts_valid_item():
    stats = RunStats()
    pipeline = ClassifyPipeline(stats)
    item = make_item()
    result = pipeline.process_item(item, MagicMock())
    assert result is item
    assert stats.parsed_count == 1
    assert stats.rejected_count == 0


def test_classify_pipeline_rejects_with_reason():
    stats = RunStats()
    pipeline = ClassifyPipeline(stats)
    item = make_item(wage_numbers=6000)
    with pytest.raises(DropItem):
        pipeline.process_item(item, MagicMock())
    assert stats.parsed_count == 1
    assert stats.rejected_count == 1
    assert stats.rejected_reasons["wage_over_5000"] == 1


def test_jsonl_pipeline_writes_lines():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "test.jsonl")
        pipeline = JsonLinesPipeline(path)
        pipeline.open_spider(MagicMock())
        pipeline.process_item(make_item(), MagicMock())
        pipeline.process_item(make_item(url="https://example.com/jb/xyz"), MagicMock())
        pipeline.close_spider(MagicMock())

        with open(path) as f:
            lines = f.readlines()
        assert len(lines) == 2
        first = json.loads(lines[0])
        assert first["title"] == "ホテル清掃スタッフ"
        assert first["category"] == "cleaning"
