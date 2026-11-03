"""Link every designation row to the district units it treats (dataset plan section 2c).

Rules, in order:
- Hand pins (data/raw/designations/link_pins.csv, resolved to units by 02_pins.py) come first. A pin with a project_id
  applies to that row only; a pin without one applies to every row naming that place. A pin that resolves to no unit
  leaves its row as "prefecture only".
- Singapore, Hong Kong and Macau rows treat the economy's only unit.
- Rows that name only a prefecture or region (area_scope prefecture or unnamed) treat no unit; every unit of that
  prefecture is listed with rule "prefecture only", for the check that drops them from the comparison group. Rows that
  name several prefectures list no unit.
- Otherwise the place name (place_en before the first comma) is matched to unit names of the same economy, inside the
  prefecture or province named after the comma when there is one. Names are compared after removing accents,
  bracketed text, punctuation, spaces and administrative words (city, province, council and the like, and the
  suffixes -si, -gun, -gu, -do in Korea, -shi, -ku, -machi, -mura, -cho, -son in Japan and amphoe, khet in Thailand
  only, since elsewhere they are words of a name, as in Si Chiang Mai). In Japan, long vowels are dropped and Hepburn
  spellings folded to Kunrei (Ooda and Oda, Yaidu and Yaizu, Syoudoshima and Shodoshima, Gotenba and Gotemba), because
  gbOpen spells names both ways. In Indonesia "City" maps to the "Kota" units, so that Kota Semarang and Semarang
  Regency stay apart, and a bare name (only network members have one) is tried as "Kota" first, since members are city
  governments; Banyuwangi and Sumedang have no Kota and fall back to the regency. In Thailand a city or town
  municipality named after its province lies in the Mueang district of that province.
- A whole-area row whose name matches no unit but matches a prefecture or province (a city larger than one unit, such
  as Busan, Bangkok or Ho Chi Minh City) treats every unit of it, rule "whole cluster".
Rows still unmatched, or matched to more than one unit by name, are written to unmatched.csv and must be pinned.

argv[1] = data/raw/designations, argv[2] = data/final/units.csv, argv[3] = data/raw/boundaries/jpn_name_fill.csv,
argv[4] = data/interim/treatment/pins_resolved.csv, argv[5] = output folder (data/interim/treatment). Writes links.csv
(one line per designation row and unit) and unmatched.csv there.
"""
import re, sys, unicodedata
from pathlib import Path

import pandas as pd

DES, UNITS, FILL, PINS, OUT = (Path(a) for a in sys.argv[1:6])
STOP = {"city", "province", "prefecture", "regency", "municipality", "municipal", "district", "town", "metropolitan",
        "special", "self", "governing", "autonomous", "county", "township", "the", "of", "council", "corporation",
        "subdistrict"}
# suffixes that are words of a name elsewhere (Si Chiang Mai in Thailand, Son Tra in Vietnam) are dropped only at home
STOP_ISO = {"KOR": {"si", "gun", "gu", "do"}, "JPN": {"shi", "si", "ku", "machi", "mura", "cho", "son"},
            "THA": {"amphoe", "khet"}}
SINGLE = {"Singapore", "Hong Kong", "Macau"}


def norm(s, iso=None):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\(.*?\)", " ", s)
    stop = STOP | STOP_ISO.get(iso, set())
    s = "".join(w for w in re.sub(r"[-'’.,/]", " ", s).split() if w not in stop)
    if iso == "JPN":  # fold Hepburn to Kunrei on both sides, since gbOpen mixes them (Syoudoshima, Yaidu)
        for a, b in (("ou", "o"), ("oo", "o"), ("uu", "u"), ("tsu", "tu"), ("shi", "si"), ("chi", "ti"), ("sh", "sy"),
                     ("ch", "ty"), ("fu", "hu"), ("ji", "zi"), ("di", "zi"), ("du", "zu"), ("j", "zy")):
            s = s.replace(a, b)
        s = re.sub(r"n(?=[bmp])", "m", s)
    return s


units = pd.read_csv(UNITS)
fill = pd.read_csv(FILL).query("accepted").set_index("unit_id").name_filled
units.loc[units.unit_id.isin(fill.index), "name"] = units.unit_id.map(fill)
units["key"] = [norm(n, i) for n, i in zip(units.name, units.iso3)]
units["ckey"] = [norm(n, i) for n, i in zip(units.cluster_name, units.iso3)]
econ_iso = units.drop_duplicates("economy").set_index("economy").iso3.to_dict() | {"Korea": "KOR"}
pins = pd.read_csv(PINS, dtype=str).fillna("")

links, unmatched = [], []
for f in sorted(p for p in DES.glob("*.csv") if p.name != "link_pins.csv"):
    for k, r in pd.read_csv(f).iterrows():
        iso = econ_iso[r.economy]
        u = units[units.iso3 == iso]
        name, _, hint = str(r.place_en).partition(",")
        key, hkey = norm(name, iso), norm(hint, iso)
        if iso == "IDN" and re.search(r"\bcity\b", name, re.I):
            key = "kota" + key
        base = {"file": f.name, "row": k, "project_id": r.project_id, "economy": r.economy, "place_en": r.place_en,
                "area_scope": r.area_scope, "first_treated_year": r.first_treated_year, "flag": ""}
        pin = pins[(pins.economy == r.economy) & (pins.place_en == r.place_en) & pins.project_id.isin(["", r.project_id])]
        pin = pin.sort_values("project_id").tail(1)  # a row's own pin wins over the place-wide one
        scope = r.area_scope
        if len(pin) and pin.unit_ids.iloc[0] == "":
            scope, pin = "prefecture", pin.iloc[:0]
        if len(pin):
            ids = pin.unit_ids.iloc[0].split(";")
            hit, rule = u[u.unit_id.isin(ids)], "pin"
            assert len(hit) == len(ids), (r.project_id, r.place_en)
            base["flag"] = pin.flag.iloc[0]
        elif r.economy in SINGLE:
            hit, rule = u, "single unit"
        elif str(r.place_en).startswith("several prefectures"):
            links.append(base | {"unit_id": None, "unit_name": None, "cluster_name": None, "rule": "several prefectures"})
            continue
        elif scope in ("prefecture", "unnamed"):
            hit, rule = u[u.ckey == (hkey or key)], "prefecture only"
            if hit.empty:
                hit = u[u.ckey == key]
        else:
            inside = u[u.ckey == hkey] if hkey and (u.ckey == hkey).any() else u
            bare_idn = iso == "IDN" and not re.search(r"\b(city|regency)\b", name, re.I)
            hit, rule = inside[inside.key == ("kota" + key if bare_idn else key)], "name"
            if hit.empty and iso == "THA":
                hit, rule = inside[inside.key == "mueang" + key], "Mueang district"
            if hit.empty and bare_idn:
                hit = inside[inside.key == key]
            if hit.empty and scope == "whole":
                hit, rule = u[u.ckey == key], "whole cluster"
        if hit.empty or (rule == "name" and len(hit) > 1):
            unmatched.append(base | {"candidates": "; ".join(hit.unit_id + " " + hit.name + " (" + hit.cluster_name + ")")})
            continue
        if scope == "part" and not base["flag"]:
            base["flag"] = "part"
        links += [base | {"unit_id": x, "unit_name": n, "cluster_name": c, "rule": rule}
                  for x, n, c in zip(hit.unit_id, hit.name, hit.cluster_name)]

OUT.mkdir(parents=True, exist_ok=True)
links, unmatched = pd.DataFrame(links), pd.DataFrame(unmatched)
links.to_csv(OUT / "links.csv", index=False)
unmatched.to_csv(OUT / "unmatched.csv", index=False)
rows = links.drop_duplicates(["file", "row"])
print(pd.crosstab(rows.economy, rows.rule))
print(len(unmatched), "rows unmatched:", unmatched.groupby("economy").size().to_dict() if len(unmatched) else {})
