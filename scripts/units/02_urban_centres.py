"""Build the 2015 urban centres of the study region from GHS-SMOD R2023A (dataset plan section 2b).

Reads the 2015 epoch of the Settlement Model grid (1 km, Mollweide) inside the zip, keeps class 30 (urban centre grid
cell), groups the cells into centres by edge contiguity (no diagonals), converts each centre to WGS84 and writes
urban_centres_2015.parquet. The zip is hashed, recorded in ghsl_sources.csv and deleted.

argv[1] = data/raw/ghsl, argv[2] = data/interim/units, argv[3] = empty download folder outside the project.
"""
import csv, datetime, hashlib, sys, zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.features import shapes
from rasterio.windows import from_bounds
from shapely.geometry import shape

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch import fetch_parallel  # noqa: E402

RAW, OUT, DL = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
NAME = "GHS_SMOD_E2015_GLOBE_R2023A_54009_1000_V2_0"
URL = ("https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_SMOD_GLOBE_R2023A/"
       f"GHS_SMOD_E2015_GLOBE_R2023A_54009_1000/V2-0/{NAME}.zip")
REGION = (87.0, -12.0, 155.0, 54.0)  # lon and lat bounds of the 17 economies, with margin
URBAN_CENTRE = 30

z = fetch_parallel(URL, DL / f"{NAME}.zip")
sha = hashlib.sha256(z.read_bytes()).hexdigest()
assert zipfile.ZipFile(z).testzip() is None
with rasterio.open(f"/vsizip/{z}/{NAME}.tif") as r:
    assert r.crs.to_string() in ("ESRI:54009", "EPSG:54009") or "Mollweide" in r.crs.to_wkt(), r.crs
    box = Transformer.from_crs(4326, r.crs, always_xy=True).transform_bounds(*REGION, densify_pts=101)
    win = from_bounds(*box, transform=r.transform).round_offsets().round_lengths()
    a = r.read(1, window=win)
    tr = r.window_transform(win)
    crs = r.crs
    classes = sorted(np.unique(a).tolist())
assert URBAN_CENTRE in classes, classes
print("window", a.shape, "classes", classes, "urban centre cells", int((a == URBAN_CENTRE).sum()), flush=True)

mask = a == URBAN_CENTRE
polys = [shape(g) for g, v in shapes(mask.astype(np.uint8), mask=mask, connectivity=4, transform=tr) if v == 1]
uc = gpd.GeoDataFrame({"n_cells": [round(p.area / 1e6) for p in polys]}, geometry=polys, crs=crs)
assert uc.n_cells.sum() == mask.sum()
uc = uc.to_crs(4326)
uc = uc.sort_values("n_cells", ascending=False).reset_index(drop=True)
uc.insert(0, "uc_id", [f"UC{i + 1:05d}" for i in range(len(uc))])
uc.to_parquet(OUT / "urban_centres_2015.parquet", compression="zstd")
print(len(uc), "urban centres; largest", uc.n_cells.iloc[0], "cells; smallest", uc.n_cells.iloc[-1], flush=True)

record = {"file": f"{NAME}.zip", "use": "2015 urban centres (class 30), study region only",
          "licence": "CC BY 4.0 (European Union)", "url": URL, "sha256": sha, "bytes": z.stat().st_size,
          "read_date": datetime.date.today().isoformat()}
src = RAW / "ghsl_sources.csv"
rows = {r["file"]: r for r in csv.DictReader(open(src, encoding="utf-8"))} if src.exists() else {}
rows[record["file"]] = record
with open(src, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, list(record))
    w.writeheader()
    w.writerows(rows.values())
z.unlink()
