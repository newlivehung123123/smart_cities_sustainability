"""Build the 2015 population weights on the 0.01 degree outcome grid, and the 2015 population of every urban unit and
city-state with the share living in urban centre cells (dataset plan section 2b).

GHS-POP R2023A, 2015 epoch, 3 arc-second tiles in WGS84. Only tiles that meet an urban unit or a city-state (buffered by
0.011 degree, so that every 0.01 degree cell touching such a unit is complete) are fetched. Each tile is read in strips
inside its zip:
- cells below zero are set to zero and counted;
- a cell is inside an urban centre if its centre falls in a 2015 urban centre polygon, and belongs to the unit whose
  polygon holds its centre; unit population and urban centre population are summed at 3 arc-seconds;
- both layers are summed onto the 0.01 degree grid. GHS-POP cell centres sit on multiples of 1/1200 degree and the
  0.01 degree cell edges on multiples of 12 of them, so each 0.01 degree cell takes its 11 by 11 inner cells in full,
  half of each edge cell and a quarter of each corner cell.
Each tile's sums are saved to the download folder before the tile is deleted, so a stopped run resumes where it left off.

Writes data/interim/ghs_pop_2015_001deg.tif (band 1 all population, band 2 population in urban centre cells; cells that
draw on a tile that exists but was not fetched are missing), adds the tiles to data/raw/ghsl/ghsl_sources.csv and writes
data/final/units.csv (one row per unit, no geometry).

argv[1] = data/interim/units, argv[2] = data/raw/ghsl, argv[3] = data/interim, argv[4] = data/final,
argv[5] = empty download folder outside the project.
"""
import csv, datetime, hashlib, re, subprocess, sys, zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import shapely
from rasterio.features import rasterize
from rasterio.transform import from_origin
from rasterio.windows import Window
from scipy import sparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch import UA, fetch_parallel  # noqa: E402

UNITS, RAW, INTERIM, FINAL, DL = (Path(a) for a in sys.argv[1:6])
BASE = ("https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_GLOBE_R2023A/"
        "GHS_POP_E2015_GLOBE_R2023A_4326_3ss/V1-0/tiles/")
NAME = "GHS_POP_E2015_GLOBE_R2023A_4326_3ss_V1_0_R{r}_C{c}"
STRIP = 1280  # rows per read, five 256-row TIFF blocks
TODAY = datetime.date.today().isoformat()


def tile_box(r, c):
    """Nominal tile extent in 1/1200 degree units (left, bottom, right, top); checked against each file's transform."""
    left, top = -216000 + 12000 * (c - 1) - 9.5, 106920 - 12000 * (r - 1) - 0.5
    return left, top - 12000, left + 12000, top


def weights(g, k0, nk):
    """Sparse (len(g), nk) matrix sending each 3 arc-second centre index g to the 0.01 degree cells k0..k0+nk-1."""
    k, inner = g // 12, g % 12 != 0
    rows = np.r_[np.arange(len(g)), np.flatnonzero(~inner)]
    cols = np.r_[k, k[~inner] - 1] - k0
    vals = np.r_[np.where(inner, 1.0, 0.5), np.full((~inner).sum(), 0.5)]
    assert cols.min() >= 0 and cols.max() < nk
    return sparse.csr_matrix((vals, (rows, cols)), shape=(len(g), nk))


def centre_index(origin, step, n):
    g = (origin + (np.arange(n) + 0.5) * step) * 1200
    assert np.abs(g - np.round(g)).max() < 0.01
    return np.round(g).astype(np.int64)


units = gpd.read_parquet(UNITS / "units.parquet")
need = units[units.urban | units.city_state].reset_index(drop=True)
need_geom = need.geometry.values
need_tree = shapely.STRtree(need_geom)
uc_geom = gpd.read_parquet(UNITS / "urban_centres_2015.parquet").geometry.values
uc_tree = shapely.STRtree(uc_geom)

index = subprocess.run(["curl", "-sSfL", "-A", UA, "-m", "120", BASE], capture_output=True, text=True, check=True).stdout
exists = sorted({(int(r), int(c)) for r, c in re.findall(r"_R(\d+)_C(\d+)\.zip", index)})
assert len(exists) == 348, len(exists)
tiles = [(r, c) for r, c in exists if len(need_tree.query(shapely.box(*(v / 1200 for v in tile_box(r, c))),
                                                          predicate="dwithin", distance=0.011))]
skipped = [(r, c) for r, c in exists if (r, c) not in tiles]
print(len(tiles), "tiles to fetch:", " ".join(f"R{r}_C{c}" for r, c in tiles), flush=True)

# 0.01 degree accumulation grid over the fetched tiles: kx, ky index cells [0.01 k, 0.01 (k + 1)]
boxes = np.array([tile_box(r, c) for r, c in tiles])
kx0, kx1 = int(np.floor(boxes[:, 0].min() / 12)) - 1, int(np.floor(boxes[:, 2].max() / 12))
ky0, ky1 = int(np.floor(boxes[:, 1].min() / 12)) - 1, int(np.floor(boxes[:, 3].max() / 12))
nkx, nky = kx1 - kx0 + 1, ky1 - ky0 + 1
print("grid", nky, "rows by", nkx, "columns", flush=True)


def process(r, c, z):
    """Sum one tile; returns the saved npz path."""
    tif = next(n for n in zipfile.ZipFile(z).namelist() if n.endswith(".tif"))
    unit_pop, unit_uc = np.zeros(len(need) + 1), np.zeros(len(need) + 1)
    raw_total, n_neg = 0.0, 0
    with rasterio.open(f"/vsizip/{z}/{tif}") as src:
        t = src.transform
        assert src.count == 1 and src.shape == (12000, 12000) and abs(t.a * 1200 - 1) < 1e-6 and abs(t.e + t.a) < 1e-12  # pixel sizes differ from 1/1200 by about 3e-12 degrees; centres are checked below
        gx, gy_all = centre_index(t.c, t.a, src.width), -centre_index(-t.f, t.a, src.height)
        nb = tile_box(r, c)
        assert (gx[0], gx[-1], gy_all[-1], gy_all[0]) == (nb[0] + 0.5, nb[2] - 0.5, nb[1] + 0.5, nb[3] - 0.5), (r, c, nb)
        # this tile's own block of the 0.01 degree grid
        kx_lo, ky_lo = gx.min() // 12 - 1, gy_all.min() // 12 - 1
        nkx_t, nky_t = gx.max() // 12 - kx_lo + 1, gy_all.max() // 12 - ky_lo + 1
        acc_pop, acc_uc = np.zeros((nky_t, nkx_t)), np.zeros((nky_t, nkx_t))
        wx = weights(gx, kx_lo, nkx_t)
        for row0 in range(0, src.height, STRIP):
            h = min(STRIP, src.height - row0)
            win = Window(0, row0, src.width, h)
            p = src.read(1, window=win)
            assert np.isfinite(p).all()
            neg = p < 0
            n_neg += int(neg.sum())
            p[neg] = 0.0
            raw_total += p.sum()
            gy = gy_all[row0:row0 + h]
            wt = src.window_transform(win)
            strip = shapely.box(wt.c, wt.f - h * t.a, wt.c + src.width * t.a, wt.f)
            hit = uc_tree.query(strip, predicate="intersects")
            inuc = (rasterize(((g, 1) for g in uc_geom[hit]), out_shape=p.shape, transform=wt, fill=0, dtype="uint8")
                    if len(hit) else np.zeros(p.shape, "uint8"))
            pu = p * inuc
            hit = need_tree.query(strip, predicate="intersects")
            if len(hit):
                uid = rasterize(((need_geom[i], i + 1) for i in hit), out_shape=p.shape, transform=wt, fill=0,
                                dtype="int32").ravel()
                unit_pop += np.bincount(uid, weights=p.ravel(), minlength=len(need) + 1)
                unit_uc += np.bincount(uid, weights=pu.ravel(), minlength=len(need) + 1)
            wy = weights(gy, ky_lo, nky_t)
            acc_pop += wy.T @ (wx.T @ p.T).T  # sparse products only: rows by 0.01 degree, then columns
            acc_uc += wy.T @ (wx.T @ pu.T).T
    assert abs(acc_pop.sum() - raw_total) <= 1e-9 * max(raw_total, 1.0), (acc_pop.sum(), raw_total)
    out = DL / f"R{r}_C{c}.npz"
    np.savez_compressed(out, r0=ky_lo - ky0, c0=kx_lo - kx0, pop=acc_pop, uc=acc_uc,
                        unit_pop=unit_pop, unit_uc=unit_uc, raw_total=raw_total, n_neg=n_neg,
                        sha256=hashlib.sha256(z.read_bytes()).hexdigest(), bytes=z.stat().st_size, tif=tif)
    z.unlink()
    print(f"R{r}_C{c}: population {raw_total:,.0f}, cells below zero {n_neg}", flush=True)
    return out


def download(r, c):
    return fetch_parallel(BASE + NAME.format(r=r, c=c) + ".zip", DL / (NAME.format(r=r, c=c) + ".zip"), parts=12)


todo = [(r, c) for r, c in tiles if not (DL / f"R{r}_C{c}.npz").exists()]
with ThreadPoolExecutor(2) as pool:
    jobs = {k: pool.submit(download, *t) for k, t in enumerate(todo[:2])}
    for k, (r, c) in enumerate(todo):
        z = jobs.pop(k).result()
        if k + 2 < len(todo):
            jobs[k + 2] = pool.submit(download, *todo[k + 2])
        process(r, c, z)

# assemble
grid_pop, grid_uc = np.zeros((nky, nkx)), np.zeros((nky, nkx))
unit_pop, unit_uc = np.zeros(len(need) + 1), np.zeros(len(need) + 1)
records, raw_total, n_neg = [], 0.0, 0
for r, c in tiles:
    d = np.load(DL / f"R{r}_C{c}.npz")
    r0, c0 = int(d["r0"]), int(d["c0"])
    grid_pop[r0:r0 + d["pop"].shape[0], c0:c0 + d["pop"].shape[1]] += d["pop"]
    grid_uc[r0:r0 + d["uc"].shape[0], c0:c0 + d["uc"].shape[1]] += d["uc"]
    unit_pop += d["unit_pop"]
    unit_uc += d["unit_uc"]
    raw_total += float(d["raw_total"])
    n_neg += int(d["n_neg"])
    name = NAME.format(r=r, c=c) + ".zip"
    records.append({"file": name, "use": "2015 population, 3 arc-second tile (" + str(d["tif"]) + ")",
                    "licence": "CC BY 4.0 (European Union)", "url": BASE + name, "sha256": str(d["sha256"]),
                    "bytes": int(d["bytes"]), "read_date": TODAY})
assert abs(grid_pop.sum() - raw_total) <= 1e-9 * raw_total
print(f"{len(tiles)} tiles, population {raw_total:,.0f}, cells below zero {n_neg}", flush=True)

# grid rows run north to south: row i holds ky = ky1 - i
grid_pop, grid_uc = grid_pop[::-1], grid_uc[::-1]
missing = np.zeros((nky, nkx), bool)
for r, c in skipped:  # tiles that exist but were not fetched leave their 0.01 degree cells incomplete
    left, bottom, right, top = tile_box(r, c)
    a, b = int(np.floor(left / 12)) - kx0, int(np.floor(right / 12)) - kx0
    lo, hi = int(np.floor(bottom / 12)) - ky0, int(np.floor(top / 12)) - ky0
    if b < 0 or a >= nkx or hi < 0 or lo >= nky:
        continue
    missing[nky - 1 - min(hi, nky - 1):nky - max(lo, 0), max(a, 0):min(b, nkx - 1) + 1] = True
grid_pop[missing] = np.nan
grid_uc[missing] = np.nan
out = INTERIM / "ghs_pop_2015_001deg.tif"
profile = {"driver": "GTiff", "height": nky, "width": nkx, "count": 2, "dtype": "float32", "crs": "EPSG:4326",
           "transform": from_origin(kx0 * 0.01, (ky1 + 1) * 0.01, 0.01, 0.01), "nodata": np.nan, "compress": "deflate",
           "predictor": 3, "tiled": True, "blockxsize": 512, "blockysize": 512}
with rasterio.open(out, "w", **profile) as dst:
    dst.write(grid_pop.astype("float32"), 1)
    dst.write(grid_uc.astype("float32"), 2)
    dst.set_band_description(1, "GHS-POP R2023A 2015 population per 0.01 degree cell")
    dst.set_band_description(2, "of which in 2015 urban centre cells (GHS-SMOD R2023A class 30)")
print(out.name, f"{out.stat().st_size / 1e6:.0f} MB; missing cells {int(missing.sum())}", flush=True)

src = RAW / "ghsl_sources.csv"
rows = {r["file"]: r for r in csv.DictReader(open(src, encoding="utf-8"))} if src.exists() else {}
rows.update({r["file"]: r for r in records})
with open(src, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, list(records[0]))
    w.writeheader()
    w.writerows(rows.values())

# unit table
need["pop2015"] = unit_pop[1:]
need["pop2015_uc"] = unit_uc[1:]
t = units.drop(columns="geometry").merge(need[["unit_id", "pop2015", "pop2015_uc"]], on="unit_id", how="left")
t["uc_pop_share"] = t.pop2015_uc / t.pop2015
t["urban_city_rule"] = (t.uc_pop_share >= 0.5).where(t.pop2015.notna())
panel = t.urban & ~t.city_state
t.loc[panel, "size_group"] = pd.qcut(t.loc[panel, "pop2015"], 4, labels=[1, 2, 3, 4]).astype(int)
t["size_group"] = t.size_group.astype("Int64")
t.to_csv(FINAL / "units.csv", index=False, float_format="%.6g")
print(t[t.city_state][["economy", "area_km2", "pop2015", "uc_pop_share"]].to_string(index=False))
print(int(panel.sum()), "urban units;", int(t.urban_city_rule.fillna(False).sum()), "meet the city rule;",
      "size group bounds", t[panel].groupby("size_group").pop2015.agg(["min", "max"]).round(0).values.tolist())
