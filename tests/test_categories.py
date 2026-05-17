# tests/test_categories.py
from helloworks_scraper.categories import CATEGORIES, PREFECTURES, EMPLOYMENT_TYPES


EXPECTED_SLUGS = [
    "cleaning",
    "hotel_cleaning",
    "security",
    "inspection",
    "food",
    "care",
    "welfare",
    "factory",
    "manufacturing",
    "light_work",
    "warehouse",
    "construction",
    "civil",
    "delivery",
    "logistics",
]


def test_fifteen_categories():
    assert len(CATEGORIES) == 15
    slugs = [c["slug"] for c in CATEGORIES]
    assert slugs == EXPECTED_SLUGS


def test_each_category_has_keywords_and_label():
    for c in CATEGORIES:
        assert c["keywords"]
        # 全カテゴリが単一キーワード (ハイフン無し)。
        # hotel_cleaning は単一フレーズ "ホテル清掃" (旧スクレイパー互換)。
        assert "-" not in c["keywords"], f"hyphen not allowed in {c['slug']}"
        assert c["label_jp"]


def test_70_areas_tokyo_split():
    # 46 都府県 + 23区 + 東京23区外 = 70 (旧スクレイパーと完コピ)
    assert len(PREFECTURES) == 70
    assert PREFECTURES[0] == "北海道"
    assert PREFECTURES[-1] == "沖縄県"
    # 東京都はそのままでは含まれない (23 区分割済み)
    assert "東京都" not in PREFECTURES
    # 23区が個別に含まれる
    assert "東京都千代田区" in PREFECTURES
    assert "東京都港区" in PREFECTURES
    assert "東京都江戸川区" in PREFECTURES
    # 「東京23区外」 (郊外、市部) も含まれる
    assert "東京23区外" in PREFECTURES
    # 23区の数を実数で確認
    wards = [a for a in PREFECTURES if a.startswith("東京都")]
    assert len(wards) == 23


def test_employment_types():
    assert EMPLOYMENT_TYPES == [2, 5]
