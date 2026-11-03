"""Check the links made by name against geography (dataset plan section 2c).

A random sample of places linked by name (up to 15 distinct places per economy, seed 1) is looked up through the
OpenStreetMap Nominatim search service by the name as printed in the source, in the source's own script, inside the
place's country (one request every 1.5 seconds, answers kept with the pin answers). An outline that comes back is
assigned to the unit holding most of it, a point to the unit that contains it. The link agrees when that unit is one of
the units the row was linked to.

argv[1] = data/raw/designations, argv[2] = data/interim/treatment/links.csv, argv[3] = data/interim/units,
argv[4] = data/raw/boundaries. Writes link_check.csv next to links.csv.
"""
import hashlib, json, subprocess, sys, time
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely
from shapely.geometry import shape

DES, LINKS, U, RAW = (Path(a) for a in sys.argv[1:5])
UA = "smart_cities_sustainability research script (github.com/newlivehung123123/smart_cities_sustainability)"
URL = "https://nominatim.openstreetmap.org/search"
ISO2 = {"JPN": "jp", "KOR": "kr", "THA": "th", "MYS": "my", "BRN": "bn", "LAO": "la", "MMR": "mm", "KHM": "kh",
        "PHL": "ph", "IDN": "id"}


def search(q, cc):
    f = RAW / "nominatim" / f"search_{hashlib.sha1(f'{cc}|{q}'.encode()).hexdigest()[:12]}.json"
    if not f.exists():
        out = subprocess.run(["curl", "-sSfG", "-A", UA, "-m", "60", URL, "--data-urlencode", f"q={q}",
                              "--data-urlencode", f"countrycodes={cc}", "-d", "format=jsonv2", "-d", "limit=1",
                              "-d", "dedupe=0", "-d", "polygon_geojson=1", "-d", "namedetails=1"],
                             capture_output=True, check=True).stdout
        f.write_bytes(out)
        time.sleep(1.5)
    a = json.loads(f.read_text())
    return a[0] if a else None


units = gpd.read_parquet(U / "units.parquet").to_crs(6933)
printed = pd.concat([pd.read_csv(f).assign(file=f.name).reset_index(names="row")[["file", "row", "place_as_printed"]]
                     for f in DES.glob("*.csv") if f.name != "link_pins.csv"])
links = pd.read_csv(LINKS).merge(printed, on=["file", "row"])
named = links[links.rule.isin(["name", "Mueang district"])]
places = named.drop_duplicates(["economy", "place_as_printed"])
sample = places.groupby("economy", group_keys=False).apply(lambda g: g.sample(min(len(g), 15), random_state=1))

rows = []
for _, s in sample.iterrows():
    iso = units.loc[units.unit_id == s.unit_id, "iso3"].iloc[0]
    ue = units[units.iso3 == iso]
    a = search(s.place_as_printed, ISO2[iso])
    got = None
    if a is not None:
        g = gpd.GeoSeries([shape(a["geojson"])], crs=4326).to_crs(6933)[0]
        if g.geom_type in ("Polygon", "MultiPolygon"):
            got = ue.unit_id.iloc[shapely.area(shapely.intersection(ue.geometry.values, g)).argmax()]
        else:
            hit = ue[ue.contains(g)]
            got = hit.unit_id.iloc[0] if len(hit) else None
    linked = set(named.loc[(named.file == s.file) & (named.row == s.row), "unit_id"])
    rows.append({"economy": s.economy, "place_as_printed": s.place_as_printed, "place_en": s.place_en, "rule": s.rule,
                 "linked_unit": s.unit_name, "osm_name": a.get("display_name", "")[:80] if a else None,
                 "osm_unit": ue.loc[ue.unit_id == got, "name"].iloc[0] if got else None,
                 "agree": None if got is None else got in linked})
t = pd.DataFrame(rows)
t.to_csv(LINKS.parent / "link_check.csv", index=False)
print(t.groupby("economy").agg(checked=("agree", "size"), found=("agree", "count"), agree=("agree", "sum")).to_string())
print(t[t.agree == False].to_string())
