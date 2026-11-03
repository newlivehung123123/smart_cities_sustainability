"""Night-time light (2005 to 2024) and 2015 built-up area for every panel district and city-state (registration Q12,
Q19 and Q20, deviation 2).

python -I scripts/covariates/03_light_built.py data/interim/outcomes/weights.parquet data/raw/ntl data/final/covariates

Night-time light. The registration names the VIIRS annual composites of the Earth Observation Group, which are
distributed only to registered users. The light series used instead is version 10 of the harmonised global night-time
light dataset of Li et al. (2020), on figshare (article 9828827) with no account: DMSP values intercalibrated across
satellites for 2005 to 2013 (Harmonized_DN_NTL_{year}_calDMSP.tif) and VIIRS values converted to the DMSP scale for 2014
to 2024 (Harmonized_DN_NTL_{year}_simVIIRS.tif). Values are digital numbers from 0 to 63 on a 30 arc-second grid. RQ2
uses 2012 to 2024, and the years from 2005 serve the longer check of Q19.
ntl is the mean digital number over the district, each 0.01 degree cell of weights.parquet weighted by its area inside
the district (w_area) and read at the 30 arc-second pixel holding the cell centre.

Built-up area. built is the built-up surface of the district in km2 in 2015, from GHS-BUILT-S R2023A (epoch 2015, 30
arc-second grid in WGS84, Pesaresi and Politis 2023). Each 0.01 degree cell takes the built-up share of the 30
arc-second pixel holding its centre, times the area of the cell inside the district.

Each source file is downloaded to argv[2], its SHA-256 is added to ntl_sources.csv, the values at the cells used are
saved as {stem}.npz, and the file is deleted. Writes data/final/covariates/light.csv (unit_id, year, ntl, and built in
the 2015 row) and light_log.json next to it.
"""
import csv
import datetime
import hashlib
import json
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
import requests
from rasterio.windows import from_bounds

FIGSHARE = "https://api.figshare.com/v2/articles/9828827/files?page_size=100"
BUILT = ("https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_BUILT_S_GLOBE_R2023A/"
         "GHS_BUILT_S_E2015_GLOBE_R2023A_4326_30ss/V1-0/GHS_BUILT_S_E2015_GLOBE_R2023A_4326_30ss_V1_0.zip")
YEARS = range(2005, 2025)
KM_PER_DEG = 111.32


def download(url, dest, raw):
    h = hashlib.sha256()
    for k in range(5):
        try:
            with requests.get(url, stream=True, timeout=120) as r:
                r.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
                        h.update(chunk)
            break
        except requests.RequestException as e:
            print(f"  {dest.name} attempt {k + 1} failed: {e}", flush=True)
            h = hashlib.sha256()
            time.sleep(15 * (k + 1))
    else:
        sys.exit(f"could not download {url}")
    src = raw / "ntl_sources.csv"
    new = not src.exists()
    with open(src, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["file", "url", "sha256", "bytes", "read_date"])
        w.writerow([dest.name, url, h.hexdigest(), dest.stat().st_size, datetime.date.today().isoformat()])


def sample(path, lon, lat):
    """Value of the raster pixel holding each point, read from one window over the points' bounding box."""
    with rasterio.open(path) as r:
        win = from_bounds(lon.min() - 0.01, lat.min() - 0.01, lon.max() + 0.01, lat.max() + 0.01, r.transform)
        win = win.round_offsets().round_lengths()
        a = r.read(1, window=win)
        t = r.window_transform(win)
        nod = r.nodata
    col = np.floor((lon - t.c) / t.a).astype(int)
    row = np.floor((lat - t.f) / t.e).astype(int)
    v = a[row, col].astype("float64")
    if nod is not None:
        v[v == nod] = np.nan
    return v


def main():
    weights, raw, out = (Path(a) for a in sys.argv[1:4])
    raw.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    w = pd.read_parquet(weights, columns=["unit_id", "row", "col", "w_area"])
    lat = -60 + 0.01 * (w["row"].to_numpy() + 0.5)
    lon = -180 + 0.01 * (w["col"].to_numpy() + 0.5)
    t0 = time.time()

    files = {f["name"]: f["download_url"] for f in requests.get(FIGSHARE, timeout=60).json()}
    names = {y: f"Harmonized_DN_NTL_{y}_{'calDMSP' if y <= 2013 else 'simVIIRS'}.tif" for y in YEARS}
    vals = {}
    for y, n in names.items():
        cache = raw / (Path(n).stem + ".npz")
        if not cache.exists():
            dest = raw / n
            download(files[n], dest, raw)
            np.savez_compressed(cache, x=sample(dest, lon, lat).astype("float32"))
            dest.unlink()
            print(f"{n} read, {time.time() - t0:.0f} s", flush=True)
        vals[y] = np.load(cache)["x"].astype("float64")

    cache = raw / "GHS_BUILT_S_E2015_GLOBE_R2023A_4326_30ss_V1_0.npz"
    if not cache.exists():
        dest = raw / Path(BUILT).name
        download(BUILT, dest, raw)
        with zipfile.ZipFile(dest) as zf:
            member = next(m for m in zf.namelist() if m.endswith(".tif"))
        tif = f"/vsizip/{dest}/{member}"
        np.savez_compressed(cache, x=sample(tif, lon, lat).astype("float32"))
        dest.unlink()
        print(f"built-up surface read, {time.time() - t0:.0f} s", flush=True)
    built_m2 = np.load(cache)["x"].astype("float64")
    pixel_km2 = (KM_PER_DEG / 120) ** 2 * np.cos(np.radians(lat))
    cell_km2 = w["w_area"].to_numpy() * (KM_PER_DEG / 100) ** 2  # w_area is coverage times cos(latitude)
    w["built"] = np.clip(built_m2 / 1e6 / pixel_km2, 0, 1) * cell_km2

    rows = []
    for y in YEARS:
        ok = ~np.isnan(vals[y])
        num = pd.Series(vals[y][ok] * w["w_area"].to_numpy()[ok]).groupby(w["unit_id"].to_numpy()[ok]).sum()
        den = pd.Series(w["w_area"].to_numpy()[ok]).groupby(w["unit_id"].to_numpy()[ok]).sum()
        rows.append(pd.DataFrame({"unit_id": num.index, "year": y, "ntl": (num / den).to_numpy()}))
    res = pd.concat(rows, ignore_index=True)
    b = w.groupby("unit_id")["built"].sum().rename("built").reset_index().assign(year=2015)
    res = res.merge(b, on=["unit_id", "year"], how="outer").sort_values(["unit_id", "year"])
    res.to_csv(out / "light.csv", index=False, float_format="%.5f")
    log = dict(ntl_source="Li et al. (2020) harmonised NTL v10, figshare 9828827", ntl_files=names,
               built_source=BUILT, units=int(res["unit_id"].nunique()),
               ntl_zero_district_years=int((res["ntl"] == 0).sum()), ntl_missing=int(res["ntl"].isna().sum()),
               ntl_by_year=res.groupby("year")["ntl"].mean().round(3).to_dict(),
               built_km2=b["built"].describe().round(2).to_dict())
    (out / "light_log.json").write_text(json.dumps(log, indent=2, default=str))
    print(json.dumps(log, indent=1, default=str), f"done in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
