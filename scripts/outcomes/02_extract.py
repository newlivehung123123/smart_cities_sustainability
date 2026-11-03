"""District means of the PM2.5 and NO2 grids (dataset plan sections 3 and 4).

Each file is read over the network and never stored. HDF5 (ros3 driver) gives the byte range of every chunk that
holds a cell of a panel unit or city-state; only those chunks are downloaded (HTTP range requests), inflated and
unshuffled. For each unit and period:
- mean_pop: mean of the cells with data, weighted by w_pop (2015 population in the cell times the share of the cell
  inside the unit, from 01_weights.py);
- mean_area: the same with w_area (area inside the unit), kept as a check;
- pop_share, area_share: share of the unit's weight held by cells with data;
- n_cells, n_valid: cells touched and cells with data.
A unit-period is missing (mean_pop and mean_area empty) when cells with data hold less than half of its weighted
population (section 4). Cells with no data are the file's fill value (PM2.5 -999.9, NO2 NaN); any other negative value
is kept and counted in the run log. NO2 also stores water and some shoreline cells as exactly 0 with an uncertainty of
0, so a cell that is 0 in all 240 months is no data; a cell that is 0 in only some months is a low estimate and is kept.
For NO2 the cell values of each month are therefore saved first (data/interim/outcomes/no2_cells/), and the means are
computed once every month has been read (no2_means; the count of zero months per cell goes to no2_zero_months.parquet).
The NO2 uncertainty is 0.455 times the value at every level, so it cannot tell water from a low estimate. Partly-zero
cells are estimates cut off at zero (neighbouring years read 0.25 to 0.50 ppb there), and the NO2 CSVs add clip_share,
the share of the population weight behind mean_pop held by such cells (the main specification sets a district-year
missing when it is above 0.10 in any month, registration Q12).

Products:
- pm25_annual: V6.GL.03 annual files, 1998 to 2024;
- pm25_monthly: V6.GL.03 monthly files, 2005 to 2024 (Singapore burning-season check);
- no2_monthly: SatNO2 V4.GL.01 monthly files, 2005 to 2024.
Writes one CSV per period to data/interim/outcomes/<product>/ and skips periods already written, so a stopped run
resumes. The first period of every run is checked against h5py's own reading of one chunk. If no period finishes in
15 minutes (a stalled S3 read), the workers are killed and the remaining periods start again.

argv[1] = product, argv[2] = data/interim/outcomes/weights.parquet, argv[3] = data/interim/outcomes, argv[4] (optional)
= number of files read at once (default 3)
"""
import sys, time, zlib
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, ThreadPoolExecutor, wait
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
import requests

PRODUCT, WEIGHTS, OUT = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
WORKERS = int(sys.argv[4]) if len(sys.argv) > 4 else 3
CELLS = OUT / "no2_cells"
BUCKET = "https://satpmdata.s3.amazonaws.com/"
FILL_BELOW = -999  # PM2.5 fill is -999.9; NO2 fill is NaN
UA = {"User-Agent": "smart_cities_sustainability research script (github.com/newlivehung123123/smart_cities_sustainability)"}


def periods(product):
    if product == "pm25_annual":
        return [(str(y), f"V6GL03/CNNPM25/Annual/GL/V6GL03.CNNPM25.GL.{y}01-{y}12.nc", "PM25") for y in range(1998, 2025)]
    ym = [(y, m) for y in range(2005, 2025) for m in range(1, 13)]
    if product == "pm25_monthly":
        return [(f"{y}-{m:02d}", f"V6GL03/CNNPM25/Monthly/GL/V6GL03.CNNPM25.GL.{y}{m:02d}-{y}{m:02d}.nc", "PM25")
                for y, m in ym]
    if product == "no2_monthly":
        return [(f"{y}-{m:02d}", f"SATNO2V4GL01/NO2/{y}/NO2_surface_monthly_0p01deg_{y}{m:02d}.nc", "NO2") for y, m in ym]
    raise SystemExit(f"unknown product {product}")


def get_range(url, start, size, tries=5):
    for k in range(tries):
        try:
            r = requests.get(url, headers=UA | {"Range": f"bytes={start}-{start + size - 1}"}, timeout=180)
            if r.status_code == 206 and len(r.content) == size:
                return r.content
            err = f"status {r.status_code}, {len(r.content)} bytes"
        except requests.RequestException as e:
            err = repr(e)
        time.sleep(5 * (k + 1))
    raise RuntimeError(f"{url} bytes {start}+{size}: {err}")


def open_h5(url, tries=4):
    for k in range(tries):
        try:
            return h5py.File(url, "r", driver="ros3", aws_region=b"us-east-1")
        except OSError as e:
            if k == tries - 1:
                raise
            time.sleep(10 * (k + 1))


def run(job):
    label, key, var, check = job
    t0 = time.time()
    w = pd.read_parquet(WEIGHTS)
    url = BUCKET + key
    h = open_h5(url)
    d = h[var]
    cr, cc = d.chunks
    filters = d._filters
    assert set(filters) <= {"shuffle", "gzip"} and "gzip" in filters and d.dtype == np.float32, filters
    kr, kc = (w.row // cr).to_numpy(), (w.col // cc).to_numpy()
    keys = sorted(set(zip(kr.tolist(), kc.tolist())))
    info = {k: d.id.get_chunk_info_by_coord((k[0] * cr, k[1] * cc)) for k in keys}
    assert all(i.filter_mask == 0 for i in info.values())

    def chunk(k):
        b = zlib.decompress(get_range(url, info[k].byte_offset, info[k].size))
        a = np.frombuffer(b, np.uint8)
        if "shuffle" in filters:
            a = a.reshape(4, -1).T.copy()
        return k, a.view("<f4").reshape(cr, cc)

    with ThreadPoolExecutor(8) as ex:
        chunks = dict(ex.map(chunk, keys))
    if check:  # compare one chunk with h5py's own reading
        k = keys[len(keys) // 2]
        ref = d[k[0] * cr:(k[0] + 1) * cr, k[1] * cc:(k[1] + 1) * cc]
        assert np.array_equal(chunks[k][:ref.shape[0], :ref.shape[1]], ref, equal_nan=True), "chunk decode differs"
    h.close()

    v = np.empty(len(w), np.float32)
    for k, a in chunks.items():
        m = (kr == k[0]) & (kc == k[1])
        v[m] = a[w.row.to_numpy()[m] - k[0] * cr, w.col.to_numpy()[m] - k[1] * cc]
    mb = sum(i.size for i in info.values()) / 2**20
    if PRODUCT == "no2_monthly":  # the means wait for the zero mask, which needs every month
        tmp = CELLS / f"{label}.part"
        with open(tmp, "wb") as f:
            np.save(f, v)
        tmp.rename(CELLS / f"{label}.npy")
        return f"{label}: {len(keys)} chunks, {mb:.0f} MB, {time.time() - t0:.0f} s; {int((v == 0).sum())} zero cells"
    ok = np.isfinite(v) & (v > FILL_BELOW)
    n_neg = int((ok & (v < 0)).sum())
    res = means(w, v, ok, label)
    write(res, label)
    return (f"{label}: {len(keys)} chunks, {mb:.0f} MB, {time.time() - t0:.0f} s; {int(res.mean_pop.isna().sum())} units "
            f"missing; {n_neg} negative cells kept; mean_pop median {np.nanmedian(res.mean_pop):.2f}")


def means(w, v, ok, label):
    uid, idx = np.unique(w.unit_id.to_numpy(), return_inverse=True)
    res = {"unit_id": uid, "period": label}
    for wcol, tag in (("w_pop", "pop"), ("w_area", "area")):
        wt = w[wcol].to_numpy()
        tot = np.bincount(idx, wt, len(uid))
        has = np.bincount(idx, np.where(ok, wt, 0), len(uid))
        num = np.bincount(idx, np.where(ok, wt * np.where(ok, v, 0), 0), len(uid))
        with np.errstate(invalid="ignore", divide="ignore"):
            res[f"mean_{tag}"], res[f"{tag}_share"] = num / has, has / tot
    res["n_cells"] = np.bincount(idx, minlength=len(uid))
    res["n_valid"] = np.bincount(idx, ok, len(uid)).astype(int)
    res = pd.DataFrame(res)
    res.loc[res.pop_share < 0.5, ["mean_pop", "mean_area"]] = np.nan
    return res


def write(res, label):
    out = OUT / PRODUCT / f"{label}.csv"
    tmp = out.with_suffix(".part")
    res.to_csv(tmp, index=False, float_format="%.6g")
    tmp.rename(out)


def no2_means():
    w = pd.read_parquet(WEIGHTS)
    labels = [p[0] for p in periods(PRODUCT)]
    nzero = np.zeros(len(w), np.int16)
    for lab in labels:
        nzero += np.load(CELLS / f"{lab}.npy") == 0
    mask = nzero == len(labels)
    w[["unit_id", "row", "col"]].assign(zero_months=nzero).to_parquet(OUT / "no2_zero_months.parquet", index=False)
    pop = w.w_pop.to_numpy()
    print(f"{int(mask.sum())} cells are 0 in all {len(labels)} months ({pop[mask].sum() / pop.sum():.2%} of weighted "
          f"population) and count as no data; {int(((nzero > 0) & ~mask).sum())} cells are 0 in some months and are kept",
          flush=True)
    uid, idx = np.unique(w.unit_id.to_numpy(), return_inverse=True)
    for lab in labels:
        v = np.load(CELLS / f"{lab}.npy")
        ok = np.isfinite(v) & (v > FILL_BELOW) & ~mask
        res = means(w, v, ok, lab)
        # share of the population weight behind mean_pop held by cells at 0 (estimates cut off at zero)
        with np.errstate(invalid="ignore", divide="ignore"):
            res["clip_share"] = (np.bincount(idx, np.where(ok & (v == 0), pop, 0), len(uid))
                                 / np.bincount(idx, np.where(ok, pop, 0), len(uid)))
        write(res, lab)
        print(f"{lab}: {int(res.mean_pop.isna().sum())} units missing; {int((ok & (v < 0)).sum())} negative cells kept; "
              f"{int((ok & (v == 0)).sum())} zero cells kept; mean_pop median {np.nanmedian(res.mean_pop):.2f}", flush=True)


if __name__ == "__main__":
    # The ros3 driver sets no network timeout, so a stalled S3 read can hang a worker for good. If no period finishes
    # within STALL seconds the workers are killed and the remaining periods start again (at most RESTARTS times).
    STALL, RESTARTS = 900, 10
    (OUT / PRODUCT).mkdir(parents=True, exist_ok=True)
    if PRODUCT == "no2_monthly":
        CELLS.mkdir(exist_ok=True)
    done_file = (lambda lab: CELLS / f"{lab}.npy") if PRODUCT == "no2_monthly" else (lambda lab: OUT / PRODUCT / f"{lab}.csv")
    for attempt in range(RESTARTS + 1):
        todo = [p for p in periods(PRODUCT) if not done_file(p[0]).exists()]
        print(PRODUCT, len(todo), "periods to read", flush=True)
        if not todo:
            break
        jobs = [(lab, key, var, i == 0) for i, (lab, key, var) in enumerate(todo)]
        ex = ProcessPoolExecutor(WORKERS)
        futs = {ex.submit(run, j): j[0] for j in jobs}
        pending = set(futs)
        while pending:
            done, pending = wait(pending, timeout=STALL, return_when=FIRST_COMPLETED)
            if not done:
                break
            for f in done:
                print(f.result(), flush=True)
        if not pending:
            ex.shutdown()
            break
        print(f"no period finished in {STALL} s; {len(pending)} left; killing workers and restarting "
              f"(attempt {attempt + 1})", flush=True)
        for p in ex._processes.values():
            p.kill()
        ex.shutdown(wait=False, cancel_futures=True)
    else:
        raise SystemExit("too many restarts")
    if PRODUCT == "no2_monthly":
        no2_means()
