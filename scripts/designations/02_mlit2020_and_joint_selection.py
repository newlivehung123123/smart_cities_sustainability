"""Append the July 2020 MLIT rows to japan_mlit_model.csv and write japan_joint_selection.csv
(Cabinet Office joint selection of five smart city programmes, 2021 to 2025) from annex 2 (別紙2).

argv[1] = designations directory, argv[2] = data/raw/designations/sources.
area_scope adds two values for this list: prefecture (only prefectures are named) and
unnamed (an area across several municipalities, none named).
"""
import csv, re, sys, unicodedata
from collections import Counter
from pathlib import Path
import pypdf

D, C = Path(sys.argv[1]), Path(sys.argv[2])
COLS = ["economy", "place_as_printed", "place_en", "area_as_printed", "area_scope",
        "project_id", "programme", "programme_model", "announcement_date", "date_precision",
        "first_treated_year", "batch", "source", "note"]

# ---- MLIT 2020 (press release 31 July 2020) ----
L20 = [("埼玉県さいたま市", "Saitama, Saitama", "大宮駅・さいたま新都心周辺地区", "part"),
       ("東京都大田区", "Ota, Tokyo", "羽田空港跡地第1ゾーン(羽田イノベーションシティ)", "part"),
       ("新潟県新潟市", "Niigata, Niigata", "中心市街地(新潟駅周辺地区、万代地区、古町地区)", "part"),
       ("愛知県岡崎市", "Okazaki, Aichi", "乙川リバーフロントQURUWA地区", "part"),
       ("大阪府大阪市", "Osaka, Osaka", "うめきた2期地区、夢洲地区", "part"),
       ("兵庫県加古川市", "Kakogawa, Hyogo", "全域", "whole"),
       ("熊本県荒尾市", "Arao, Kumamoto", "南新地地区", "part")]
P20 = [("福島県南相馬市", "Minamisoma, Fukushima"), ("茨城県水戸市", "Mito, Ibaraki"),
       ("埼玉県熊谷市", "Kumagaya, Saitama"), ("東京都東村山市", "Higashimurayama, Tokyo"),
       ("石川県加賀市", "Kaga, Ishikawa")]
mlit = list(csv.DictReader(open(D / "japan_mlit_model.csv", encoding="utf-8")))
mlit = [r for r in mlit if r["announcement_date"] != "2020-07-31"]
assert len(mlit) == 40
base = {"economy": "Japan", "programme": "MLIT Smart City Model Projects",
        "programme_model": "implementation support", "announcement_date": "2020-07-31",
        "date_precision": "day", "first_treated_year": "2021"}
for n, (p, en, a, s) in enumerate(L20, 1):
    mlit.append({**base, "place_as_printed": p, "place_en": en, "area_as_printed": a,
                 "area_scope": s, "project_id": f"MLIT2020-L{n:02d}", "batch": "leading 2020",
                 "source": "[2] MLIT press release 31 July 2020, annex 1 (別紙1)",
                 "note": "priority project in 2019, moved up to leading in 2020"})
for n, (p, en) in enumerate(P20, 1):
    mlit.append({**base, "place_as_printed": p, "place_en": en, "area_as_printed": "全域",
                 "area_scope": "whole", "project_id": f"MLIT2020-P{n:02d}",
                 "batch": "priority 2020",
                 "source": "[2] MLIT press release 31 July 2020, annex 2 (別紙2)",
                 "note": "lead public partners are Saitama Prefecture and Kumagaya City" if "熊谷" in p else ""})
with open(D / "japan_mlit_model.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, COLS); w.writeheader(); w.writerows(mlit)

# ---- Joint selection 2021 to 2025 ----
PREF = {"北海道": "Hokkaido", "岩手県": "Iwate", "宮城県": "Miyagi", "秋田県": "Akita", "青森県": "Aomori",
        "福島県": "Fukushima", "茨城県": "Ibaraki", "栃木県": "Tochigi", "群馬県": "Gunma",
        "埼玉県": "Saitama", "千葉県": "Chiba", "東京都": "Tokyo", "神奈川県": "Kanagawa",
        "新潟県": "Niigata", "富山県": "Toyama", "石川県": "Ishikawa", "福井県": "Fukui",
        "長野県": "Nagano", "岐阜県": "Gifu", "静岡県": "Shizuoka", "愛知県": "Aichi", "三重県": "Mie",
        "京都府": "Kyoto", "大阪府": "Osaka", "兵庫県": "Hyogo", "奈良県": "Nara",
        "和歌山県": "Wakayama", "鳥取県": "Tottori", "島根県": "Shimane", "岡山県": "Okayama",
        "広島県": "Hiroshima", "山口県": "Yamaguchi", "香川県": "Kagawa", "愛媛県": "Ehime",
        "福岡県": "Fukuoka", "佐賀県": "Saga", "長崎県": "Nagasaki", "熊本県": "Kumamoto",
        "大分県": "Oita", "宮崎県": "Miyazaki", "鹿児島県": "Kagoshima", "沖縄県": "Okinawa",
        "滋賀県": "Shiga"}
MUNI = dict(x.split(":") for x in """札幌市:Sapporo 旭川市:Asahikawa 室蘭市:Muroran 帯広市:Obihiro
芽室町:Memuro 更別村:Sarabetsu 陸前高田市:Rikuzentakata 仙台市:Sendai 仙北市:Semboku
会津若松市:Aizuwakamatsu 南相馬市:Minamisoma つくば市:Tsukuba 守谷市:Moriya 佐野市:Sano
前橋市:Maebashi 嬬恋村:Tsumagoi さいたま市:Saitama 熊谷市:Kumagaya 入間市:Iruma 毛呂山町:Moroyama
柏市:Kashiwa 千代田区:Chiyoda 港区:Minato 大田区:Ota 横須賀市:Yokosuka 川崎市:Kawasaki
箱根町:Hakone 三浦市:Miura 新潟市:Niigata 朝日町:Asahi 加賀市:Kaga 中能登町:Nakanoto
永平寺町:Eiheiji 中津川市:Nakatsugawa 静岡市:Shizuoka 岡崎市:Okazaki 春日井市:Kasugai
多気町:Taki 明和町:Meiwa 大台町:Odai 度会町:Watarai 大紀町:Taiki 紀北町:Kihoku 与謝野町:Yosano
大阪市:Osaka 河内長野市:Kawachinagano 豊能町:Toyono 加古川市:Kakogawa 太地町:Taiji
すさみ町:Susami 美郷町:Misato 三次市:Miyoshi 三豊市:Mitoyo 松山市:Matsuyama 新居浜市:Niihama
嬉野市:Ureshino 基山町:Kiyama 人吉市:Hitoyoshi 荒尾市:Arao 延岡市:Nobeoka 宮古島市:Miyakojima
北谷町:Chatan 江差町:Esashi 盛岡市:Morioka 浪江町:Namie 常陸太田市:Hitachiota 逗子市:Zushi
葉山町:Hayama 鎌倉市:Kamakura 小田原市:Odawara 塩尻市:Shiojiri 岐阜市:Gifu 名古屋市:Nagoya
いなべ市:Inabe 菰野町:Komono 高砂市:Takasago 宇陀市:Uda 川西町:Kawanishi かつらぎ町:Katsuragi
大山町:Daisen 伯耆町:Hoki 米子市:Yonago 山口市:Yamaguchi 東温市:Toon 今治市:Imabari 伊予市:Iyo
福岡市:Fukuoka 伊仙町:Isen 恩納村:Onna 須賀川市:Sukagawa 館山市:Tateyama 南房総市:Minamiboso
渋谷区:Shibuya 横浜市:Yokohama 焼津市:Yaizu 四日市市:Yokkaichi 橋本市:Hashimoto 有田市:Arida
吉備中央町:Kibichuo 石垣市:Ishigaki 竹富町:Taketomi 南城市:Nanjo 江東区:Koto 渋川市:Shibukawa
笠間市:Kasama 茅野市:Chino 一宮市:Ichinomiya 豊中市:Toyonaka 堺市:Sakai 大田市:Oda
川本町:Kawamoto 津山市:Tsuyama 東広島市:Higashihiroshima 高松市:Takamatsu 久米島町:Kumejima
名寄市:Nayoro 稚内市:Wakkanai 美唄市:Bibai 小清水町:Koshimizu 斜里町:Shari 弘前市:Hirosaki
高崎市:Takasaki みなかみ町:Minakami 越谷市:Koshigaya 東庄町:Tonosho 墨田区:Sumida 富山市:Toyama
飯山市:Iiyama 東大阪市:Higashiosaka 多度津町:Tadotsu 小豆島町:Shodoshima 四国中央市:Shikokuchuo
精華町:Seika 木津川市:Kizugawa 渡会町:Watarai""".split())
PREF_RE = re.compile(r"^(北海道|東京都|京都府|大阪府|[^、・()]{2,3}?県)")

KANSAI = "Kansai and Chubu prefectures (Osaka, Kyoto, Hyogo, Nara, Shiga, Mie, Wakayama and part of Aichi)"
OVR = {  # printed place -> [(pref+municipality, area, scope, note)]
    "仙台市泉区南光台・八乙女地区": [("宮城県仙台市", "泉区南光台・八乙女地区", "part", "")],
    "埼玉県入間市 宮寺・二本木、東金子、金子、藤沢第一・第二 エリア":
        [("埼玉県入間市", "宮寺・二本木、東金子、金子、藤沢第一・第二 エリア", "part", "")],
    "山手線周辺/横須賀市": [("東京都", "山手線周辺", "unnamed", "area along the JR Yamanote line; wards not named"),
                       ("神奈川県横須賀市", "", "whole", "")],
    "川崎市、箱根町": [("神奈川県川崎市", "", "whole", "prefecture not printed"),
                 ("神奈川県箱根町", "", "whole", "prefecture not printed")],
    "京都府精華町、木津川市(けいはんな学研都市(精華地区・西木津地区))":
        [("京都府精華町", "けいはんな学研都市(精華地区・西木津地区)", "part", ""),
         ("京都府木津川市", "けいはんな学研都市(精華地区・西木津地区)", "part", "")],
    "けいはんな学研都市(京都府精華町・西木津地区)":
        [("京都府精華町", "けいはんな学研都市(精華町・西木津地区)", "part", ""),
         ("京都府木津川市", "けいはんな学研都市(精華町・西木津地区)", "part", "西木津地区 lies in Kizugawa, which is not printed")],
    "兵庫県播磨科学公園都市": [("兵庫県", "播磨科学公園都市", "unnamed",
                         "planned town across parts of Tatsuno, Kamigori and Sayo; no municipality printed")],
    "鳥取県大山町、伯耆町、米子市(一部)": [("鳥取県大山町", "", "whole", ""), ("鳥取県伯耆町", "", "whole", ""),
                                ("鳥取県米子市", "一部", "part", "")],
    "九州全県": [("", "九州全県", "prefecture", "all Kyushu prefectures")],
    "神奈川県横浜市旭区": [("神奈川県横浜市", "旭区", "part", "")],
    "神奈川県横須賀市、北海道札幌市、旭川市、他": [
        ("神奈川県横須賀市", "", "whole", "other places (他) not named"),
        ("北海道札幌市", "", "whole", "other places (他) not named"),
        ("北海道旭川市", "", "whole", "other places (他) not named")],
    "大阪府、京都府、兵庫県、奈良県、滋賀県、三重県、和歌山県及び愛知県の一部": [("", "", "prefecture", KANSAI)],
    "大阪府、京都府、兵庫県、奈良県、和歌山県、滋賀県、三重県ならびに愛知県の一部": [("", "", "prefecture", KANSAI)],
    "神奈川県川崎市中原区、高津区": [("神奈川県川崎市", "中原区、高津区", "part", "")],
    "大阪府大阪市北区": [("大阪府大阪市", "北区", "part", "")],
    "大阪府堺市南区": [("大阪府堺市", "南区", "part", "")],
    "島根県大田圏域(大田市・川本町・美郷町)": [("島根県大田市", "大田圏域", "whole", ""),
                                  ("島根県川本町", "大田圏域", "whole", ""),
                                  ("島根県美郷町", "大田圏域", "whole", "")],
    "三重県多気町・大台町・渡会町": [("三重県多気町", "", "whole", ""), ("三重県大台町", "", "whole", ""),
                          ("三重県渡会町", "", "whole", "printed 渡会町; the town is 度会町 (Watarai)")],
    "香川県高松市、多度津町、小豆島町 等": [(f"香川県{m}", "", "whole", "other places (等) not named")
                                 for m in ("高松市", "多度津町", "小豆島町")],
    "愛媛県四国中央市、今治市 等": [(f"愛媛県{m}", "", "whole", "other places (等) not named")
                          for m in ("四国中央市", "今治市")],
}
EARLIER_AREA = {"千代田区": "大手町・丸の内・有楽町地区", "港区": "竹芝地区", "大田区": "羽田空港跡地第1ゾーン"}


def split_place(s):
    if s in OVR:
        return OVR[s]
    m = re.fullmatch(r"(.+?)\((.+)\)", s)
    if m and PREF_RE.match(m.group(1)) and "、" not in m.group(1):
        return [(m.group(1), m.group(2), "part", "")]
    pieces, out, pref = re.split(r"[、・]", s), [], ""
    for p in pieces:
        pm = PREF_RE.match(p)
        if pm:
            pref, p = pm.group(1), p[pm.end():]
        out.append((pref + p, "", "whole" if p else "prefecture", ""))
    if all(o[2] == "prefecture" for o in out) and len(out) > 1:
        return [("", s, "prefecture", "")]
    return out


def place_en(pm):
    m = PREF_RE.match(pm)
    pref, muni = (m.group(1), pm[m.end():]) if m else ("", pm)
    if not muni:
        return f"{PREF[pref]} Prefecture" if pref else ""
    return f"{MUNI[muni]}, {PREF[pref]}"


SYM = "☆□○●■"
LEG_A = dict(zip(SYM, ["CAO", "MIC", "METI", "MAAS", "MLIT"]))  # 2021 to 2023
LEG_B = dict(zip(SYM, ["CAO", "MIC", "MLIT", "METI", "MAAS"]))  # 2024 and 2025
PROG = {"CAO": "Cabinet Office Future Technology Implementation Project",
        "MIC": "MIC Smart City Promotion Project", "METI": "METI Regional New MaaS Project",
        "MAAS": "MLIT Japan MaaS Project", "MLIT": "MLIT Smart City Model Projects"}
JP = {"CAO": {y: "未来技術社会実装事業" for y in range(2021, 2026)},
      "MIC": {2021: "データ連携促進型スマートシティ推進事業", 2022: "地域課題解決のためのスマートシティ推進事業",
              2023: "地域課題解決のためのスマートシティ推進事業", 2024: "地域課題解決のためのスマートシティ推進事業",
              2025: "地域社会DX推進パッケージ事業"},
      "METI": {y: "地域新MaaS創出推進事業" for y in range(2021, 2026)},
      "MAAS": {2021: "日本版MaaS推進・支援事業", 2022: "日本版MaaS推進・支援事業", 2023: "日本版MaaS推進・支援事業",
               2024: "共創・MaaS実証プロジェクト(日本版MaaS推進・支援事業)",
               2025: "日本版MaaS推進・支援事業(「交通空白」解消等リ・デザイン全面展開プロジェクト)"},
      "MLIT": {2021: "スマートシティモデルプロジェクト", **{y: "スマートシティ実装化支援事業" for y in range(2022, 2026)}}}
OFFICIAL = {2021: dict(CAO=9, MIC=9, METI=14, MAAS=12, MLIT=30), 2022: dict(CAO=10, MIC=13, METI=11, MAAS=6, MLIT=14),
            2023: dict(CAO=2, MIC=5, METI=8, MAAS=6, MLIT=13), 2024: dict(CAO=1, MIC=8, MLIT=13, METI=6, MAAS=8),
            2025: dict(CAO=3, MIC=2, MLIT=8, METI=5, MAAS=11)}
REGIONS = {2021: 62, 2022: 51, 2023: 32, 2024: 34, 2025: 29}
ROUNDS = [(2021, "210824", "2021-08-24", 2022, 3), (2022, "220713", "2022-07-13", 2023, 4),
          (2023, "230630", "2023-06-30", 2023, 5), (2024, "20240621", "2024-06-21", 2024, 6),
          (2025, "20250411", "2025-04-11", 2025, 7)]

rows = []
for year, stem, date, ftyear, src in ROUNDS:
    leg = LEG_A if year <= 2023 else LEG_B
    text = unicodedata.normalize("NFKC", pypdf.PdfReader(C / f"CAO_smartcity_joint_{date}_bessi2.pdf").pages[0].extract_text())
    text = text.replace("〇", "○")
    lines, items, cur, started = text.splitlines(), {}, None, False
    for ln in lines:
        ln = ln.strip()
        if ln.startswith("項番"):
            started = True; continue
        if not started or not ln:
            continue
        if re.match(r"^\d+\s*[" + SYM + "]", ln):  # map labels
            cur = None; continue
        m = re.match(r"^(\d+) (.+)$", ln)
        if m:
            cur = int(m.group(1)); items[cur] = m.group(2)
        elif cur is not None:
            items[cur] += ln
    assert sorted(items) == list(range(1, REGIONS[year] + 1)), (year, sorted(items))
    count = Counter()
    for n, body in items.items():
        toks = body.split(" ")
        syms = []
        while toks and set(toks[-1]) <= set(SYM):
            syms.insert(0, toks.pop())
        place = " ".join(toks)
        sel, past = syms[0], (syms[1] if len(syms) > 1 else "")
        assert len(syms) in (1, 2) and (year <= 2022 or len(syms) == 1), (year, n, body)
        codes = [leg[c] for c in sel]
        for code, k in Counter(codes).items():
            count[code] += k
        seen = Counter()
        for code in codes:
            seen[code] += 1
            suffix = "" if codes.count(code) == 1 else "ab"[seen[code] - 1]
            pid = f"CAO{year}-{n:02d}-{code}{suffix}"
            for pm, area, scope, note in split_place(place):
                notes = [f"programme name that year: {JP[code][year]}"]
                if note:
                    notes.append(note)
                muni = PREF_RE.sub("", pm)
                if scope == "whole" and not area and muni in EARLIER_AREA and year >= 2024:
                    notes.append(f"printed without an area; earlier rounds name {EARLIER_AREA[muni]}")
                if past:
                    notes.append(f"earlier selections as printed: {past} ("
                                 + ", ".join(dict.fromkeys(leg[c] for c in past)) + ")")
                rows.append({"economy": "Japan", "place_as_printed": pm or place,
                             "place_en": place_en(pm) if pm else ("" if scope != "prefecture" else "several prefectures, as printed"),
                             "area_as_printed": area, "area_scope": scope, "project_id": pid,
                             "programme": PROG[code], "programme_model": "implementation support",
                             "announcement_date": date, "date_precision": "day",
                             "first_treated_year": str(ftyear), "batch": f"joint selection {year}",
                             "source": f"[{src}] Cabinet Office press release {date}, annex 2 (別紙2), item {n}",
                             "note": "; ".join(notes)})
    assert dict(count) == OFFICIAL[year], (year, dict(count), OFFICIAL[year])
    print(year, "regions", len(items), "projects", sum(count.values()), dict(count), "matches the press release")

with open(D / "japan_joint_selection.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, COLS); w.writeheader(); w.writerows(rows)
print("joint rows", len(rows), Counter(r["area_scope"] for r in rows))
print("MLIT rows in joint list", sum(r["programme"].startswith("MLIT Smart") for r in rows))
print("mlit file rows", len(mlit))
