"""業種分類とアイテム品質判定。

category は category_top から切り出した単一業種で、title のキーワードマッチで判定する。
classify_item は Verdict を返す authoritative なデータ品質フィルタ。
"""

from dataclasses import dataclass


# {category_top: [(sub_category, [keywords]), ...]} — 順序が優先順位（先勝ち）
# Post-run-1 改訂 (2026-05-14):
#   - agriculture_fisheries ルール削除（categories.py で対象外に）
#   - hotel_cleaning ルール追加
#   - care/welfare/food のキーワード辞書を unclassified サンプルから拡張
SUBCATEGORY_RULES: dict[str, list[tuple[str, list[str]]]] = {
    "security_cleaning_inspection": [
        ("cleaning",    ["清掃", "ホテル", "ハウスキーパー", "ベッドメイキング", "客室"]),
        ("security",    ["警備員", "警備", "巡回", "交通誘導"]),
        ("inspection",  ["設備点検", "点検", "検査員"]),
    ],
    # 旧スクレイパーと同じ「ホテル清掃」単発検索の専用カテゴリ。
    # 警備-清掃-点検 bundle で 32 件しか取れなかった清掃データを補完する。
    "hotel_cleaning": [
        ("cleaning",    ["清掃", "ホテル", "ハウスキーパー", "ベッドメイキング", "客室"]),
    ],
    "care_welfare": [
        ("care",        ["訪問介護", "訪問看護", "訪問入浴", "看護師", "看護", "介護", "ヘルパー", "デイサービス"]),
        ("welfare",     ["障害者支援", "保育士", "保育園", "生活支援", "福祉"]),
    ],
    "food": [
        ("food",        ["仕込み", "開店準備", "惣菜", "配膳", "飲食", "ホール", "キッチン", "調理", "厨房", "接客"]),
    ],
    "factory_manufacturing": [
        ("factory",         ["工場"]),
        ("manufacturing",   ["製造", "組立", "加工", "ライン"]),
    ],
    "light_warehouse": [
        ("light_work",  ["軽作業", "ピッキング", "仕分け", "梱包"]),
        ("warehouse",   ["倉庫"]),
    ],
    "construction_civil": [
        ("construction",["建築", "建設", "大工", "施工"]),
        ("civil",       ["土木", "舗装"]),
    ],
    "delivery_logistics": [
        ("delivery",    ["配送", "宅配", "デリバリー", "ドライバー"]),
        ("logistics",   ["物流"]),
    ],
}


def classify_category(category_top: str, title: str) -> tuple[str, str | None]:
    """title のキーワードマッチで category_top の sub-category を 1 つ返す。

    Returns:
        (category, matched_keyword). マッチなしは ('unclassified', None).
    """
    if not title or category_top not in SUBCATEGORY_RULES:
        return "unclassified", None
    for sub_category, keywords in SUBCATEGORY_RULES[category_top]:
        for kw in keywords:
            if kw in title:
                return sub_category, kw
    return "unclassified", None


@dataclass
class Verdict:
    accepted: bool
    reject_reason: str | None = None


def classify_item(item: dict) -> Verdict:
    """Authoritative data quality filter. Phase 1: 時給データのみ蓄積。

    Reject reasons:
      - missing_category_top
      - missing_title
      - missing_wage_numbers
      - missing_address
      - non_hourly
      - wage_over_5000
    """
    if not item.get("category_top"):
        return Verdict(False, "missing_category_top")
    if not item.get("title"):
        return Verdict(False, "missing_title")
    if item.get("wage_numbers") is None:
        return Verdict(False, "missing_wage_numbers")
    if not item.get("address"):
        return Verdict(False, "missing_address")
    if item.get("salary_type") != "時給":
        return Verdict(False, "non_hourly")
    if item["wage_numbers"] > 5000:
        return Verdict(False, "wage_over_5000")
    return Verdict(True, None)
