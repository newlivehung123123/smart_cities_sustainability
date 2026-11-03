"""Write japan_mlit_model.csv (2019 selection) and add the shared columns to ascn.csv.

Shared schema for every designation list:
economy, place_as_printed, place_en, area_as_printed, area_scope, project_id, programme,
programme_model, announcement_date, date_precision, first_treated_year, batch, source, note

area_scope: whole = the whole place named; part = an area inside it (flagged later);
wider = an area that reaches beyond the place named.
"""
import csv, sys
from pathlib import Path

D = Path(sys.argv[1])
COLS = ["economy", "place_as_printed", "place_en", "area_as_printed", "area_scope",
        "project_id", "programme", "programme_model", "announcement_date", "date_precision",
        "first_treated_year", "batch", "source", "note"]

# ---- ASCN: add the new columns, keep every value as it was ----
rows = list(csv.DictReader(open(D / "ascn.csv", encoding="utf-8")))
assert len(rows) == 38
for i, r in enumerate(rows, 1):
    r["place_en"] = r["place_as_printed"]
    r["area_as_printed"] = ""
    r["area_scope"] = "whole"
    r["project_id"] = f"ASCN-{i:02d}"
with open(D / "ascn.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, COLS)
    w.writeheader()
    w.writerows(rows)

# ---- MLIT 2019 ----
# (pref+municipality as printed, English, area as printed, scope, project number, note)
LEAD = [
    ("北海道札幌市", "Sapporo, Hokkaido", "市中心部および郊外", "part", 1, ""),
    ("秋田県仙北市", "Semboku, Akita", "全域", "whole", 2, ""),
    ("茨城県つくば市", "Tsukuba, Ibaraki", "全域", "whole", 3, "lead public partner is Ibaraki Prefecture; Tsukuba City is a member"),
    ("栃木県宇都宮市", "Utsunomiya, Tochigi", "全域", "whole", 4, ""),
    ("埼玉県毛呂山町", "Moroyama, Saitama", "全域", "whole", 5, ""),
    ("千葉県柏市", "Kashiwa, Chiba", "柏の葉キャンパス駅周辺", "part", 6, ""),
    ("東京都千代田区", "Chiyoda, Tokyo", "大手町・丸の内・有楽町エリア", "part", 7, ""),
    ("東京都江東区", "Koto, Tokyo", "豊洲エリア", "part", 8, ""),
    ("静岡県熱海市", "Atami, Shizuoka", "熱海市市街地、下田市市街地", "part", 9, "one project in two municipalities (VIRTUAL SHIZUOKA); lead public partner is Shizuoka Prefecture"),
    ("静岡県下田市", "Shimoda, Shizuoka", "熱海市市街地、下田市市街地", "part", 9, "one project in two municipalities (VIRTUAL SHIZUOKA); lead public partner is Shizuoka Prefecture"),
    ("静岡県藤枝市", "Fujieda, Shizuoka", "全域", "whole", 10, ""),
    ("愛知県春日井市", "Kasugai, Aichi", "高蔵寺ニュータウン", "part", 11, ""),
    ("京都府精華町", "Seika, Kyoto", "けいはんな学研都市（精華・西木津地区）", "part", 12, "one project in two municipalities; lead public partner is Kyoto Prefecture"),
    ("京都府木津川市", "Kizugawa, Kyoto", "けいはんな学研都市（精華・西木津地区）", "part", 12, "one project in two municipalities; lead public partner is Kyoto Prefecture"),
    ("島根県益田市", "Masuda, Shimane", "全域", "whole", 13, ""),
    ("広島県三次市", "Miyoshi, Hiroshima", "川西地区", "part", 14, "lead public partner is Hiroshima Prefecture"),
    ("愛媛県松山市", "Matsuyama, Ehime", "中心市街地西部", "part", 15, ""),
]
PRIORITY = [
    ("宮城県仙台市", "Sendai, Miyagi", "泉パークタウン", "part", 1, ""),
    ("茨城県守谷市", "Moriya, Ibaraki", "全域", "whole", 2, ""),
    ("群馬県前橋市", "Maebashi, Gunma", "全域", "whole", 3, ""),
    ("埼玉県さいたま市", "Saitama, Saitama", "美園地区、大宮駅周辺地区", "part", 4, ""),
    ("東京都大田区", "Ota, Tokyo", "羽田空港跡地第1ゾーン(第一期事業)", "part", 5, ""),
    ("神奈川県横浜市", "Yokohama, Kanagawa", "みなとみらい21地区", "part", 6, ""),
    ("神奈川県川崎市", "Kawasaki, Kanagawa", "新百合ヶ丘駅周辺地区", "part", 7, ""),
    ("神奈川県横須賀市", "Yokosuka, Kanagawa", "全域", "whole", 8, ""),
    ("新潟県新潟市", "Niigata, Niigata", "全域", "whole", 9, ""),
    ("福井県永平寺町", "Eiheiji, Fukui", "全域", "whole", 10, ""),
    ("岐阜県岐阜市", "Gifu, Gifu", "全域", "whole", 11, ""),
    ("愛知県岡崎市", "Okazaki, Aichi", "乙川リバーフロントエリア", "part", 12, ""),
    ("大阪府大阪市", "Osaka, Osaka", "うめきた2期地区、夢洲地区", "part", 13, ""),
    ("兵庫県加古川市", "Kakogawa, Hyogo", "全域", "whole", 14, ""),
    ("岡山県倉敷市", "Kurashiki, Okayama", "中心市街地", "part", 15, ""),
    ("広島県呉市", "Kure, Hiroshima", "全域", "whole", 16, ""),
    ("広島県福山市", "Fukuyama, Hiroshima", "全域", "whole", 17, ""),
    ("徳島県美波町", "Minami, Tokushima", "全域", "whole", 18, ""),
    ("香川県高松市", "Takamatsu, Kagawa", "全域", "whole", 19, ""),
    ("愛媛県新居浜市", "Niihama, Ehime", "全域", "whole", 20, ""),
    ("福岡県福岡市", "Fukuoka, Fukuoka", "九州大学箱崎キャンパス跡地及び周辺地域", "part", 21, ""),
    ("長崎県島原市", "Shimabara, Nagasaki", "島原半島", "wider", 22, "public partners are Shimabara City and Nagasaki Prefecture; the peninsula also covers Unzen and Minamishimabara, which are not named, so only Shimabara is coded"),
    ("熊本県荒尾市", "Arao, Kumamoto", "南新地地区", "part", 23, ""),
]
assert len({p[4] for p in LEAD}) == 15 and len(PRIORITY) == 23

out = []
for batch, tag, items, page in [("leading 2019", "L", LEAD, "annex 1 (別紙1), pp. 2-3"),
                                ("priority 2019", "P", PRIORITY, "annex 2 (別紙2), pp. 4-7")]:
    for place, en, area, scope, n, note in items:
        out.append({
            "economy": "Japan", "place_as_printed": place, "place_en": en,
            "area_as_printed": area, "area_scope": scope,
            "project_id": f"MLIT2019-{tag}{n:02d}",
            "programme": "MLIT Smart City Model Projects",
            "programme_model": "implementation support",
            "announcement_date": "2019-05-31", "date_precision": "day",
            "first_treated_year": "2019", "batch": batch,
            "source": f"[1] MLIT press release 31 May 2019, {page}",
            "note": note,
        })
with open(D / "japan_mlit_model.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, COLS)
    w.writeheader()
    w.writerows(out)
print(len(out), "MLIT rows;", sum(r["area_scope"] == "part" for r in out), "part;",
      sum(r["area_scope"] == "whole" for r in out), "whole;",
      sum(r["area_scope"] == "wider" for r in out), "wider")
