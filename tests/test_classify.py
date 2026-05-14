# tests/test_classify.py
import pytest

from helloworks_scraper.classify import (
    classify_category,
    classify_item,
    SUBCATEGORY_RULES,
    Verdict,
)


@pytest.mark.parametrize("category_top,title,expected_category,expected_match", [
    ("security_cleaning_inspection", "ホテル客室清掃スタッフ募集", "cleaning",  "清掃"),
    ("security_cleaning_inspection", "ハウスキーパー大募集",       "cleaning",  "ハウスキーパー"),
    ("security_cleaning_inspection", "施設警備員(夜勤あり)",       "security",  "警備員"),
    ("security_cleaning_inspection", "交通誘導警備",               "security",  "警備"),
    ("security_cleaning_inspection", "ビル設備点検スタッフ",       "inspection","設備点検"),
    ("care_welfare",                 "介護スタッフ",               "care",      "介護"),
    ("care_welfare",                 "障害者支援員",               "welfare",   "障害者支援"),
    ("food",                         "ホールスタッフ",             "food",      "ホール"),
    ("factory_manufacturing",        "工場での加工作業",           "factory",   "工場"),
    ("factory_manufacturing",        "製造ライン作業員",           "manufacturing","製造"),
    ("light_warehouse",              "倉庫内ピッキング",           "light_work","ピッキング"),
    ("light_warehouse",              "倉庫管理スタッフ",           "warehouse", "倉庫"),
    ("construction_civil",           "建築現場作業員",             "construction","建築"),
    ("construction_civil",           "土木作業員",                 "civil",     "土木"),
    ("delivery_logistics",           "宅配ドライバー",             "delivery",  "宅配"),
    ("delivery_logistics",           "物流センター管理",           "logistics", "物流"),
    ("agriculture_fisheries",        "農作業スタッフ",             "agriculture","農作業"),
    ("agriculture_fisheries",        "林業作業員",                 "forestry",  "林業"),
    ("agriculture_fisheries",        "水産加工",                   "fishery",   "水産"),
])
def test_classify_category(category_top, title, expected_category, expected_match):
    cat, match = classify_category(category_top, title)
    assert cat == expected_category
    assert match == expected_match


def test_classify_unclassified():
    cat, match = classify_category("security_cleaning_inspection", "事務員募集")
    assert cat == "unclassified"
    assert match is None


def test_classify_first_keyword_wins():
    cat, match = classify_category("security_cleaning_inspection", "ホテル警備員")
    assert cat == "cleaning"
    assert match == "ホテル"


def test_classify_item_accept():
    item = {
        "url": "https://example.com/jb/abc",
        "title": "ホテル清掃スタッフ",
        "salary_type": "時給",
        "wage_text": "時給1200円",
        "wage_numbers": 1200,
        "address": "東京都新宿区",
        "category_top": "security_cleaning_inspection",
    }
    verdict = classify_item(item)
    assert verdict.accepted is True
    assert verdict.reject_reason is None


def test_classify_item_rejects_wage_over_5000():
    item = {
        "url": "https://example.com/jb/abc",
        "title": "ホテル清掃",
        "salary_type": "時給",
        "wage_text": "時給6000円",
        "wage_numbers": 6000,
        "address": "東京都",
        "category_top": "security_cleaning_inspection",
    }
    verdict = classify_item(item)
    assert verdict.accepted is False
    assert verdict.reject_reason == "wage_over_5000"


def test_classify_item_rejects_missing_title():
    item = {
        "url": "https://example.com/jb/abc",
        "title": None,
        "salary_type": "時給",
        "wage_text": "時給1200円",
        "wage_numbers": 1200,
        "address": "東京都",
        "category_top": "security_cleaning_inspection",
    }
    verdict = classify_item(item)
    assert verdict.accepted is False
    assert verdict.reject_reason == "missing_title"


def test_classify_item_rejects_missing_category_top():
    item = {
        "url": "https://example.com/jb/abc",
        "title": "ホテル清掃",
        "salary_type": "時給",
        "wage_text": "時給1200円",
        "wage_numbers": 1200,
        "address": "東京都",
        "category_top": None,
    }
    verdict = classify_item(item)
    assert verdict.accepted is False
    assert verdict.reject_reason == "missing_category_top"


def test_classify_item_rejects_non_hourly_salary():
    item = {
        "url": "https://example.com/jb/abc",
        "title": "ホテル清掃",
        "salary_type": "月給",
        "wage_text": "月給25万円",
        "wage_numbers": 250000,
        "address": "東京都",
        "category_top": "security_cleaning_inspection",
    }
    verdict = classify_item(item)
    assert verdict.accepted is False
    assert verdict.reject_reason == "non_hourly"


def test_eight_keys_in_rules():
    assert set(SUBCATEGORY_RULES.keys()) == {
        "security_cleaning_inspection",
        "care_welfare",
        "food",
        "factory_manufacturing",
        "light_warehouse",
        "construction_civil",
        "delivery_logistics",
        "agriculture_fisheries",
    }
