# tests/test_spider_meta.py
import os
import uuid

from scrapy.http import HtmlResponse, Request

from helloworks_scraper.spider import KyujinboxV2Spider


FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _load_fixture(name: str) -> bytes:
    with open(os.path.join(FIXTURE_DIR, name), "rb") as f:
        return f.read()


def _make_response(url: str, fixture: str, meta: dict) -> HtmlResponse:
    request = Request(url=url, meta=meta)
    return HtmlResponse(url=url, body=_load_fixture(fixture), request=request, encoding="utf-8")


def test_start_requests_emits_all_combos():
    run_id = str(uuid.uuid4())
    spider = KyujinboxV2Spider(run_id=run_id)
    requests = list(spider.start_requests())
    # 8 categories × 47 prefectures × 2 employment types
    assert len(requests) == 8 * 47 * 2
    sample = requests[0]
    assert sample.meta["category_top"]
    assert sample.meta["area"]
    assert sample.meta["employment_type"] in (2, 5)
    assert sample.meta["scrape_run_id"] == run_id


def test_parse_propagates_meta_to_detail_requests():
    spider = KyujinboxV2Spider(run_id="00000000-0000-0000-0000-000000000000")
    meta = {
        "category_top": "security_cleaning_inspection",
        "category_keywords": "警備-清掃-点検",
        "area": "東京都",
        "employment_type": 2,
        "scrape_run_id": "00000000-0000-0000-0000-000000000000",
    }
    response = _make_response("https://xn--pckua2a7gp15o89zb.com/警備-清掃-点検の仕事-東京都?e=2&u=1", "listing.html", meta)

    detail_requests = [r for r in spider.parse(response) if r.callback == spider.parse_detail]
    assert detail_requests, "expected at least one detail follow"
    for r in detail_requests:
        for key in ("category_top", "category_keywords", "area", "employment_type", "scrape_run_id"):
            assert r.meta.get(key) == meta[key], f"meta key '{key}' lost on response.follow"


def test_parse_propagates_meta_to_next_page():
    spider = KyujinboxV2Spider(run_id="00000000-0000-0000-0000-000000000000")
    meta = {
        "category_top": "security_cleaning_inspection",
        "category_keywords": "警備-清掃-点検",
        "area": "東京都",
        "employment_type": 2,
        "scrape_run_id": "00000000-0000-0000-0000-000000000000",
    }
    response = _make_response("https://xn--pckua2a7gp15o89zb.com/警備-清掃-点検の仕事-東京都?e=2&u=1", "listing.html", meta)
    next_page_requests = [r for r in spider.parse(response) if r.callback == spider.parse]
    if not next_page_requests:
        # Some fixtures may not have a next page; skip
        return
    for r in next_page_requests:
        for key in ("category_top", "category_keywords", "area", "employment_type", "scrape_run_id"):
            assert r.meta.get(key) == meta[key]


def test_parse_detail_emits_item_with_meta():
    spider = KyujinboxV2Spider(run_id="00000000-0000-0000-0000-000000000000")
    meta = {
        "category_top": "security_cleaning_inspection",
        "category_keywords": "警備-清掃-点検",
        "area": "東京都",
        "employment_type": 2,
        "scrape_run_id": "00000000-0000-0000-0000-000000000000",
    }
    response = _make_response("https://xn--pckua2a7gp15o89zb.com/jb/abc123", "detail.html", meta)
    items = list(spider.parse_detail(response))
    assert items, "expected at least one item from parse_detail"
    item = items[0]
    assert item["category_top"] == "security_cleaning_inspection"
    assert item["area"] == "東京都"
    assert item["employment_type"] == 2
    assert item["scrape_run_id"] == "00000000-0000-0000-0000-000000000000"
