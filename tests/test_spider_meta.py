# tests/test_spider_meta.py
import os
import urllib.parse
import uuid

from scrapy.http import HtmlResponse, Request

from helloworks_scraper.spider import KyujinboxV2Spider, _build_listing_url


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
    # 15 categories × 70 areas × 2 employment types
    assert len(requests) == 15 * 70 * 2
    sample = requests[0]
    assert sample.meta["category_top"]
    assert sample.meta["area"]
    assert sample.meta["employment_type"] in (2, 5)
    assert sample.meta["scrape_run_id"] == run_id


def test_start_requests_filters_to_single_category():
    spider = KyujinboxV2Spider(run_id="r", category="construction")
    requests = list(spider.start_requests())
    # 1 category × 70 areas × 2 employment types
    assert len(requests) == 1 * 70 * 2
    assert all(r.meta["category_top"] == "construction" for r in requests)


def test_start_requests_rejects_unknown_category():
    import pytest as _pytest
    with _pytest.raises(ValueError, match="unknown category slug"):
        KyujinboxV2Spider(run_id="r", category="not_a_real_slug")


def test_start_requests_filters_to_single_employment_type():
    spider = KyujinboxV2Spider(run_id="r", category="cleaning", employment_type=2)
    requests = list(spider.start_requests())
    # 1 category × 70 areas × 1 emp = 70
    assert len(requests) == 70
    assert all(r.meta["employment_type"] == 2 for r in requests)


def test_start_requests_rejects_unknown_employment_type():
    import pytest as _pytest
    with _pytest.raises(ValueError, match="unknown employment_type"):
        KyujinboxV2Spider(run_id="r", employment_type=99)


def test_parse_propagates_meta_to_detail_requests():
    spider = KyujinboxV2Spider(run_id="00000000-0000-0000-0000-000000000000")
    meta = {
        "category_top": "cleaning",
        "category_keywords": "清掃",
        "area": "東京都",
        "employment_type": 2,
        "scrape_run_id": "00000000-0000-0000-0000-000000000000",
    }
    response = _make_response("https://xn--pckua2a7gp15o89zb.com/清掃の仕事-東京都?e=2&u=1", "listing.html", meta)

    detail_requests = [r for r in spider.parse(response) if r.callback == spider.parse_detail]
    assert detail_requests, "expected at least one detail follow"
    for r in detail_requests:
        for key in ("category_top", "category_keywords", "area", "employment_type", "scrape_run_id"):
            assert r.meta.get(key) == meta[key], f"meta key '{key}' lost on response.follow"


def test_parse_propagates_meta_to_next_page():
    spider = KyujinboxV2Spider(run_id="00000000-0000-0000-0000-000000000000")
    meta = {
        "category_top": "cleaning",
        "category_keywords": "清掃",
        "area": "東京都",
        "employment_type": 2,
        "scrape_run_id": "00000000-0000-0000-0000-000000000000",
    }
    response = _make_response("https://xn--pckua2a7gp15o89zb.com/清掃の仕事-東京都?e=2&u=1", "listing.html", meta)
    next_page_requests = [r for r in spider.parse(response) if r.callback == spider.parse]
    if not next_page_requests:
        # Some fixtures may not have a next page; skip
        return
    for r in next_page_requests:
        for key in ("category_top", "category_keywords", "area", "employment_type", "scrape_run_id"):
            assert r.meta.get(key) == meta[key]


def _u_param(url: str) -> str:
    return urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["u"][0]


def test_hotel_cleaning_uses_updated_at_3():
    spider = KyujinboxV2Spider(run_id="r", category="hotel_cleaning")
    urls = [r.url for r in spider.start_requests()]
    assert urls, "expected start requests"
    assert all(_u_param(u) == "3" for u in urls), (
        "hotel_cleaning slot must use u=3 to match old SetagayaLab main daily haul"
    )


def test_non_hotel_cleaning_uses_updated_at_1():
    spider = KyujinboxV2Spider(run_id="r", category="cleaning")
    urls = [r.url for r in spider.start_requests()]
    assert urls
    assert all(_u_param(u) == "1" for u in urls)


def test_build_listing_url_default_updated_at_is_1():
    url = _build_listing_url("清掃", "東京都港区", 2)
    assert _u_param(url) == "1"


def test_build_listing_url_accepts_explicit_updated_at():
    url = _build_listing_url("ホテル清掃", "東京都港区", 2, updated_at=3)
    assert _u_param(url) == "3"


def test_parse_detail_emits_item_with_meta():
    spider = KyujinboxV2Spider(run_id="00000000-0000-0000-0000-000000000000")
    meta = {
        "category_top": "cleaning",
        "category_keywords": "清掃",
        "area": "東京都",
        "employment_type": 2,
        "scrape_run_id": "00000000-0000-0000-0000-000000000000",
    }
    response = _make_response("https://xn--pckua2a7gp15o89zb.com/jb/abc123", "detail.html", meta)
    items = list(spider.parse_detail(response))
    assert items, "expected at least one item from parse_detail"
    item = items[0]
    assert item["category_top"] == "cleaning"
    assert item["area"] == "東京都"
    assert item["employment_type"] == 2
    assert item["scrape_run_id"] == "00000000-0000-0000-0000-000000000000"
