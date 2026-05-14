"""Scrapy Item for kyujinbox_v2 rows."""

import scrapy


class KyujinboxV2Item(scrapy.Item):
    url = scrapy.Field()

    category_top = scrapy.Field()
    category_keywords = scrapy.Field()
    area = scrapy.Field()
    employment_type = scrapy.Field()

    category = scrapy.Field()
    category_match = scrapy.Field()

    title = scrapy.Field()
    recruiting_company_name = scrapy.Field()
    media_name = scrapy.Field()
    job_type = scrapy.Field()
    salary_type = scrapy.Field()
    wage_text = scrapy.Field()
    wage_numbers = scrapy.Field()

    address = scrapy.Field()
    pref = scrapy.Field()
    city = scrapy.Field()
    pref_code = scrapy.Field()
    city_code_5 = scrapy.Field()

    scrape_run_id = scrapy.Field()
