"""Write japan_sdgs_future_cities.csv (Cabinet Office SDGs Future Cities and Municipal SDGs Model
Projects, 2018 to 2025) and japan_super_city.csv (National Strategic Special Zones: Super City and
Digital Garden Health Special Zones, 2022) from the official lists.

argv[1] = designations directory, argv[2] = data/raw/designations/sources.
English place names come from the kana readings in the MIC municipal code list (1 Jan 2024),
in Hepburn without macrons.
"""
import csv, re, sys, unicodedata
from pathlib import Path
import pandas as pd
import pypdf

D, C = Path(sys.argv[1]), Path(sys.argv[2])
COLS = ["economy", "place_as_printed", "place_en", "area_as_printed", "area_scope",
        "project_id", "programme", "programme_model", "announcement_date", "date_precision",
        "first_treated_year", "batch", "source", "note"]
BASE = "https://www.chisou.go.jp/tiiki/kankyo/teian/"

# ---- Kana readings to Hepburn ----
ROW = dict(zip("アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ",
               "a i u e o ka ki ku ke ko sa shi su se so ta chi tsu te to na ni nu ne no ha hi fu he ho "
               "ma mi mu me mo ya yu yo ra ri ru re ro wa o".split()))
ROW.update(zip("ガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポ",
               "ga gi gu ge go za ji zu ze zo da ji zu de do ba bi bu be bo pa pi pu pe po".split()))
SMALL = {"ャ": "a", "ュ": "u", "ョ": "o"}


def hepburn(kana):
    k = unicodedata.normalize("NFKC", kana)
    syl, i = [], 0
    while i < len(k):
        ch, nx = k[i], k[i + 1] if i + 1 < len(k) else ""
        if nx in SMALL and ch in ROW:
            stem = ROW[ch][:-1]
            syl.append(stem + SMALL[nx] if stem in ("sh", "ch", "j") else stem + "y" + SMALL[nx])
            i += 2
            continue
        syl.append({"ッ": "Q", "ン": "N", "ー": ""}.get(ch, ROW.get(ch, "?")))
        i += 1
    out = ""
    for j, s in enumerate(syl):
        nxt = next((t for t in syl[j + 1:] if t), "")
        if s == "Q":
            out += "t" if nxt.startswith("ch") else nxt[:1]
        elif s == "N":
            out += "m" if nxt[:1] in ("b", "m", "p") else "n"
        else:
            out += s
    if "?" in out:
        raise ValueError(f"unknown kana in {kana}")
    return out.replace("ou", "o").replace("oo", "o").replace("uu", "u")


# 広陵町 is printed ｺｳﾘﾖｳ (large ﾖ) in the MIC list; 群馬 keeps its usual spelling
KEEP = {"広陵町": "Koryo", "群馬県": "Gunma"}
mic = pd.read_excel(C / "MIC_municipal_codes_2024-01-01.xlsx", sheet_name=0, dtype=str)
mic.columns = ["code", "pref", "muni", "pref_kana", "muni_kana"]
SUFFIX = {"市": ("シ",), "区": ("ク",), "町": ("マチ", "チョウ"), "村": ("ムラ", "ソン"),
          "県": ("ケン",), "府": ("フ",), "都": ("ト",), "道": ("",)}
PREF_EN, MUNI_EN = {}, {}
for r in mic.itertuples():
    name, kana = (r.pref, r.pref_kana) if pd.isna(r.muni) else (r.muni, r.muni_kana)
    kana = unicodedata.normalize("NFKC", kana)
    cut = next(s for s in SUFFIX[name[-1]] if kana.endswith(s))
    en = KEEP.get(name) or hepburn(kana[: len(kana) - len(cut)]).capitalize()
    if pd.isna(r.muni):
        PREF_EN[r.pref] = en
    else:
        MUNI_EN[(r.pref, r.muni)] = en
PREF_RE = re.compile(r"^(北海道|東京都|京都府|大阪府|[^、・()]{2,3}?県)")


def split_place(p):
    m = PREF_RE.match(p)
    return m.group(1), p[m.end():]


def place_en(pref, muni):
    if not muni:
        return f"{PREF_EN[pref]} Prefecture"
    return f"{MUNI_EN[(pref, muni)]}, {PREF_EN[pref]}"


def numbered(f, n_expected):
    """Proposer names from a list printed as 'N proposer title', N = 1, 2, ..."""
    t = unicodedata.normalize("NFKC", "\n".join(p.extract_text() for p in pypdf.PdfReader(C / f).pages))
    out = []
    while m := re.search(rf"^{len(out) + 1}\s+(\S+)", t, re.M):
        out.append(m.group(1).replace("⻄", "西"))
    assert len(out) == n_expected, (f, len(out), n_expected)
    return out


# Round: announcement date, precision, the URL folder and file names of press release, city list, model list
ROUNDS = {
    2018: ("2018-06-15", "day", "pdf/", "result01.pdf", "result02.pdf", "result03.pdf", 29, 10),
    2019: ("2019-07-01", "day", "2019sdgs_pdf/", "sdgsfuturecitypress0701.pdf", "sdgsfuturecity2019.pdf", "sdgsmodel2019.pdf", 31, 10),
    2020: ("2020-07-17", "day", "2020sdgs_pdf/", "sdgs_r2futurecity_press0701.pdf", "sdgs_r2futurecity.pdf", "sdgs_r2model.pdf", 33, 10),
    2021: ("2021-05-21", "day", "2021sdgs_pdf/", "05_puresuissiki.pdf", "03_miraitosiitiran.pdf", "04_moderujigyouitiran.pdf", 31, 10),
    2022: ("2022-05-20", "day", "2022sdgs_pdf/", "05_puresuissiki.pdf", "03_miraitosiitiran.pdf", "04_moderujigyouitiran.pdf", 30, 10),
    2023: ("2023-05-19", "day", "2023sdgs_pdf/", "05_puresuissiki.pdf", "03_miraitosiitiran.pdf", "04_moderujigyouitiran.pdf", 28, 10),
    2024: ("2024-05-21", "day", "2024sdgs_pdf/", "04_R6puresuissiki.pdf", "06_R6miraitosiitiran.pdf", "07_R6moderujigyouitiran.pdf", 24, 10),
    2025: ("2025-06-23", "day", "2025sdgs_pdf/", "01_puresushiryou.pdf", "03_R7miraitoshiichiran.pdf", None, 9, 0),
}
FC_NOTE = ("label awarded to municipalities proposing SDGs initiatives; the 2024 summary (別紙1) states one further "
           "application to the regional revitalisation grant (地方創生推進交付金) outside the usual cap")
MP_NOTE = "subsidy to the selected project; up to 20 million yen per city in 2024 (別紙1)"


def first_treated(date):
    y, m = int(date[:4]), int(date[5:7])
    return y if m <= 6 else y + 1


rows = []
for year, (date, prec, folder, press, fc_file, mp_file, n_fc, n_mp) in ROUNDS.items():
    fc = numbered(f"CAO_sdgs_{year}_future_cities.pdf", n_fc)
    mp = numbered(f"CAO_sdgs_{year}_model_projects.pdf", n_mp) if mp_file else []
    for prog, model, names, file, label, note in (
            ("SDGs Future Cities", "certification", fc, fc_file, "FC", FC_NOTE),
            ("Municipal SDGs Model Projects", "implementation support", mp, mp_file, "MP", MP_NOTE)):
        for i, printed in enumerate(names, 1):
            printed = printed.replace("(注1)", "")
            extra = ""
            if printed == "鹿児島県奄美市" and label == "MP":
                extra = "; note 1 on the list: selected as an SDGs Future City in 2023"
            if printed == "新潟県佐渡市" and label == "MP":
                extra = "; selected as an SDGs Future City in 2022"
            places = ["大阪府", "大阪府大阪市"] if printed == "大阪府・大阪市" else [printed]
            if len(places) == 2:
                extra += "; joint proposal by Osaka Prefecture and Osaka city, one row each"
            for pl in places:
                pref, muni = split_place(pl)
                rows.append({
                    "economy": "Japan", "place_as_printed": printed, "place_en": place_en(pref, muni),
                    "area_as_printed": "", "area_scope": "whole" if muni else "prefecture",
                    "project_id": f"SDGS{year}-{label}{i:02d}", "programme": prog, "programme_model": model,
                    "announcement_date": date, "date_precision": prec, "first_treated_year": first_treated(date),
                    "batch": f"{year} round",
                    "source": f"Cabinet Office (地方創生推進室) list, {BASE}{folder}{file}, item {i}; "
                              f"press release {BASE}{folder}{press}",
                    "note": note + extra + ("; after the panel" if year == 2025 else "")})

fc_rows = [r for r in rows if r["programme"] == "SDGs Future Cities"]
mp_rows = [r for r in rows if r["programme"] != "SDGs Future Cities"]
assert len({r["project_id"] for r in fc_rows if r["batch"] != "2025 round"}) == 206   # summary 別紙4: 206 cities 2018 to 2024
assert len({r["project_id"] for r in mp_rows}) == 70                                 # summary 別紙4: 70 model projects
fc_set = {(r["place_as_printed"]) for r in fc_rows}
assert all(r["place_as_printed"] in fc_set for r in mp_rows)  # every model project city is a Future City
with open(D / "japan_sdgs_future_cities.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, COLS)
    w.writeheader()
    w.writerows(rows)

# ---- Super City and Digital Garden Health Special Zones (Cabinet Office release, 10 March 2022) ----
SC = "https://www.chisou.go.jp/tiiki/kokusentoc/dai53/Release.pdf"
ORDER = "cabinet order (政令) designating the zones adopted 12 April 2022 (council materials of Osaka and Tsukuba, 第1回 資料2)"
STATUS = ("status: regulatory special zone; the release names digitalisation and regulatory reform and no funding; "
          "the council timeline records a Cabinet Office survey project on advanced services adopted 20 July 2022, "
          "places not named")
sc = [("つくば市", "茨城県", "つくば市", "つくば市全域", "whole", "SC2022-1", "National Strategic Special Zones: Super City", ""),
      ("大阪市", "大阪府", "大阪市", "万博予定地の夢洲、大阪駅北の「うめきた2期」", "part", "SC2022-2",
       "National Strategic Special Zones: Super City", ""),
      ("吉備中央町", "岡山県", "吉備中央町", "", "whole", "DH2022-1",
       "National Strategic Special Zones: Digital Garden Health Special Zone", "; not in design Table 1, sensitivity check only"),
      ("茅野市", "長野県", "茅野市", "", "whole", "DH2022-1",
       "National Strategic Special Zones: Digital Garden Health Special Zone", "; not in design Table 1, sensitivity check only"),
      ("加賀市", "石川県", "加賀市", "", "whole", "DH2022-1",
       "National Strategic Special Zones: Digital Garden Health Special Zone", "; not in design Table 1, sensitivity check only")]
with open(D / "japan_super_city.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, COLS)
    w.writeheader()
    for printed, pref, muni, area, scope, pid, prog, extra in sc:
        w.writerow({"economy": "Japan", "place_as_printed": printed, "place_en": place_en(pref, muni),
                    "area_as_printed": area, "area_scope": scope, "project_id": pid, "programme": prog,
                    "programme_model": "certification", "announcement_date": "2022-03-10", "date_precision": "day",
                    "first_treated_year": 2022, "batch": "2022 designation",
                    "source": f"Cabinet Office (地方創生推進事務局) release on the 53rd Council on National Strategic "
                              f"Special Zones, {SC}, page 1 and annex 2",
                    "note": f"{STATUS}; {ORDER}{extra}"})

print(len(fc_rows), "Future City rows,", len(mp_rows), "Model Project rows,", len(sc), "special zone rows")
