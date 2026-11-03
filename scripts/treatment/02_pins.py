"""Resolve the hand pins in link_pins.csv to district units (dataset plan section 2c).

Each pin gives a place query (several joined by " | " are combined). The query is looked up once through the
OpenStreetMap Nominatim search service inside the pin's country (one request every 1.5 seconds, as its usage policy
asks), and the answer is kept. The outline that comes back decides the units:
- an area treats the units lying at least half inside it, or, if there are none, the unit holding most of it;
- a point treats the unit that contains it.
A query "line=<name>" collects every OSM way of that name (roads and canals are cut into many ways), widens them by
250 m on each side and treats the units holding at least 5 percent of that strip, so that a canal on a district border
counts for both sides. A query "cluster=<name>" treats every unit of that prefecture or province, and "units=<a>;<b>"
treats the units of those names, each with the reason given in the pin.

argv[1] = data/raw/designations/link_pins.csv, argv[2] = data/interim/units, argv[3] = data/raw/boundaries,
argv[4] = output folder (data/interim/treatment). Writes pins_resolved.csv there and the raw answers into
argv[3]/nominatim/search_*.json.
"""
import hashlib, json, subprocess, sys, time
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely
from shapely.geometry import shape

PINS, U, RAW, OUT = (Path(a) for a in sys.argv[1:5])
UA = "smart_cities_sustainability research script (github.com/newlivehung123123/smart_cities_sustainability)"
URL = "https://nominatim.openstreetmap.org/search"
ISO2 = {"JPN": "jp", "KOR": "kr", "THA": "th", "MYS": "my", "BRN": "bn", "LAO": "la", "MMR": "mm", "KHM": "kh",
        "PHL": "ph", "IDN": "id"}

units = gpd.read_parquet(U / "units.parquet")
units_ea = units.to_crs(6933)
iso = units.drop_duplicates("economy").set_index("economy").iso3.to_dict() | {"Korea": "KOR"}
d = RAW / "nominatim"
d.mkdir(exist_ok=True)


def search(q, cc, limit=1):
    tag = f"{cc}|{q}" if limit == 1 else f"{cc}|{q}|{limit}"
    f = d / f"search_{hashlib.sha1(tag.encode()).hexdigest()[:12]}.json"
    if not f.exists():
        out = subprocess.run(["curl", "-sSfG", "-A", UA, "-m", "60", URL, "--data-urlencode", f"q={q}",
                              "--data-urlencode", f"countrycodes={cc}", "-d", "format=jsonv2", "-d", f"limit={limit}",
                              "-d", "dedupe=0", "-d", "polygon_geojson=1", "-d", "namedetails=1"],
                             capture_output=True, check=True).stdout
        f.write_bytes(out)
        time.sleep(1.5)
    a = json.loads(f.read_text())
    return a if limit > 1 else (a[0] if a else None)


def resolve(q, i3):
    u, ue = units[units.iso3 == i3], units_ea[units_ea.iso3 == i3]
    if q.startswith("cluster="):
        hit = u[u.cluster_name == q[8:]]
        return list(hit.index), {"osm_name": q[8:], "geom": "cluster"}
    if q.startswith("units="):
        hit = u[u.name.isin(q[6:].split(";"))]
        assert len(hit) == len(q[6:].split(";")), q
        return list(hit.index), {"osm_name": q[6:], "geom": "named units"}
    if q.startswith("line="):
        ways = [a for a in search(q[5:], ISO2[i3], 50) if a.get("namedetails", {}).get("name") == q[5:]
                and a["geojson"]["type"] in ("LineString", "MultiLineString")]
        g = gpd.GeoSeries([shape(a["geojson"]) for a in ways], crs=4326).to_crs(6933).union_all().buffer(250)
        inter = shapely.area(shapely.intersection(ue.geometry.values, g))
        return list(ue.index[inter >= 0.05 * g.area]), {"osm": f"{len(ways)} ways", "geom": "line strip"}
    a = search(q, ISO2[i3])
    if a is None:
        return [], {"osm_name": None, "geom": "not found"}
    g = gpd.GeoSeries([shape(a["geojson"])], crs=4326).to_crs(6933)[0]
    meta = {"osm_name": a.get("display_name", "")[:90], "osm": f"{a['osm_type']}/{a['osm_id']}", "geom": g.geom_type}
    if g.geom_type in ("Polygon", "MultiPolygon"):
        inter = shapely.area(shapely.intersection(ue.geometry.values, g))
        inside = inter / shapely.area(ue.geometry.values)
        idx = list(ue.index[inside >= 0.5]) or [ue.index[inter.argmax()]]
        meta["place_share_of_unit"] = round(float(inter[ue.index.get_indexer(idx)].sum() / shapely.area(ue.loc[idx].geometry.values).sum()), 3)
    else:
        idx = list(ue.index[ue.contains(g)])
    return idx, meta


rows = []
for _, p in pd.read_csv(PINS, dtype=str).iterrows():
    idx, metas = [], []
    for q in p.query.split(" | "):
        i, m = resolve(q.strip(), iso[p.economy])
        idx += [x for x in i if x not in idx]
        metas.append(m)
    hit = units.loc[idx]
    rows.append({"economy": p.economy, "place_en": p.place_en, "project_id": p.project_id, "query": p.query,
                 "unit_ids": ";".join(hit.unit_id), "unit_names": "; ".join(hit.name.astype(str) + " (" + hit.cluster_name + ")"),
                 "osm": "; ".join(str(m.get("osm", "")) for m in metas), "geom": "; ".join(m["geom"] for m in metas),
                 "place_share_of_unit": metas[0].get("place_share_of_unit"), "flag": p.flag, "reason": p.reason})
    print(p.economy[:5], "|", p.place_en[:45], "->", rows[-1]["unit_names"][:110], "|", rows[-1]["geom"], flush=True)
t = pd.DataFrame(rows)
OUT.mkdir(parents=True, exist_ok=True)
t.to_csv(OUT / "pins_resolved.csv", index=False)
print((t.unit_ids == "").sum(), "pins resolved to no unit")
