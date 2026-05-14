"""8 業種 × 47 都道府県 × 雇用形態 2 種 = 752 検索の定数定義。

Post-run-1 改訂 (2026-05-14):
  - 農林水産を削除: 取得量 7 件で構造的に少ない (kyujinbox がアルバイト・派遣の農林水産系を
    ほぼ持っていない)。
  - ホテル清掃 (hotel_cleaning) を追加: 警備-清掃-点検 bundle では清掃データが 32 件と
    旧スクレイパー (ホテル清掃キーワード 416 件/日) と比べて極端に少なかった。旧と同じ
    単発キーワード検索を専用カテゴリとして併走させる。
"""

CATEGORIES: list[dict] = [
    {"slug": "security_cleaning_inspection", "keywords": "警備-清掃-点検", "label_jp": "警備・清掃・点検"},
    {"slug": "hotel_cleaning",               "keywords": "ホテル-清掃",   "label_jp": "ホテル清掃"},
    {"slug": "care_welfare",                 "keywords": "介護-福祉",     "label_jp": "介護・福祉"},
    {"slug": "food",                         "keywords": "飲食",         "label_jp": "飲食"},
    {"slug": "factory_manufacturing",        "keywords": "工場-製造",     "label_jp": "工場・製造"},
    {"slug": "light_warehouse",              "keywords": "軽作業-倉庫",   "label_jp": "軽作業・倉庫"},
    {"slug": "construction_civil",           "keywords": "建築-土木",     "label_jp": "建築・土木"},
    {"slug": "delivery_logistics",           "keywords": "配送-物流",     "label_jp": "配送・物流"},
]

PREFECTURES: list[str] = [
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県",
    "岐阜県", "静岡県", "愛知県", "三重県",
    "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県",
    "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県",
    "福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県",
    "沖縄県",
]

# e=2: アルバイト・パート / e=5: 派遣社員
EMPLOYMENT_TYPES: list[int] = [2, 5]
