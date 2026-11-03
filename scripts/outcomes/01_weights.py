"""Cell weights for the district means of the outcome grids (dataset plan section 4).

PM2.5 (ACAG V6.GL.03) and NO2 (ACAG SatNO2 V4.GL.01) share one 0.01 degree grid: 13,000 rows from 60 S (row 0) to
70 N and 36,000 columns from 180 W, cell edges on multiples of 0.01 degree. The 2015 population grid from
04_population.py has the same edges, so every cell of it is one outcome cell.

For every panel unit and city-state, exactextract gives the fraction of each 0.01 degree cell inside the unit. Each cell
then carries two weights:
- w_pop: GHS-POP 2015 population of the cell times that fraction (the main weight);
- w_area: the fraction times the cosine of the cell's centre latitude, proportional to the area inside the unit (the
  unweighted area mean kept as a check).
The population of the unit implied by the weights (sum of w_pop) is compared with pop2015 in units.csv, which sums 3
arc-second cells by their centres; the two differ only where population sits in cells cut by the unit's boundary.

Writes data/interim/outcomes/weights.parquet (unit_id, row and column on the outcome grid, coverage, w_pop, w_area).

argv[1] = data/interim/units/units.parquet, argv[2] = data/final/units.csv, argv[3] = data/interim/ghs_pop_2015_001deg.tif,
argv[4] = data/interim/outcomes
"""
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from exactextract import exact_extract

GEOM, UNITS, POP, OUT = (Path(a) for a in sys.argv[1:5])

units = pd.read_csv(UNITS)
keep = units[units.in_panel | units.city_state]
g = gpd.read_parquet(GEOM, columns=["unit_id", "geometry"])
g = g[g.unit_id.isin(keep.unit_id)].reset_index(drop=True)
assert len(g) == len(keep), (len(g), len(keep))

with rasterio.open(POP) as src:
    pop = src.read(1)
    t = src.transform
    assert abs(t.a - 0.01) < 1e-9 and abs(t.e + 0.01) < 1e-9
    ncol = src.width
# outcome grid indices of the population grid's first row and column
col0 = int(round((t.c + 180) / 0.01))
row_top = int(round((t.f + 60) / 0.01)) - 1  # outcome row of the population grid's top row (rows run south to north)

ex = exact_extract(str(POP), g, ["cell_id", "coverage"], include_cols=["unit_id"], output="pandas")
ex = ex.rename(columns=lambda k: k.removeprefix("band_1_"))  # the grid has two bands; band 1 is all population
ex = ex.explode(["cell_id", "coverage"])
ex = ex[ex.coverage.astype(float) > 0]
cell = ex.cell_id.astype(np.int64).to_numpy()
r, c = cell // ncol, cell % ncol
w = pd.DataFrame({"unit_id": ex.unit_id.to_numpy(), "row": (row_top - r).astype(np.int32),
                  "col": (col0 + c).astype(np.int32), "coverage": ex.coverage.astype(float).to_numpy()})
cell_pop = pop[r, c].astype(float)
lat = -60 + 0.01 * (w.row + 0.5)
w["w_pop"] = cell_pop * w.coverage
w["w_area"] = w.coverage * np.cos(np.radians(lat))

n_nan = int(np.isnan(cell_pop).sum())
assert n_nan == 0, f"{n_nan} cells without a population value"
OUT.mkdir(parents=True, exist_ok=True)
w.to_parquet(OUT / "weights.parquet", index=False)

s = w.groupby("unit_id").agg(cells=("row", "size"), pop_w=("w_pop", "sum"))
s = s.join(keep.set_index("unit_id")[["economy", "pop2015"]])
s["ratio"] = s.pop_w / s.pop2015
print(len(w), "unit-cell pairs for", len(s), "units; cells per unit median", int(s.cells.median()), "min", s.cells.min(),
      "max", s.cells.max())
print("weights population / pop2015: quantiles", s.ratio.quantile([0, .01, .05, .5, .95, .99, 1]).round(3).to_dict())
print("units with zero weighted population:", int((s.pop_w == 0).sum()))
print(s.sort_values("ratio").head(5)[["economy", "cells", "pop_w", "pop2015", "ratio"]].to_string())
print(s.sort_values("ratio").tail(5)[["economy", "cells", "pop_w", "pop2015", "ratio"]].to_string())
