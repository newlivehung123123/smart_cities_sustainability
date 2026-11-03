"""Build the treatment tables (dataset plan sections 2 and 6).

Each link from 01_link.py gets the programme fields of its designation row and a specification:
- main: ASEAN Smart Cities Network; Japan MLIT Smart City Model Projects (2019 to 2020 list, and the same programme in
  the joint selection from FY2021), SDGs Future Cities, Municipal SDGs Model Projects and Super City; Thailand depa
  smart city logo; Korea National Pilot Smart Cities and Smart Challenge (campus challenge excepted); Indonesia Gerakan
  Menuju Smart City; Malaysia Smart City Framework pilots and the 2024 rating; Singapore Smart Nation and the Hong Kong
  Blueprint (synthetic control only).
- one named check for every other row: jp_joint (the other four joint-selection programmes), jp_digital_garden,
  kr_campus, kr_theme_complex, my_rating_2023 (roster partial), ph_digital_cities, hk_kowloon_east, macau (not
  estimated).
A link treats its unit unless the row names only a prefecture or several prefectures. A year printed with an unknown
month ("2027 if after June") takes the later year and is flagged, as section 2 requires.

Writes data/final/designation_links.csv (one line per designation row and unit) and data/final/treatment.csv (one line
per unit), whose columns are explained in docs/codebook.md. Every first_treated column is the first year of a treating
link under the stated specification, empty if never.

argv[1] = data/raw/designations, argv[2] = data/interim/treatment/links.csv, argv[3] = data/final/units.csv,
argv[4] = data/final
"""
import re, sys
from pathlib import Path

import pandas as pd

DES, LINKS, UNITS, FINAL = (Path(a) for a in sys.argv[1:5])

rows = pd.concat([pd.read_csv(f, dtype=str).reset_index(names="row").assign(file=f.name)
                  for f in sorted(DES.glob("*.csv")) if f.name != "link_pins.csv"])
rows["row"] = rows.row.astype(int)
keep = ["file", "row", "programme", "programme_model", "batch", "announcement_date", "date_precision", "note"]
links = pd.read_csv(LINKS, dtype={"first_treated_year": str}).merge(rows[keep], on=["file", "row"], how="left",
                                                                     validate="many_to_one")
assert links.programme.notna().all()

y = links.first_treated_year.str.extract(r"^(\d{4})")[0]
links["year_flag"] = (~links.first_treated_year.str.fullmatch(r"\d{4}")).map({True: "month unknown, later year", False: ""})
links["first_treated_year"] = y.astype(int)


def spec(r):
    p, b = r.programme, str(r.batch)
    if r.file == "japan_joint_selection.csv":
        return "main" if p == "MLIT Smart City Model Projects" else "jp_joint"
    if p.startswith("National Strategic Special Zones: Digital Garden"):
        return "jp_digital_garden"
    if r.file == "korea_molit_smart_city.csv":
        return "kr_campus" if b == "2021 campus" else "kr_theme_complex" if p.startswith("Theme-type") else "main"
    if r.file == "malaysia_kpkt_smart_city.csv" and b.startswith("rating 2023"):
        return "my_rating_2023"
    if r.file == "philippines_dict_digital_cities.csv":
        return "ph_digital_cities"
    if p.startswith("Kowloon East"):
        return "hk_kowloon_east"
    if r.file == "macau_smart_city.csv":
        return "macau"
    return "main"


links["spec"] = links.apply(spec, axis=1)
links["treats"] = ~links.rule.isin(["prefecture only", "several prefectures"])
roster = links.note.str.extract(r"roster: ([a-z ]+?)(?: \(|;|$)")[0]
links["id_mou_only"] = (links.economy == "Indonesia") & (roster == "mou")
links["id_alt_year"] = links.first_treated_year.where(links.batch != "2023 round", 2022).where(links.economy == "Indonesia")
links = links.rename(columns={"rule": "link_rule", "flag": "link_flag"})
links["link_flag"] = links.link_flag.fillna("")
cols = ["unit_id", "unit_name", "cluster_name", "economy", "file", "row", "project_id", "place_en", "area_scope",
        "programme", "programme_model", "batch", "announcement_date", "date_precision", "first_treated_year",
        "year_flag", "spec", "link_rule", "link_flag", "treats", "id_mou_only", "id_alt_year"]
links = links[cols].sort_values(["economy", "file", "row", "unit_id"])

units = pd.read_csv(UNITS)
t = units[["unit_id", "economy", "iso3", "cluster_name", "urban", "city_state", "unit_flag", "in_panel", "pop2015",
           "size_group"]].copy()
tr = links[links.treats & links.unit_id.notna()]
main = tr[tr.spec == "main"]


def first(sel, year="first_treated_year"):
    return t.unit_id.map(sel.groupby("unit_id")[year].min()).astype("Int64")


t["first_treated"] = first(main)
firsts = main.merge(t[["unit_id", "first_treated"]], on="unit_id")
firsts = firsts[firsts.first_treated_year == firsts.first_treated.astype(int)]
g = firsts.groupby("unit_id")
t["first_programme"] = t.unit_id.map(g.programme.agg(lambda s: "; ".join(sorted(set(s)))))
t["first_model"] = t.unit_id.map(g.programme_model.agg(lambda s: "; ".join(sorted(set(s)))))
t["first_is_part"] = t.unit_id.map(g.link_flag.agg(lambda s: (s == "part").all())).astype("boolean")
t["n_main_projects"] = t.unit_id.map(main.groupby("unit_id").project_id.nunique()).fillna(0).astype(int)
for m, c in (("implementation support", "impl"), ("certification", "cert"), ("network membership", "ascn")):
    t[f"first_treated_{c}"] = first(main[main.programme_model == m])
sc = main.programme.str.startswith("National Strategic Special Zones: Super City")
t["first_treated_impl_sc"] = first(main[(main.programme_model == "implementation support") | sc])
t["first_treated_cert_sc"] = first(main[(main.programme_model == "certification") & ~sc])
t["first_treated_no_part"] = first(main[main.link_flag != "part"])
for s in ("jp_joint", "jp_digital_garden", "kr_campus", "kr_theme_complex", "my_rating_2023", "ph_digital_cities",
          "hk_kowloon_east"):
    t[f"first_treated_{s}"] = first(tr[tr.spec.isin(["main", s])])
t["first_treated_id_2022"] = first(main.assign(first_treated_year=main.id_alt_year.fillna(main.first_treated_year)))
t["first_treated_id_no_mou_only"] = first(main[~main.id_mou_only])
t["id_mou_only_unit"] = t.first_treated.notna() & t.first_treated_id_no_mou_only.isna()
pref = links[(links.link_rule == "prefecture only") & (links.spec == "main")]
t["prefecture_named_year"] = first(pref)

FINAL.mkdir(parents=True, exist_ok=True)
links.to_csv(FINAL / "designation_links.csv", index=False)
t.to_csv(FINAL / "treatment.csv", index=False)

p = t[t.in_panel]
s = p.groupby("economy").agg(panel_units=("unit_id", "size"), treated=("first_treated", "count"),
                             treated_by_2024=("first_treated", lambda x: int((x <= 2024).sum())),
                             first_is_part=("first_is_part", "sum"),
                             in_named_prefecture=("prefecture_named_year", "count"))
print(s.to_string())
print("panel units treated by 2024:", int((p.first_treated <= 2024).sum()), "of", len(p),
      "| first treated years:", p.first_treated.value_counts().sort_index().to_dict())
print("city-states:", t[t.city_state][["economy", "first_treated", "first_treated_hk_kowloon_east"]].to_dict("records"))
