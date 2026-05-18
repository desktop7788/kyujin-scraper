"""業種分類とアイテム品質判定。

Post-run-3 改訂 (2026-05-16):
  - 15 カテゴリ単一キーワード分割で fetch 時点の純度は高くなったが、
    kyujinbox は「ホテル清掃」フレーズ検索でも「ホテルの調理師」等を
    related/templated として埋め込んで返してくる仕様。
  - 旧スクレイパー (SetagayaLab) はこの noise を DB の 2段階フィルタで除去していた:
      Stage 1: clean_kyujinbox トリガー BEFORE INSERT
        title に {ホテル, 清掃, ハウスキーパー, ベッドメイキング, 客室} のいずれも
        含まない行は破棄。
      Stage 2: delete_unwanted_kyujinbox_records (upload 後に rpc 呼び出し)
        title が 25 個の cleaning キーワードを含まず、かつ title に
        「ホテル」または「スタッフ」を含む行を DELETE。
  - 新では classify_item に組み込んで 1 pass で同じ効果を実現。
  - hotel_cleaning カテゴリのみ適用 (他カテゴリは旧の対応物がないため別途検証)。
"""

from dataclasses import dataclass


# 旧 clean_kyujinbox トリガーの 5 キーワード (これがないと INSERT 破棄)
_HOTEL_CLEANING_STAGE1_KEYWORDS = (
    "ホテル", "清掃", "ハウスキーパー", "ベッドメイキング", "客室",
)

# 旧 delete_unwanted_kyujinbox_records の 25 キーワード (これがないと DELETE)
_HOTEL_CLEANING_STAGE2_KEYWORDS = (
    "清掃", "客室", "ベッドメイク", "ベッドメイキング", "ベットメイキング",
    "ハウスキーピング", "ハウスキーパー", "ホテルクリーニング", "ルームクリーニング",
    "クリーンスタッフ", "クリーニング", "シーツ", "ベッド", "美装", "掃除",
    "クリーン", "宿泊", "ラブホテル", "そうじ", "リネン", "ルーム",
    "チェッカー", "共用", "営繕", "メイク",
)


def classify_category(category_top: str, title: str) -> tuple[str, str | None]:
    """category_top をそのまま category として返す (15 カテゴリ分割後はサブ分類不要)。"""
    return category_top, None


def _hotel_cleaning_title_passes(title: str) -> bool:
    """旧 clean_kyujinbox トリガー + delete_unwanted の合成判定。

    Stage 1: 5 キーワードのいずれかを含む必要あり。
    Stage 2: 25 キーワードを含まず、かつ ホテル or スタッフ を含む場合は破棄。
    """
    if not title:
        return False
    # Stage 1
    if not any(kw in title for kw in _HOTEL_CLEANING_STAGE1_KEYWORDS):
        return False
    # Stage 2: drop if NOT(cleaning kw) AND (has ホテル OR スタッフ)
    has_cleaning_kw = any(kw in title for kw in _HOTEL_CLEANING_STAGE2_KEYWORDS)
    has_hotel_or_staff = ("ホテル" in title) or ("スタッフ" in title)
    if has_hotel_or_staff and not has_cleaning_kw:
        return False
    return True


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
      - off_topic_title (category 固有のタイトルキーワード不一致)
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

    # カテゴリ固有のタイトル絞り込み
    # cleaning / hotel_cleaning とも、kyujinbox の deep pagination が
    # 「バリスタ」「保育士」「ピッキング」等の related/templated ad を混ぜて返す
    # (5/18 検証で新の deep pagination 結果 2,736 件中 86.6% が cleaning kw なしと確認)。
    # 旧スクレイパーは pagination が浅く noise に触れないため、現状トリガー無しで
    # 100% 純粋な cleaning を取れているが、新の deep pagination 経路では本フィルタが
    # noise 除去のために必須。
    if item["category_top"] in ("hotel_cleaning", "cleaning"):
        if not _hotel_cleaning_title_passes(item["title"]):
            return Verdict(False, "off_topic_title")

    return Verdict(True, None)
