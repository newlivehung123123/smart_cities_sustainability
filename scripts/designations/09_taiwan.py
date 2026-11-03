"""Check Taiwan's smart city programme (普及智慧城鄉生活應用計畫, started in 2018 by the Industrial Development Bureau of the
Ministry of Economic Affairs; the case book read here is on the Ministry of Digital Affairs file server and lists approvals
to 2025). No designation list is written: the programme subsidises firms, all 22 counties and cities sit on its platform,
and its 2018 local projects already span most of them, so Taiwan is coded as a nationwide programme (see the sources file).

argv[1] = designations directory (unused, kept for the common call), argv[2] = data/raw/designations/sources.
Reads the annex "補助計畫清單" of the ministry's case book (taiwan_saved/moda_smart_city_case_book_6.txt, made from the PDF
saved on 1 Nov 2026) and two Executive Yuan releases (ey_*.txt, made from the html saved the same day), asserts the counts
and passages quoted in the sources file and prints the first year each county or city is named in a local project title.
"""
import collections, re, sys
from pathlib import Path

S = Path(sys.argv[2]) / "taiwan_saved"
t = (S / "moda_smart_city_case_book_6.txt").read_text(encoding="utf-8")
assert "工業局自2018年開始推行「普及智慧城鄉生活應用計" in t
for name, date, n in [("ey_2019-11-13.txt", "日期：108-11-13", "第九次"), ("ey_2020-07-22.txt", "日期：109-07-22", "第十次")]:
    e = (S / name).read_text(encoding="utf-8")
    assert date in e and f"召開「智慧城鄉溝通平台{n}會議」，邀集22個地方縣市政府" in e, name
assert "「普及智慧城鄉生活應用計畫」，目前已累計224案例、295業者投入" in e
body = t[t.index("=== page 25 ==="):]
body = re.sub(r"=== page \d+ ===\n|\n\d{3}\n|核定日期 分類 公司名稱 計畫名稱\n", "\n", body)
recs = [re.sub(r"\s*\n\s*", "", r) for r in re.split(r"\n(?=20[12]\d\.\d\d\.\d\d )", body)
        if re.match(r"20[12]\d\.\d\d\.\d\d ", r)]
assert len(recs) == 268
by_year = collections.Counter(r[:4] for r in recs)
assert by_year == {"2018": 141, "2019": 29, "2020": 53, "2021": 17, "2023": 18, "2025": 10}, by_year
local18 = [r for r in recs if r.startswith("2018") and "地方創新類計畫" in r]
assert len(local18) == 55
dates = sorted(r[:10] for r in local18)
assert (dates[0], dates[-1]) == ("2018.07.13", "2018.09.06")

# Counties and cities named in a title. Kaohsiung's "雄健康" and Chiayi's "嘉驛" are not counted (city or county unclear).
NAMES = {"基隆市": ["基隆"], "臺北市": ["臺北", "台北"], "新北市": ["新北"], "桃園市": ["桃園"], "新竹市": ["新竹市"],
         "新竹縣": ["新竹縣"], "苗栗縣": ["苗栗"], "臺中市": ["臺中", "台中"], "彰化縣": ["彰化"], "南投縣": ["南投"],
         "雲林縣": ["雲林"], "嘉義市": ["嘉義市"], "嘉義縣": ["嘉義縣"], "臺南市": ["臺南", "台南", "府城"],
         "高雄市": ["高雄"], "屏東縣": ["屏東"], "宜蘭縣": ["宜蘭"], "花蓮縣": ["花蓮"], "臺東縣": ["臺東", "台東"],
         "澎湖縣": ["澎湖", "菊島"], "金門縣": ["金門"], "連江縣": ["連江", "馬祖"]}
assert len(NAMES) == 22
named = {c for r in local18 for c, keys in NAMES.items() if any(k in r for k in keys)}
untitled = sum(not any(k in r for keys in NAMES.values() for k in keys) for r in local18)
assert len(named) == 16 and untitled == 28, (sorted(named), untitled)
print(len(recs), "approvals:", dict(sorted(by_year.items())))
print(len(local18), "local innovation projects approved", dates[0], "to", dates[-1] + ";",
      len(named), "of 22 counties and cities named in titles:", " ".join(sorted(named)) + ";",
      untitled, "titles name no county")
first = {}
for r in sorted(recs):
    if "創新服務類" not in r:
        for c, keys in NAMES.items():
            if any(k in r for k in keys):
                first.setdefault(c, r[:4])
assert first.get("苗栗縣") is None and sum(y == "2018" for y in first.values()) == 16
print("first year named in a local project title:", "; ".join(f"{c} {first.get(c, 'never')}" for c in NAMES))
