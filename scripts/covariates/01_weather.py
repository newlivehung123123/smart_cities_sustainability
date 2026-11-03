"""Annual weather covariates for every panel district and city-state, 2005 to 2024 (registration Q12, deviation 1).

python -I scripts/covariates/01_weather.py data/interim/outcomes/weights.parquet data/raw/terraclimate data/final/covariates

The registration names ERA5-Land. ERA5-Land is distributed only to registered Copernicus users, so the weather
covariates come from TerraClimate (Abatzoglou et al., 2018), a monthly 1/24 degree grid that needs no account. The yearly
files are read over OPeNDAP from the University of Idaho THREDDS server, one request per variable and year covering the
study region.

Variables, from the monthly values of each year:
- t2m: mean of (tmax + tmin) / 2 over the 12 months, degrees C;
- tp: sum of monthly precipitation (ppt), mm;
- wind10: mean of monthly wind speed at 10 m (ws), m/s.

Each 0.01 degree cell of weights.parquet falls in one TerraClimate cell, so a district value is the mean of the
TerraClimate cells weighted by the 2015 population (w_pop) of the 0.01 degree cells inside the district. Cells that
TerraClimate records as water are excluded and the weights of the remaining cells are rescaled. A district with no
land cell takes the nearest land cell to its population-weighted centre; those districts are listed in
weather_log.json.

The values at the cells used are saved to data/raw/terraclimate/{var}_{year}.npz, so a stopped run resumes.
Writes data/final/covariates/weather.csv (unit_id, year, t2m, tp, wind10) and weather_log.json next to it.
"""
import json
import sys
import time
from pathlib import Path

import netCDF4
import numpy as np
import pandas as pd

URL = "http://thredds.northwestknowledge.net:8080/thredds/dodsC/TERRACLIMATE_ALL/data/TerraClimate_{v}_{y}.nc"
VARS = ("tmax", "tmin", "ppt", "ws")
YEARS = range(2005, 2025)
RES = 24  # cells per degree


def fetch(v, y, r0, r1, c0, c1, tries=5):
    for k in range(tries):
        try:
            with netCDF4.Dataset(URL.format(v=v, y=y)) as d:
                a = d[v][:, r0:r1, c0:c1]
            return np.ma.filled(a.astype("float64"), np.nan)
        except OSError as e:
            print(f"  {v} {y} attempt {k + 1} failed: {e}", flush=True)
            time.sleep(10 * (k + 1))
    sys.exit(f"could not read {v} {y}")


def main():
    weights, raw, out = (Path(a) for a in sys.argv[1:4])
    raw.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    w = pd.read_parquet(weights, columns=["unit_id", "row", "col", "w_pop"])
    lat = -60 + 0.01 * (w["row"].to_numpy() + 0.5)
    lon = -180 + 0.01 * (w["col"].to_numpy() + 0.5)
    w["tr"] = np.floor((90 - lat) * RES).astype(int)
    w["tc"] = np.floor((lon + 180) * RES).astype(int)
    r0, r1, c0, c1 = w["tr"].min() - 24, w["tr"].max() + 25, w["tc"].min() - 24, w["tc"].max() + 25
    g = w.groupby(["unit_id", "tr", "tc"], as_index=False)["w_pop"].sum()

    # land mask from the first file, then the nearest land cell for districts with no land cell of their own
    first = fetch(VARS[0], YEARS[0], r0, r1, c0, c1)
    land = ~np.isnan(first).all(axis=0)
    g["land"] = land[g["tr"] - r0, g["tc"] - c0]
    has_land = g[g["land"]].groupby("unit_id")["w_pop"].sum() > 0
    lacking = sorted(set(g["unit_id"]) - set(has_land[has_land].index))
    lr, lc = np.nonzero(land)
    fallback = {}
    for u in lacking:
        x = g[g["unit_id"] == u]
        wt = x["w_pop"].to_numpy() if x["w_pop"].sum() > 0 else np.ones(len(x))
        cr, cc = np.average(x["tr"], weights=wt) - r0, np.average(x["tc"], weights=wt) - c0
        k = np.argmin((lr - cr) ** 2 + ((lc - cc) * np.cos(np.radians(90 - (cr + r0 + 0.5) / RES))) ** 2)
        fallback[u] = (int(lr[k] + r0), int(lc[k] + c0))
    g = g[g["land"]]
    if fallback:
        fb = pd.DataFrame([(u, r, c, 1.0, True) for u, (r, c) in fallback.items()], columns=g.columns)
        g = pd.concat([g[~g["unit_id"].isin(fallback)], fb], ignore_index=True)
    g = g.astype({"tr": int, "tc": int, "w_pop": float})
    # districts with land cells but no population in them use equal weights on those cells
    nopop = g.groupby("unit_id")["w_pop"].transform("sum") == 0
    g.loc[nopop, "w_pop"] = 1.0
    cells = g[["tr", "tc"]].drop_duplicates().reset_index(drop=True)
    cells["k"] = np.arange(len(cells))
    g = g.merge(cells, on=["tr", "tc"])

    t0 = time.time()
    vals = {}
    for v in VARS:
        for y in YEARS:
            f = raw / f"{v}_{y}.npz"
            if not f.exists():
                a = first if (v, y) == (VARS[0], YEARS[0]) else fetch(v, y, r0, r1, c0, c1)
                np.savez_compressed(f, tr=cells["tr"].to_numpy(), tc=cells["tc"].to_numpy(),
                                    x=a[:, cells["tr"].to_numpy() - r0, cells["tc"].to_numpy() - c0].astype("float32"))
                print(f"{v} {y} read, {time.time() - t0:.0f} s", flush=True)
            z = np.load(f)
            assert (z["tr"] == cells["tr"].to_numpy()).all() and (z["tc"] == cells["tc"].to_numpy()).all()
            vals[v, y] = z["x"].astype("float64")  # months by cells

    rows = []
    for y in YEARS:
        cell = pd.DataFrame({
            "t2m": np.nanmean((vals["tmax", y] + vals["tmin", y]) / 2, axis=0),
            "tp": np.where(np.isnan(vals["ppt", y]).all(axis=0), np.nan, np.nansum(vals["ppt", y], axis=0)),
            "wind10": np.nanmean(vals["ws", y], axis=0),
        })
        x = g.join(cell, on="k")
        for c in ("t2m", "tp", "wind10"):
            ok = x[c].notna()
            num = (x.loc[ok, c] * x.loc[ok, "w_pop"]).groupby(x.loc[ok, "unit_id"]).sum()
            den = x.loc[ok, "w_pop"].groupby(x.loc[ok, "unit_id"]).sum()
            x[c + "_u"] = x["unit_id"].map(num / den)
        u = x.drop_duplicates("unit_id")[["unit_id", "t2m_u", "tp_u", "wind10_u"]]
        u.columns = ["unit_id", "t2m", "tp", "wind10"]
        u.insert(1, "year", y)
        rows.append(u)
    res = pd.concat(rows, ignore_index=True).sort_values(["unit_id", "year"])
    res.to_csv(out / "weather.csv", index=False, float_format="%.4f")
    log = dict(source="TerraClimate (Abatzoglou et al., 2018), yearly files over OPeNDAP", region_rows=[int(r0), int(r1)],
               region_cols=[int(c0), int(c1)], cells=len(cells), units=int(res["unit_id"].nunique()),
               nearest_land_cell=fallback, missing={c: int(res[c].isna().sum()) for c in ("t2m", "tp", "wind10")},
               summary=res[["t2m", "tp", "wind10"]].describe().round(3).to_dict())
    (out / "weather_log.json").write_text(json.dumps(log, indent=2, default=str))
    print(json.dumps({k: log[k] for k in ("cells", "units", "missing")}, indent=2), f"{len(fallback)} districts use the nearest land cell")


if __name__ == "__main__":
    main()
