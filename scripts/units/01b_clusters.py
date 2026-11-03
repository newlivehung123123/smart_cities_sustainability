"""Choose the cluster (ADM1) file of each economy by how cleanly it nests the district units (dataset plan section 2b).

Several gbOpen ADM1 files come from coarser sources than the unit files they should contain (South Korea from Natural
Earth, Vietnam from a 2008 Wikipedia map), so units straddle provinces they do not belong to. For every economy with a
cluster level, this script scores each candidate cluster file and keeps the best:
  - gbOpen ADM1 (Philippines ADM2), written by 01_boundaries.py;
  - gbHumanitarian ADM1 at the same geoBoundaries commit, where one exists;
  - South Korea only: the 2015 provinces rebuilt from OpenStreetMap. OSM now holds the July 2026 Jeonnam-Gwangju merger
    and Daegu with Gunwi-gun (moved from North Gyeongsang on 1 July 2023), so Gwangju is rebuilt as the union of its five
    districts, South Jeolla as the merged province minus Gwangju, and Gunwi-gun is moved back to North Gyeongsang.
Each unit's share is the largest part of its area inside one cluster. A unit is ambiguous when its second largest part
is more than half its largest. Candidates are ranked by ambiguous units, then units below a 0.9 share, then units in no
cluster, then the median share; ties keep gbOpen. Areas are on EPSG:6933.

argv[1] = data/raw/boundaries, argv[2] = data/interim/units, argv[3] = download folder outside the project.
Writes {ISO}_ADM1_hum.parquet and KOR_ADM1_osm2015.parquet into argv[2], the saved OSM relations into argv[1]/osm, and
cluster_sources.csv (every candidate, its scores, provenance and whether it was chosen) into argv[1].
"""
import csv, datetime, hashlib, json, os, subprocess, sys
from pathlib import Path

os.environ["OGR_GEOJSON_MAX_OBJ_SIZE"] = "0"
import geopandas as gpd  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import shapely  # noqa: E402
from shapely.geometry import LineString  # noqa: E402
from shapely.ops import polygonize, unary_union  # noqa: E402

RAW, OUT, DL = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
COMMIT = "9469f09"
GBH = f"https://github.com/wmgeolab/geoBoundaries/raw/{COMMIT}/releaseData/gbHumanitarian"
OSM = "https://api.openstreetmap.org/api/0.6/relation"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
TODAY = datetime.date.today().isoformat()
EA = 6933
HUMANITARIAN = ["JPN", "MNG", "KHM", "IDN", "LAO", "MYS", "THA", "TLS", "VNM"]  # gbHumanitarian ADM1 at the commit
# South Korea: OSM relation, version read, 2015 code and English name
KOR_PROVINCES = [(2297418, 150, "KR-11", "Seoul"), (2396450, 83, "KR-26", "Busan"), (2395674, 58, "KR-27", "Daegu"),
                 (2297419, 117, "KR-28", "Incheon"), (2349984, 54, "KR-30", "Daejeon"), (2395867, 47, "KR-31", "Ulsan"),
                 (2349795, 54, "KR-50", "Sejong"), (2306392, 227, "KR-41", "Gyeonggi"), (2308426, 104, "KR-42", "Gangwon"),
                 (2327258, 83, "KR-43", "North Chungcheong"), (2327259, 110, "KR-44", "South Chungcheong"),
                 (2355168, 75, "KR-45", "North Jeolla"), (2304454, 147, "KR-47", "North Gyeongsang"),
                 (2393403, 113, "KR-48", "South Gyeongsang"), (2398560, 45, "KR-49", "Jeju")]
KOR_MERGED = (21039457, 7)  # Jeonnam-Gwangju Special Metropolitan City, from 1 July 2026
GWANGJU_DISTRICTS = [(4162635, 20), (7348583, 24), (7348741, 17), (7348758, 19), (7348759, 18)]  # Dong, Buk, Nam, Gwangsan, Seo
GUNWI = (7816959, 15)
COLS = ["economy", "iso3", "level", "candidate", "chosen", "file", "n_clusters", "median_share", "p5_share",
        "units_below_0.9", "units_below_0.5", "ambiguous", "unmatched", "source", "licence", "year_represented", "url",
        "sha256", "bytes", "read_date"]


def fetch(url, dest):
    if dest.exists() and dest.stat().st_size > 0:  # left by an earlier run, or the saved OSM copy
        return dest
    subprocess.run(["curl", "-sSfL", "--compressed", "-A", UA, "-m", "1800", "-o", str(dest), url], check=True)
    return dest


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def polygonal(geoms):
    """make_valid, keeping only the polygon parts."""
    out = shapely.make_valid(np.asarray(geoms))
    bad = ~np.isin(shapely.get_type_id(out), [3, 6])
    out[bad] = [unary_union([p for p in shapely.get_parts(g) if p.geom_type in ("Polygon", "MultiPolygon")])
                for g in out[bad]]
    assert shapely.is_valid(out).all() and not shapely.is_empty(out).any()
    return out


def osm_relation(rel, version):
    """Polygon of one OSM relation from its saved full copy, with the version checked."""
    path = fetch(f"{OSM}/{rel}/full.json", RAW / "osm" / f"relation_{rel}_full.json")
    els = json.loads(path.read_text())["elements"]
    r = next(e for e in els if e["type"] == "relation" and e["id"] == rel)
    assert r["version"] == version, (rel, r["version"])
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
    return geom, r, path


def nesting(units, clusters):
    """Largest share of each unit inside one cluster, and whether the second largest exceeds half of it."""
    a, c = polygonal(units.to_crs(EA).geometry.values), polygonal(clusters.to_crs(EA).geometry.values)
    i, j = shapely.STRtree(c).query(a, predicate="intersects")
    ov = pd.DataFrame({"i": i, "km2": shapely.area(shapely.intersection(a[i], c[j])) / 1e6})
    ov = ov.sort_values(["i", "km2"], ascending=[True, False])
    first = ov.drop_duplicates("i").set_index("i").km2.reindex(range(len(a)), fill_value=0.0).values
    second = ov[ov.duplicated("i")].drop_duplicates("i").set_index("i").km2.reindex(range(len(a)), fill_value=0.0).values
    share = first / (shapely.area(a) / 1e6)
    return {"n_clusters": len(c), "median_share": round(float(np.median(share)), 4),
            "p5_share": round(float(np.percentile(share, 5)), 4), "units_below_0.9": int((share < 0.9).sum()),
            "units_below_0.5": int((share < 0.5).sum()), "ambiguous": int((second > 0.5 * first).sum()),
            "unmatched": int((first == 0).sum())}


def korea_2015():
    """The 17 South Korean provinces as they stood in 2015, from OSM."""
    geoms, recs, files = {}, [], []
    for rel, version, code, name in KOR_PROVINCES:
        geoms[code], r, path = osm_relation(rel, version)
        recs.append((rel, version, r["timestamp"])); files.append(path)
    merged, r, path = osm_relation(*KOR_MERGED)
    recs.append((KOR_MERGED[0], KOR_MERGED[1], r["timestamp"])); files.append(path)
    parts = []
    for rel, version in GWANGJU_DISTRICTS:
        g, r, path = osm_relation(rel, version)
        parts.append(g); recs.append((rel, version, r["timestamp"])); files.append(path)
    gwangju = unary_union(parts)
    gunwi, r, path = osm_relation(*GUNWI)
    recs.append((GUNWI[0], GUNWI[1], r["timestamp"])); files.append(path)
    assert gwangju.difference(merged).area < 1e-6 * gwangju.area and gunwi.difference(geoms["KR-27"]).area < 1e-6 * gunwi.area
    geoms["KR-29"], geoms["KR-46"] = gwangju, merged.difference(gwangju)
    geoms["KR-27"], geoms["KR-47"] = geoms["KR-27"].difference(gunwi), unary_union([geoms["KR-47"], gunwi])
    names = {code: name for _, _, code, name in KOR_PROVINCES} | {"KR-29": "Gwangju", "KR-46": "South Jeolla"}
    codes = sorted(geoms)
    g = gpd.GeoDataFrame({"economy": "South Korea", "shapeName": [names[k] for k in codes],
                          "shapeID": [f"OSM-{k}-2015" for k in codes], "shapeGroup": "KOR", "shapeType": "ADM1"},
                         geometry=list(polygonal([geoms[k] for k in codes])), crs=4326)
    km2 = dict(zip(codes, shapely.area(polygonal(g.to_crs(EA).geometry.values)) / 1e6))
    print(f"KOR 2015 rebuild: Gwangju {km2['KR-29']:.0f} km2, Gunwi-gun {shapely.area(polygonal(gpd.GeoSeries([gunwi], crs=4326).to_crs(EA).values))[0] / 1e6:.0f} km2", flush=True)
    h = hashlib.sha256("".join(sha256(p) for p in files).encode()).hexdigest()
    src = ("OpenStreetMap relations " + "; ".join(f"{rel} v{v} ({t})" for rel, v, t in recs) +
           ". Gwangju = union of its five districts; South Jeolla = Jeonnam-Gwangju minus Gwangju; Gunwi-gun moved from Daegu to North Gyeongsang")
    return g, {"source": src, "licence": "Open Data Commons Open Database License 1.0", "year_represented": "2015",
               "url": f"{OSM}/{{id}}/full.json", "sha256": h, "bytes": sum(p.stat().st_size for p in files)}


src = pd.read_csv(RAW / "boundary_sources.csv")
rows = []
for iso, sel in src.groupby("iso3", sort=False):
    unit = sel[sel.role == "unit"].iloc[0]
    if (sel.role == "cluster candidate").sum() == 0:
        continue
    gb = sel[sel.role == "cluster candidate"].iloc[0]
    units = gpd.read_parquet(OUT / unit.file)
    cands = [("gbOpen", gb.file, gb[["source", "licence", "year_represented", "url", "sha256", "bytes",
                                                      "read_date"]].to_dict())]
    if iso in HUMANITARIAN:
        name = f"geoBoundaries-{iso}-ADM1"
        meta = json.loads(fetch(f"{GBH}/{iso}/ADM1/{name}-metaData.json", DL / f"{name}-metaData.json").read_text())
        url = f"{GBH}/{iso}/ADM1/{name}.geojson"
        gj = DL / f"{iso}-ADM1.geojson"  # name of the copies left by the nesting probe
        fetch(url, gj)
        h = gpd.read_file(gj)
        assert h.crs.to_epsg() == 4326 and h.shapeID.is_unique, iso
        h = h[["shapeName", "shapeID", "shapeGroup", "shapeType", "geometry"]]
        h = h.set_geometry(gpd.GeoSeries(polygonal(h.geometry.values), index=h.index, crs=4326))
        h.insert(0, "economy", unit.economy)
        h.to_parquet(OUT / f"{iso}_ADM1_hum.parquet", compression="zstd")
        cands.append(("gbHumanitarian", f"{iso}_ADM1_hum.parquet",
                      {"source": meta["boundarySource"], "licence": meta["boundaryLicense"],
                       "year_represented": meta["boundaryYear"], "url": url, "sha256": sha256(gj),
                       "bytes": gj.stat().st_size, "read_date": TODAY}))
    if iso == "KOR":
        k, prov = korea_2015()
        k.to_parquet(OUT / "KOR_ADM1_osm2015.parquet", compression="zstd")
        cands.append(("OSM 2015 rebuild", "KOR_ADM1_osm2015.parquet", prov | {"read_date": TODAY}))
    scored = []
    for cand, file, prov in cands:
        s = nesting(units, gpd.read_parquet(OUT / file))
        scored.append({"economy": unit.economy, "iso3": iso, "level": gb.level, "candidate": cand, "file": file} | s | prov)
    order = sorted(range(len(scored)), key=lambda n: (scored[n]["ambiguous"], scored[n]["units_below_0.9"],
                                                       scored[n]["unmatched"], -scored[n]["median_share"], n))
    for n, s in enumerate(scored):
        s["chosen"] = n == order[0]
        print(f"{iso} {s['candidate']:16s} clusters {s['n_clusters']:3d} median {s['median_share']:.4f} "
              f"below 0.9 {s['units_below_0.9']:3d} ambiguous {s['ambiguous']:2d} unmatched {s['unmatched']}"
              f"{'  <- chosen' if s['chosen'] else ''}", flush=True)
    rows += scored

with open(RAW / "cluster_sources.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, COLS)
    w.writeheader()
    w.writerows(rows)
print(sum(r["chosen"] for r in rows), "economies with a chosen cluster file")
