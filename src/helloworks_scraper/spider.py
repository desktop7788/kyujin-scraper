"""kyujinbox.com を 8 業種 × 47 都道府県 × 2 雇用形態で巡回する Scrapy Spider.

CRITICAL: response.follow() は親 Request の meta を自動伝播しない。
parse / parse_detail で response.follow() を呼ぶ際は常に meta={...} を明示すること。
これを怠ると category_top=None で classify_pipeline が全件 reject する事故になる
(2026-05-12 の Phase 1 dry-run で実際に起きた)。
"""

import time
import urllib.parse

import scrapy
from scrapy.extensions.httpcache import DummyPolicy
from scrapy.utils.httpobj import urlparse_cached

from helloworks_scraper.address import normalize_address
from helloworks_scraper.categories import CATEGORIES, EMPLOYMENT_TYPES, PREFECTURES
from helloworks_scraper.classify import classify_category
from helloworks_scraper.items import KyujinboxV2Item
from helloworks_scraper.salary import parse_salary


META_KEYS = ("category_top", "category_keywords", "area", "employment_type", "scrape_run_id")


def _build_listing_url(keywords: str, area: str, employment_type: int) -> str:
    path = urllib.parse.quote(f"{keywords}の仕事-{area}")
    query = urllib.parse.urlencode({"e": employment_type, "u": 1})
    return f"https://xn--pckua2a7gp15o89zb.com/{path}?{query}"


class KyujinboxV2Spider(scrapy.Spider):
    name = "kyujinbox_v2"
    allowed_domains = ["xn--pckua2a7gp15o89zb.com"]

    def __init__(self, run_id: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.run_id = run_id

    def start_requests(self):
        for category in CATEGORIES:
            for area in PREFECTURES:
                for emp in EMPLOYMENT_TYPES:
                    url = _build_listing_url(category["keywords"], area, emp)
                    meta = {
                        "category_top": category["slug"],
                        "category_keywords": category["keywords"],
                        "area": area,
                        "employment_type": emp,
                        "scrape_run_id": self.run_id,
                    }
                    yield scrapy.Request(url, callback=self.parse, meta=meta, priority=1)

    def parse(self, response):
        meta = {k: response.meta.get(k) for k in META_KEYS}

        for card in response.css("section.p-result_card"):
            detail_url = card.xpath("./h2/a/@href").get()
            company = card.xpath('./p[@class="p-result_company"]/text()').get()
            if not detail_url:
                continue

            parsed = urllib.parse.urlparse(detail_url)
            qs = urllib.parse.parse_qs(parsed.query)
            if "uaid" in qs:
                detail_url = f"https://xn--pckua2a7gp15o89zb.com/jb/{qs['uaid'][0]}"
            elif "?" in detail_url:
                detail_url = detail_url.split("?", 1)[0]

            follow_meta = {**meta, "company": company}
            yield response.follow(detail_url, callback=self.parse_detail, meta=follow_meta)

        next_page = response.xpath('//li[@class="c-pager_btn"]/a/@href').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse, meta=dict(meta))

    def parse_detail(self, response):
        meta = {k: response.meta.get(k) for k in META_KEYS}
        company = response.meta.get("company")

        parsed_url = urllib.parse.urlparse(response.url)
        url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

        title = response.css("p.p-detail_head_title::text").get()
        wage_text_a = response.css("li.p-detail_summary-pay::text").get()
        wage_text_b = response.xpath(
            '//dt[contains(@class,"c-icon--C")]/following-sibling::dd/div/div/p/text()'
        ).get()
        address_block = response.css("dd.p-detail_table_data div div p.p-detail_line::text").getall()
        address_short = response.css("li.p-detail_summary-area::text").get()
        job_type = response.xpath(
            '//dt[contains(text(), "雇用形態")]/following-sibling::dd/div/div/p/text()'
        ).get()
        media_name = response.xpath('//p[contains(text(), "掲載元")]/text()').get()
        if media_name:
            media_name = media_name.replace("掲載元", "").strip()

        salary = parse_salary(wage_text_a)
        wage_text = wage_text_a
        if salary is None:
            salary = parse_salary(wage_text_b)
            wage_text = wage_text_b
        salary_type = salary["salary_type"] if salary else "不明"
        wage_numbers = salary["wage_numbers"] if salary else None

        address_norm = None
        for candidate in [*address_block, address_short]:
            if not candidate:
                continue
            address_norm = normalize_address(candidate.strip())
            if address_norm:
                break

        if address_norm:
            address = address_norm["address"]
            pref = address_norm["pref"]
            city = address_norm["city"]
        else:
            address = address_short.strip() if address_short else None
            pref = None
            city = None

        category, category_match = classify_category(meta["category_top"], title or "")

        item = KyujinboxV2Item()
        item["url"] = url
        item["category_top"] = meta["category_top"]
        item["category_keywords"] = meta["category_keywords"]
        item["area"] = meta["area"]
        item["employment_type"] = meta["employment_type"]
        item["scrape_run_id"] = meta["scrape_run_id"]
        item["category"] = category
        item["category_match"] = category_match
        item["title"] = title
        item["recruiting_company_name"] = company
        item["media_name"] = media_name
        item["job_type"] = job_type
        item["salary_type"] = salary_type
        item["wage_text"] = wage_text
        item["wage_numbers"] = wage_numbers
        item["address"] = address
        item["pref"] = pref
        item["city"] = city
        yield item


class CachePolicy(DummyPolicy):
    def should_cache_request(self, request):
        return urlparse_cached(request).path.startswith("/jb/")

    def should_cache_response(self, response, request):
        return response.status == 200


class BackoffMiddleware:
    def process_response(self, request, response, spider):
        if response.status == 403:
            spider.logger.warning("403 received, sleeping 300s before retry")
            time.sleep(300)
            return request
        return response
