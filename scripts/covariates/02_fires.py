"""Fire covariates for every panel district and city-state, 2005 to 2024 (registration Q12).

python -I scripts/covariates/02_fires.py data/interim/units/units.parquet data/interim/outcomes/weights.parquet data/raw/firms data/final/covariates

Fire detections are the MODIS active fire archive of NASA FIRMS (collection 6.1), read from the yearly all-countries
files that FIRMS publishes without an account. Each yearly zip is downloaded, the detections inside the study region
(85 to 152 E, 16 S to 56 N) are kept with their confidence and type, the zip's SHA-256 is added to firms_sources.csv
and the zip is deleted. The kept detections are saved as data/raw/firms/modis_{year}_region.csv.gz, so a stopped run
resumes.

A detection counts when its confidence is 30 or more and its type is 0 (presumed vegetation fire, which excludes
volcanoes, static land sources such as gas flares and offshore sources). Detections are counted on a 0.05 degree grid,
and a district's count within D km is the sum over the grid cells whose centre lies within D km of the district polygon.
Distances are measured in an azimuthal equidistant projection centred on the district (polygon simplified to 500 m
before buffering).

Writes data/final/covariates/fires.csv (unit_id, year, ln_fire_100km, ln_fire_300km, ln_fire_500km, each ln(1 + count))
and fires_log.json next to it. The 500 km count is used only by the Singapore monthly synthetic control check.
"""
import csv
import datetime
import hashlib
import io
import json
import sys
import time
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyproj
import requests
import shapely
from scipy import sparse

URL = "https://firms.modaps.eosdis.nasa.gov/data/country/zips/modis_{y}_all_countries.zip"
YEARS = range(2005, 2025)
LON0, LON1, LAT0, LAT1, STEP = 85.0, 152.0, -16.0, 56.0, 0.05
NX, NY = round((LON1 - LON0) / STEP), round((LAT1 - LAT0) / STEP)
DIST = (100, 300, 500)
CONF_MIN = 30


def download(y, raw):
    out = raw / f"modis_{y}_region.csv.gz"
    if out.exists():
        return
    z = raw / f"modis_{y}_all_countries.zip"
    h = hashlib.sha256()
    for k in range(5):
        try:
            with requests.get(URL.format(y=y), stream=True, timeout=120) as r:
                r.raise_for_status()
                with open(z, "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
                        h.update(chunk)
            break
        except requests.RequestException as e:
            print(f"  {y} attempt {k + 1} failed: {e}", flush=True)
            h = hashlib.sha256()
            time.sleep(15 * (k + 1))
    else:
        sys.exit(f"could not download {y}")
    keep = []
    with zipfile.ZipFile(z) as zf:
        members = [m for m in zf.namelist() if m.endswith(".csv")]
        for m in members:
            d = pd.read_csv(io.BytesIO(zf.read(m)))
            d = d[d["longitude"].between(LON0, LON1) & d["latitude"].between(LAT0, LAT1)]
            if len(d):
                cols = [c for c in ("latitude", "longitude", "acq_date", "acq_time", "confidence", "type", "satellite") if c in d]
                d = d[cols].copy()
                d["file"] = Path(m).name
                keep.append(d)
    d = pd.concat(keep, ignore_index=True)
    d.to_csv(out, index=False, compression="gzip")
    src = raw / "firms_sources.csv"
    new = not src.exists()
    with open(src, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["file", "url", "sha256", "bytes", "csv_members", "detections_in_region", "read_date"])
        w.writerow([z.name, URL.format(y=y), h.hexdigest(), z.stat().st_size, len(members), len(d),
                    datetime.date.today().isoformat()])
    z.unlink()
    print(f"{y}: {len(d)} detections in the region from {len(members)} files", flush=True)


def grid_counts(raw, log):
    C = np.zeros((NY * NX, len(YEARS)), dtype=np.int32)
    for j, y in enumerate(YEARS):
        d = pd.read_csv(raw / f"modis_{y}_region.csv.gz")
        n0 = len(d)
        d = d.drop_duplicates(["latitude", "longitude", "acq_date", "acq_time", "satellite"])
        ok = d["confidence"] >= CONF_MIN
        if "type" in d:
            ok &= d["type"] == 0
        else:
            log.setdefault("years_without_type", []).append(y)
        d = d[ok]
        ix = np.clip(((d["longitude"] - LON0) / STEP).astype(int), 0, NX - 1)
        iy = np.clip(((d["latitude"] - LAT0) / STEP).astype(int), 0, NY - 1)
        np.add.at(C[:, j], iy.to_numpy() * NX + ix.to_numpy(), 1)
        log.setdefault("detections", {})[y] = dict(in_region=n0, duplicates=n0 - len(ok), counted=int(ok.sum()))
    return C


def buffer_cells(geom, dist_km):
    c = geom.centroid
    to = pyproj.Transformer.from_crs(4326, f"+proj=aeqd +lat_0={c.y} +lon_0={c.x} +units=m", always_xy=True)
    back = pyproj.Transformer.from_crs(to.target_crs, 4326, always_xy=True)
    g = shapely.simplify(shapely.transform(geom, lambda a: np.column_stack(to.transform(a[:, 0], a[:, 1]))), 500)
    out = {}
    for d in dist_km:
        b = shapely.transform(shapely.buffer(g, d * 1000, quad_segs=16),
                              lambda a: np.column_stack(back.transform(a[:, 0], a[:, 1])))
        x0, y0, x1, y1 = b.bounds
        i0, i1 = max(int((x0 - LON0) / STEP), 0), min(int((x1 - LON0) / STEP) + 1, NX)
        j0, j1 = max(int((y0 - LAT0) / STEP), 0), min(int((y1 - LAT0) / STEP) + 1, NY)
        I, J = np.meshgrid(np.arange(i0, i1), np.arange(j0, j1))
        inside = shapely.contains_xy(b, LON0 + (I + 0.5) * STEP, LAT0 + (J + 0.5) * STEP)
        out[d] = (J[inside] * NX + I[inside]).astype(np.int32)
    return out


def main():
    geom_f, weights, raw, out = (Path(a) for a in sys.argv[1:5])
    raw.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    for y in YEARS:
        download(y, raw)
    log = dict(source="NASA FIRMS MODIS C6.1 yearly all-countries archive", confidence_min=CONF_MIN, type=0,
               grid_step_degree=STEP, region=[LON0, LON1, LAT0, LAT1])
    C = grid_counts(raw, log)
    print(f"grid counts done, {time.time() - t0:.0f} s", flush=True)

    ids = pd.read_parquet(weights, columns=["unit_id"])["unit_id"].unique()
    units = gpd.read_parquet(geom_f, columns=["unit_id", "geometry"])
    units = units[units["unit_id"].isin(ids)].set_index("unit_id").loc[sorted(ids)]
    rows = {d: ([], []) for d in DIST}
    for k, (u, geom) in enumerate(units["geometry"].items()):
        for d, idx in buffer_cells(geom, DIST).items():
            rows[d][0].append(np.full(len(idx), k, dtype=np.int32))
            rows[d][1].append(idx)
        if k % 250 == 0:
            print(f"  buffers {k}/{len(units)}, {time.time() - t0:.0f} s", flush=True)
    res = pd.DataFrame({"unit_id": np.repeat(units.index.to_numpy(), len(YEARS)),
                        "year": np.tile(list(YEARS), len(units))})
    for d in DIST:
        r, c = np.concatenate(rows[d][0]), np.concatenate(rows[d][1])
        M = sparse.csr_matrix((np.ones(len(r), dtype=np.int32), (r, c)), shape=(len(units), NY * NX))
        n = np.asarray(M @ C)
        res[f"fire_{d}km"] = n.ravel()
        res[f"ln_fire_{d}km"] = np.log1p(res[f"fire_{d}km"])
        log[f"cells_within_{d}km"] = dict(min=int(np.diff(M.indptr).min()), median=float(np.median(np.diff(M.indptr))))
    log["units"] = len(units)
    log["summary"] = res[[f"fire_{d}km" for d in DIST]].describe().round(1).to_dict()
    res[["unit_id", "year"] + [f"ln_fire_{d}km" for d in DIST]].to_csv(out / "fires.csv", index=False, float_format="%.5f")
    (out / "fires_log.json").write_text(json.dumps(log, indent=2, default=str))
    print(json.dumps(log["summary"], indent=1), f"done in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
