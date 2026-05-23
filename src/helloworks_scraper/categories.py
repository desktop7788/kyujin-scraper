"""15 業種 × 70 areas × 雇用形態 2 種 = 2,100 検索の定数定義。

Post-run-3 改訂 (2026-05-16):
  - 8 カテゴリ → 15 カテゴリ (単一キーワード分割) で kyujinbox OR検索 noise を回避
  - PREFECTURES → 70 areas に拡張: 東京都を 23区+東京23区外 に分割
    (旧スクレイパー実測値と完コピ。23区を都道府県単位で検索すると、
     港区/新宿区/渋谷区等の都心ホテルが「東京都」検索の後段ページに埋もれて
     取得漏れする現象を回避)

2026-05-23 改訂:
  - hotel_cleaning のみ updated_at=3 を指定。旧 SetagayaLab main (Windows 02:30 daily,
    旧 Supabase kyujinbox 書き込み) の本番設定が u=3 で約 1,398 件/日を取得していた
    のに対し、新 u=1 では 382 件/日と約 3.66 倍の差。kyujinbox の URL hash は日次
    ローテーションするため u=3 は同一求人を 3 日分の異なる URL で取得する仕様で、
    旧との件数・URL マッチ率を揃えるためにこの値が必要。
  - 他のカテゴリは updated_at 未指定 (= デフォルト 1)。
"""

# updated_at: kyujinbox URL の `u` パラメータ。1=過去1日, 3=過去3日。
# 未指定なら spider 側でデフォルト 1。
CATEGORIES: list[dict] = [
    {"slug": "cleaning",       "keywords": "清掃",       "label_jp": "清掃"},
    {"slug": "hotel_cleaning", "keywords": "ホテル清掃", "label_jp": "ホテル清掃", "updated_at": 3},
    {"slug": "security",       "keywords": "警備",       "label_jp": "警備"},
    {"slug": "inspection",     "keywords": "点検",       "label_jp": "点検"},
    {"slug": "food",           "keywords": "飲食",       "label_jp": "飲食"},
    {"slug": "care",           "keywords": "介護",       "label_jp": "介護"},
    {"slug": "welfare",        "keywords": "福祉",       "label_jp": "福祉"},
    {"slug": "factory",        "keywords": "工場",       "label_jp": "工場"},
    {"slug": "manufacturing",  "keywords": "製造",       "label_jp": "製造"},
    {"slug": "light_work",     "keywords": "軽作業",     "label_jp": "軽作業"},
    {"slug": "warehouse",      "keywords": "倉庫",       "label_jp": "倉庫"},
    {"slug": "construction",   "keywords": "建築",       "label_jp": "建築"},
    {"slug": "civil",          "keywords": "土木",       "label_jp": "土木"},
    {"slug": "delivery",       "keywords": "配送",       "label_jp": "配送"},
    {"slug": "logistics",      "keywords": "物流",       "label_jp": "物流"},
]

# 70 areas: 46 都府県 + 東京23区 + 東京23区外
# 旧スクレイパー (SetagayaLab Windows) と完全一致。順序は地理的 (北→南、Tokyo は administrative)。
PREFECTURES: list[str] = [
    "北海道",
    "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県",
    # 東京都 を 23区 + 東京23区外 に分割 (administrative order)
    "東京都千代田区", "東京都中央区", "東京都港区", "東京都新宿区", "東京都文京区",
    "東京都台東区", "東京都墨田区", "東京都江東区", "東京都品川区", "東京都目黒区",
    "東京都大田区", "東京都世田谷区", "東京都渋谷区", "東京都中野区", "東京都杉並区",
    "東京都豊島区", "東京都北区", "東京都荒川区", "東京都板橋区", "東京都練馬区",
    "東京都足立区", "東京都葛飾区", "東京都江戸川区",
    "東京23区外",
    "神奈川県",
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
