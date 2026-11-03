"""Download the district boundaries and write one GeoParquet per economy and level (dataset plan section 2b).

geoBoundaries gbOpen, pinned to commit 9469f09: the unit level and the cluster level of each economy (ADM2 and ADM1;
the Philippines ADM3 and ADM2; Singapore ADM0). Hong Kong and Macau: OpenStreetMap relations 913110 and 1867188, read
from the OSM API, whose saved copies are kept. Every GeoJSON is hashed, converted to GeoParquet and deleted.
South Korea: the gbOpen ADM2 file (from citypopulation.de) lies about 1 km off the true district outlines (overlap with
the OSM outlines of four Seoul districts 0.42 to 0.57), so it is kept only as a candidate and the units are the OSM
admin_level 6 districts (si, gun and autonomous gu) plus Sejong, listed as subareas of the province relations used by
01b_clusters.py (plus KOR_EXTRA, districts missing from those lists, found by the coverage check) and read from the OSM
API, with gzipped copies kept. Overpass refused or timed out on 1 Nov 2026, so it is not used. Incheon's July 2026 districts are merged back to 2015 extents: Jemulpo-gu with Yeongjong-gu
(together the 2015 Jung-gu and Dong-gu, which cannot be separated again) and Seohae-gu with Geomdan-gu (the 2015 Seo-gu).
Writes boundary_sources.csv (source, licence, year represented, URL, SHA-256 and date read of every file).

argv[1] = data/raw/boundaries, argv[2] = data/interim/units, argv[3] = empty download folder outside the project,
argv[4:] = optional ISO3 codes to rebuild; rows of the other economies already in boundary_sources.csv are kept.
"""
import csv, datetime, gzip, hashlib, json, os, re, subprocess, sys, time
from pathlib import Path

os.environ["OGR_GEOJSON_MAX_OBJ_SIZE"] = "0"  # the Philippine province file holds features over the 200 MB default
import geopandas as gpd  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import shapely  # noqa: E402
from shapely.geometry import LineString
from shapely.ops import polygonize, unary_union

RAW, OUT, DL = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
COMMIT = "9469f09"
GB = f"https://github.com/wmgeolab/geoBoundaries/raw/{COMMIT}/releaseData/gbOpen"
OSM = "https://api.openstreetmap.org/api/0.6/relation"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
TODAY = datetime.date.today().isoformat()
# economy, ISO3, unit level, cluster level
GB_ECON = [("Japan", "JPN", "ADM2", "ADM1"), ("South Korea", "KOR", "ADM2", "ADM1"), ("Taiwan", "TWN", "ADM2", "ADM1"),
           ("Mongolia", "MNG", "ADM2", "ADM1"), ("Brunei", "BRN", "ADM2", "ADM1"), ("Cambodia", "KHM", "ADM2", "ADM1"),
           ("Indonesia", "IDN", "ADM2", "ADM1"), ("Laos", "LAO", "ADM2", "ADM1"), ("Malaysia", "MYS", "ADM2", "ADM1"),
           ("Myanmar", "MMR", "ADM2", "ADM1"), ("Thailand", "THA", "ADM2", "ADM1"), ("Timor-Leste", "TLS", "ADM2", "ADM1"),
           ("Vietnam", "VNM", "ADM2", "ADM1"), ("Philippines", "PHL", "ADM3", "ADM2"), ("Singapore", "SGP", "ADM0", None)]
OSM_ECON = [("Hong Kong", "HKG", "CN-HK", 913110, 225), ("Macau", "MAC", "CN-MO", 1867188, 114)]
OSM_UNITS = {"KOR"}  # gbOpen unit file kept only as a candidate
KOR_PROVINCES = [2297418, 2396450, 2395674, 2297419, 2349984, 2395867, 2306392, 2308426, 2327258, 2327259, 2355168,
                 2304454, 2393403, 2398560, 21039457]  # saved full copies, as in 01b_clusters.py; Sejong has no districts
KOR_EXTRA = [2505634, 8127814]  # Cheorwon-gun and Ulsan Nam-gu, not subareas of their provinces; found by the gap check
KOR_SEJONG, KOR_INCHEON = 2349795, 2297419
KOR_2015 = {"Jung-gu and Dong-gu": ["제물포구", "영종구"], "Seo-gu": ["서해구", "검단구"]}  # Incheon, merged by Korean name
KOR_UNITS_2015 = 228  # 229 units of 2015 (226 si, gun and gu, Jeju-si, Seogwipo-si, Sejong) with Jung-gu and Dong-gu as one
ONLY = set(sys.argv[4:])
COLS = ["economy", "iso3", "level", "role", "file", "n_units", "n_units_metadata", "source", "licence", "year_represented",
        "url", "sha256", "bytes", "read_date"]


def fetch(url, dest):
    if dest.parent != RAW / "meta" and dest.exists() and dest.stat().st_size > 0:  # left by an earlier run
        return dest
    subprocess.run(["curl", "-sSfL", "--compressed", "-A", UA, "-m", "1800", "-o", str(dest), url], check=True)
    return dest


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def clean(gdf):
    """Repair invalid rings and keep only the polygon parts."""
    geom = shapely.make_valid(gdf.geometry.values)
    geom = [g if g.geom_type in ("Polygon", "MultiPolygon")
            else unary_union([p for p in getattr(g, "geoms", []) if p.geom_type in ("Polygon", "MultiPolygon")])
            for g in geom]
    gdf = gdf.set_geometry(gpd.GeoSeries(geom, index=gdf.index, crs=gdf.crs))
    assert gdf.geometry.is_valid.all() and not gdf.geometry.is_empty.any()
    return gdf


def osm_polygon(els, rel):
    """Polygon of one relation from the elements of its full.json."""
    r = next(e for e in els if e["type"] == "relation" and e["id"] == rel)
    nodes = {e["id"]: (e["lon"], e["lat"]) for e in els if e["type"] == "node"}
    ways = {e["id"]: e["nodes"] for e in els if e["type"] == "way"}
    lines = {}
    for m in r["members"]:
        if m["type"] == "way":
            lines.setdefault(m["role"], []).append(LineString([nodes[n] for n in ways[m["ref"]]]))
    assert set(lines) <= {"outer", "inner", "subarea"}, (rel, set(lines))  # a way given the subarea role (Sinan-gun,
    lines.pop("subarea", None)  # relation 5403755) is a tagging slip, not part of the outline; the gap check in korea_units() guards
    geom = unary_union(list(polygonize(unary_union(lines["outer"]))))
    if "inner" in lines:
        geom = geom.difference(unary_union(list(polygonize(unary_union(lines["inner"])))))
    return geom, r


def korea_units():
    """South Korean districts from OSM, merged to 2015 extents in Incheon."""
    d = RAW / "osm" / "korea"
    d.mkdir(parents=True, exist_ok=True)
    listing = d / "subareas.json"
    provinces = {}
    for p in KOR_PROVINCES:
        provinces[p] = json.loads((RAW / "osm" / f"relation_{p}_full.json").read_text())["elements"]
    if not listing.exists():
        ids = [m["ref"] for p in KOR_PROVINCES for e in provinces[p] if e["type"] == "relation" and e["id"] == p
               for m in e["members"] if m["type"] == "relation" and m["role"] == "subarea"]
        els = []
        for k in range(0, len(ids), 100):
            out = subprocess.run(["curl", "-sSf", "-A", UA, "-m", "300", f"{OSM}s.json?relations=" + ",".join(map(str, ids[k:k + 100]))],
                                 capture_output=True, check=True).stdout
            els += json.loads(out)["elements"]
        listing.write_text(json.dumps({"read": TODAY, "elements": els}, ensure_ascii=False))
    rels = sorted({e["id"] for e in json.loads(listing.read_text())["elements"] if e["tags"].get("admin_level") == "6"} |
                  set(KOR_EXTRA)) + [KOR_SEJONG]
    recs, files = [], []
    for rel in rels:
        path = d / f"relation_{rel}_full.json.gz"
        if not path.exists():
            raw = subprocess.run(["curl", "-sSf", "-A", UA, "-m", "600", f"{OSM}/{rel}/full.json"], capture_output=True,
                                 check=True).stdout
            path.write_bytes(gzip.compress(raw, mtime=0))
            time.sleep(1)
        geom, r = osm_polygon(json.loads(gzip.decompress(path.read_bytes()))["elements"], rel)
        recs.append({"rel": rel, "version": r["version"], "name": r["tags"].get("name"),
                     "name_en": r["tags"].get("name:en") or r["tags"].get("name"), "geometry": geom})
        files.append(path)
    g = gpd.GeoDataFrame(recs, crs=4326)
    country = unary_union([osm_polygon(provinces[p], p)[0] for p in KOR_PROVINCES] + [g.geometry.iloc[-1]])
    gaps = gpd.GeoSeries(shapely.get_parts(country.difference(unary_union(g.geometry.values))), crs=4326).to_crs(6933)
    gaps = gaps[gaps.area > 1e6]
    # Province outlines can include coastal sea that district outlines leave out (North Gyeongsang). Land is the gbOpen
    # ADM1 file shrunk by 2 km, which absorbs its 1 km offset; a gap holding more than 1 km2 of it is a missing district.
    land = unary_union(gpd.read_parquet(OUT / "KOR_ADM1.parquet").to_crs(6933).geometry.values).buffer(-2000)
    on_land = gaps.intersection(land).area
    for q, a, l in zip(gaps.to_crs(4326).representative_point(), gaps.area, on_land):
        print(f"KOR: area in no district at {q.x:.4f}, {q.y:.4f}: {a / 1e6:.1f} km2, of which {l / 1e6:.2f} km2 on land", flush=True)
    assert (on_land <= 1e6).all(), "land in no district (add to KOR_EXTRA)"
    incheon, _ = osm_polygon(json.loads((RAW / "osm" / f"relation_{KOR_INCHEON}_full.json").read_text())["elements"], KOR_INCHEON)
    for name, parts in KOR_2015.items():
        k = g.index[g.geometry.representative_point().within(incheon) & g.name.isin(parts)]
        assert len(k) == len(parts), (name, g.loc[k, "name"].tolist())
        merged = {"rel": None, "version": None, "name": None, "name_en": name, "geometry": unary_union(g.geometry[k].values),
                  "id": "OSM-" + "+".join(f"r{int(x)}" for x in g.rel[k])}
        g = pd.concat([g.drop(k), gpd.GeoDataFrame([merged], crs=4326)], ignore_index=True)
    g["id"] = g["id"].fillna("OSM-r" + g.rel.astype("Int64").astype(str)) if "id" in g else "OSM-r" + g.rel.astype(str)
    assert len(g) == KOR_UNITS_2015 and g["id"].is_unique, len(g)
    ea = g.to_crs(6933).geometry
    assert abs(ea.area.sum() - ea.union_all().area) < 1e-4 * ea.area.sum(), "districts overlap"
    out = clean(gpd.GeoDataFrame({"shapeName": g.name_en.values, "shapeID": g["id"].values, "shapeGroup": "KOR",
                                  "shapeType": "ADM2"}, geometry=g.geometry.values, crs=4326))
    h = hashlib.sha256("".join(sha256(p) for p in files).encode()).hexdigest()
    src = (f"OpenStreetMap admin_level 6 relations listed as subareas of the province relations on {json.loads(listing.read_text())['read']}"
           f"{', plus relations ' + ', '.join(map(str, KOR_EXTRA)) if KOR_EXTRA else ''}, plus Sejong (relation {KOR_SEJONG}); versions {min(r['version'] for r in recs)} to {max(r['version'] for r in recs)}; "
           "Incheon merged to 2015 extents (Jemulpo-gu and Yeongjong-gu; Seohae-gu and Geomdan-gu)")
    return out, src, h, sum(p.stat().st_size for p in files)


rows = []
(RAW / "meta").mkdir(parents=True, exist_ok=True)
for econ, iso, unit, cluster in GB_ECON:
    if ONLY and iso not in ONLY:
        continue
    for level, role in [(unit, "unit candidate" if iso in OSM_UNITS else "unit"),
                        (cluster, "cluster candidate")]:  # 01b_clusters.py picks the cluster file
        if level is None:
            continue
        name = f"geoBoundaries-{iso}-{level}"
        meta_path = fetch(f"{GB}/{iso}/{level}/{name}-metaData.json", RAW / "meta" / f"{name}-metaData.json")
        meta = json.loads(meta_path.read_text())
        url = f"{GB}/{iso}/{level}/{name}.geojson"
        gj = fetch(url, DL / f"{name}.geojson")
        g = gpd.read_file(gj)
        assert g.crs.to_epsg() == 4326, name  # feature counts can differ from admUnitCount (Japan 1,742 v 1,745); both are kept
        assert g.shapeID.is_unique
        g = clean(g[["shapeName", "shapeID", "shapeGroup", "shapeType", "geometry"]])
        g.insert(0, "economy", econ)
        g.to_parquet(OUT / f"{iso}_{level}.parquet", compression="zstd")
        rows.append({"economy": econ, "iso3": iso, "level": level, "role": role, "file": f"{iso}_{level}.parquet", "n_units": len(g),
                     "n_units_metadata": int(meta["admUnitCount"]),
                     "source": meta["boundarySource"], "licence": meta["boundaryLicense"],
                     "year_represented": meta["boundaryYear"], "url": url, "sha256": sha256(gj),
                     "bytes": gj.stat().st_size, "read_date": TODAY})
        gj.unlink()
        print(econ, level, len(g), meta["boundaryLicense"], flush=True)
    if iso == "KOR":
        g, src, h, size = korea_units()
        g.insert(0, "economy", econ)
        g.to_parquet(OUT / "KOR_ADM2_osm.parquet", compression="zstd")
        rows.append({"economy": econ, "iso3": iso, "level": "ADM2", "role": "unit", "file": "KOR_ADM2_osm.parquet",
                     "n_units": len(g), "n_units_metadata": KOR_UNITS_2015, "source": src,
                     "licence": "Open Data Commons Open Database License 1.0", "year_represented": "2015",
                     "url": f"{OSM}/{{id}}/full.json", "sha256": h, "bytes": size, "read_date": TODAY})
        print(econ, "OSM districts", len(g), flush=True)

(RAW / "osm").mkdir(exist_ok=True)
for econ, iso, code, rel, version in OSM_ECON:
    if ONLY and iso not in ONLY:
        continue
    path = fetch(f"{OSM}/{rel}/full.json", RAW / "osm" / f"relation_{rel}_full.json")
    els = json.loads(path.read_text())["elements"]
    r = next(e for e in els if e["type"] == "relation" and e["id"] == rel)
    assert r["version"] == version and r["tags"]["ISO3166-2"] == code, r["tags"]
    nodes = {e["id"]: (e["lon"], e["lat"]) for e in els if e["type"] == "node"}
    ways = {e["id"]: e["nodes"] for e in els if e["type"] == "way"}
    lines = {}
    for m in r["members"]:
        if m["type"] == "way":
            lines.setdefault(m["role"], []).append(LineString([nodes[n] for n in ways[m["ref"]]]))
    assert set(lines) <= {"outer", "inner"}, set(lines)
    geom = unary_union(list(polygonize(unary_union(lines["outer"]))))
    if "inner" in lines:
        geom = geom.difference(unary_union(list(polygonize(unary_union(lines["inner"])))))
    g = clean(gpd.GeoDataFrame({"economy": [econ], "shapeName": [r["tags"]["name:en"]], "shapeID": [f"OSM-r{rel}"],
                                "shapeGroup": [iso], "shapeType": ["ADM0"]}, geometry=[geom], crs=4326))
    g.to_parquet(OUT / f"{iso}_ADM0.parquet", compression="zstd")
    rows.append({"economy": econ, "iso3": iso, "level": "ADM0", "role": "unit", "file": f"{iso}_ADM0.parquet", "n_units": 1,
                 "n_units_metadata": 1,
                 "source": f"OpenStreetMap relation {rel} version {version} ({r['timestamp']})",
                 "licence": "Open Data Commons Open Database License 1.0", "year_represented": r["timestamp"][:4],
                 "url": f"{OSM}/{rel}/full.json", "sha256": sha256(path), "bytes": path.stat().st_size,
                 "read_date": TODAY})
    print(econ, "OSM", rel, "version", version, flush=True)

if ONLY:  # keep the rows of the economies not rebuilt, in their order
    old = list(csv.DictReader(open(RAW / "boundary_sources.csv", encoding="utf-8")))
    rows = [r for r in old if r["iso3"] not in ONLY] + rows
    order = [e[1] for e in GB_ECON] + [e[1] for e in OSM_ECON]
    rows.sort(key=lambda r: order.index(r["iso3"]))
with open(RAW / "boundary_sources.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, COLS)
    w.writeheader()
    w.writerows(rows)
print(len(rows), "files")
