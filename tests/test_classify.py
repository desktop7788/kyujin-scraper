# tests/test_classify.py
import pytest

from helloworks_scraper.classify import (
    classify_category,
    classify_item,
    Verdict,
)


# Post-run-3: 15 カテゴリ分割後、classify_category は category_top をそのまま返すだけ。
# title によるサブ分類は廃止された。fetch 時点で純度が高いため不要。
@pytest.mark.parametrize("category_top,title", [
    ("cleaning",       "ホテル客室清掃スタッフ募集"),
    ("hotel_cleaning", "ホテル客室清掃スタッフ募集"),
    ("security",       "施設警備員(夜勤あり)"),
    ("inspection",     "ビル設備点検スタッフ"),
    ("food",           "ホールスタッフ"),
    ("care",           "訪問看護師"),
    ("welfare",        "障害者支援員"),
    ("factory",        "工場での加工作業"),
    ("manufacturing",  "製造ライン作業員"),
    ("light_work",     "倉庫内ピッキング"),
    ("warehouse",      "倉庫管理スタッフ"),
    ("construction",   "建築現場作業員"),
    ("civil",          "土木作業員"),
    ("delivery",       "宅配ドライバー"),
    ("logistics",      "物流センター管理"),
])
def test_classify_category_returns_top_as_is(category_top, title):
    cat, match = classify_category(category_top, title)
    assert cat == category_top
    assert match is None


def test_classify_item_accept():
    item = {
        "url": "https://example.com/jb/abc",
        "title": "ホテル清掃スタッフ",
        "salary_type": "時給",
        "wage_text": "時給1200円",
        "wage_numbers": 1200,
        "address": "東京都新宿区",
        "category_top": "hotel_cleaning",
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
        "category_top": "hotel_cleaning",
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
        "category_top": "hotel_cleaning",
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
        "category_top": "hotel_cleaning",
    }
    verdict = classify_item(item)
    assert verdict.accepted is False
    assert verdict.reject_reason == "non_hourly"


# hotel_cleaning タイトルフィルタ (旧 clean_kyujinbox + delete_unwanted の合成)
@pytest.mark.parametrize("title,expected_accepted", [
    # accepted: 清掃キーワードを含む
    ("ホテル客室清掃スタッフ募集",  True),
    ("ベッドメイキングスタッフ",    True),
    ("ハウスキーパー大募集",        True),
    ("客室清掃／清掃",              True),
    ("ホテルのリネン回収",          True),  # ホテル + リネン (clean kw)
    ("シーツ交換",                  True),  # ベッド ではないが title に Stage1 keyword 含む？ シーツ単独は Stage1 NG
])
def test_hotel_cleaning_title_filter_accept(title, expected_accepted):
    item = {
        "url": "https://example.com/jb/abc",
        "title": title,
        "salary_type": "時給",
        "wage_text": "時給1200円",
        "wage_numbers": 1200,
        "address": "東京都",
        "category_top": "hotel_cleaning",
    }
    verdict = classify_item(item)
    # シーツ交換は Stage 1 (5キーワード) をパスしないので reject 想定
    if title == "シーツ交換":
        assert verdict.accepted is False
        assert verdict.reject_reason == "off_topic_title"
    else:
        assert verdict.accepted == expected_accepted, f"title={title!r}"


@pytest.mark.parametrize("title", [
    "ホテルの調理師",                # noise: ホテル含むが cleaning kw 無し
    "ホテルフロントスタッフ",         # noise: ホテル + スタッフ but no clean kw
    "特別養護老人ホームの調理師",     # noise: ホーム は ホテル ではない、cleaning kw 無し → Stage1 NG
    "工場での製造ライン作業",         # noise: cleaning と関係なし
    "病院厨房の調理師",               # noise
])
def test_hotel_cleaning_title_filter_reject(title):
    item = {
        "url": "https://example.com/jb/abc",
        "title": title,
        "salary_type": "時給",
        "wage_text": "時給1200円",
        "wage_numbers": 1200,
        "address": "東京都",
        "category_top": "hotel_cleaning",
    }
    verdict = classify_item(item)
    assert verdict.accepted is False
    assert verdict.reject_reason == "off_topic_title"


def test_cleaning_filter_applied():
    # cleaning カテゴリにも hotel_cleaning と同じ 2 段階フィルタを適用。
    # 旧は pagination 浅で noise 触れずトリガー無しで純粋取得できるが、
    # 新の deep pagination 経路では noise (バリスタ/保育士/ピッキング等) 混入のため必須。
    item = {
        "url": "https://example.com/jb/abc",
        "title": "オフィス清掃スタッフ",
        "salary_type": "時給",
        "wage_text": "時給1200円",
        "wage_numbers": 1200,
        "address": "東京都",
        "category_top": "cleaning",
    }
    verdict = classify_item(item)
    assert verdict.accepted is True

    # cleaning カテゴリでも noise (調理師) は reject
    item["title"] = "病院の調理師 未経験応相談"
    verdict = classify_item(item)
    assert verdict.accepted is False
    assert verdict.reject_reason == "off_topic_title"


def test_other_categories_not_filtered():
    # care, food 等は title フィルタ未適用 (旧の対応物が無いため)
    item = {
        "url": "https://example.com/jb/abc",
        "title": "病院の調理師 未経験応相談",
        "salary_type": "時給",
        "wage_text": "時給1200円",
        "wage_numbers": 1200,
        "address": "東京都",
        "category_top": "care",
    }
    verdict = classify_item(item)
    assert verdict.accepted is True
