# tests/test_categories.py
from helloworks_scraper.categories import CATEGORIES, PREFECTURES, EMPLOYMENT_TYPES


def test_eight_categories():
    assert len(CATEGORIES) == 8
    slugs = [c["slug"] for c in CATEGORIES]
    assert slugs == [
        "security_cleaning_inspection",
        "hotel_cleaning",
        "care_welfare",
        "food",
        "factory_manufacturing",
        "light_warehouse",
        "construction_civil",
        "delivery_logistics",
    ]


def test_each_category_has_keywords_and_label():
    for c in CATEGORIES:
        assert c["keywords"]
        # food は単一キーワード、他はすべて bundle (- 区切り)
        assert "-" in c["keywords"] or c["slug"] == "food"
        assert c["label_jp"]


def test_47_prefectures():
    assert len(PREFECTURES) == 47
    assert PREFECTURES[0] == "北海道"
    assert PREFECTURES[-1] == "沖縄県"
    assert "東京都" in PREFECTURES


def test_employment_types():
    assert EMPLOYMENT_TYPES == [2, 5]
