"""Combine the per-period district means of 02_extract.py into outcome tables (dataset plan section 4).

Reads data/interim/outcomes/<product>/<period>.csv and writes to data/final/outcomes/:
- pm25_annual.csv: one line per unit and year, 1998 to 2024;
- pm25_monthly.csv.gz: one line per unit and month, 2005 to 2024;
- no2_monthly.csv.gz: one line per unit and month, 2005 to 2024;
- no2_annual.csv: one line per unit and year, 2005 to 2024. The annual mean is the mean of the 12 monthly means and is
  missing unless all 12 months have a value (registration Q12 and Q14); n_months counts the months with a value, and
  max_clip_share is the highest monthly clip_share of the year (the main specification sets a year above 0.10 missing,
  registration Q12).
pm25 and no2 are the population-weighted means, pm25_area and no2_area the area-weighted check (codebook). A product is
combined only when every period has been extracted. Nothing here uses the treatment table.

argv[1] = data/interim/outcomes, argv[2] = data/final/outcomes
"""
import sys
from pathlib import Path

import pandas as pd

IN, OUT = Path(sys.argv[1]), Path(sys.argv[2])
N_PERIODS = {"pm25_annual": 27, "pm25_monthly": 240, "no2_monthly": 240}
NAME = {"pm25_annual": "pm25", "pm25_monthly": "pm25", "no2_monthly": "no2"}


def load(product):
    files = sorted((IN / product).glob("*.csv"))
    if len(files) != N_PERIODS[product]:
        print(f"{product}: {len(files)} of {N_PERIODS[product]} periods extracted, not combined")
        return None
    d = pd.concat([pd.read_csv(f, dtype={"unit_id": str, "period": str}) for f in files], ignore_index=True)
    v = NAME[product]
    d = d.rename(columns={"mean_pop": v, "mean_area": f"{v}_area"})
    if product.endswith("monthly"):
        d["year"] = d.period.str[:4].astype(int)
        d["month"] = d.period.str[5:].astype(int)
        keys = ["unit_id", "year", "month"]
    else:
        d["year"] = d.period.astype(int)
        keys = ["unit_id", "year"]
    extra = ["clip_share"] if "clip_share" in d else []
    d = d[keys + [v, f"{v}_area", "pop_share", "area_share", "n_cells", "n_valid"] + extra].sort_values(keys)
    assert not d.duplicated(keys).any()
    assert d.groupby(keys[1:]).size().nunique() == 1, "periods differ in their units"
    print(f"{product}: {d.unit_id.nunique()} units, {len(d)} rows, missing {int(d[v].isna().sum())}, "
          f"at or below zero {int((d[v] <= 0).sum())}")
    return d


OUT.mkdir(parents=True, exist_ok=True)
pm = load("pm25_annual")
if pm is not None:
    pm.to_csv(OUT / "pm25_annual.csv", index=False, float_format="%.6g")
pmm = load("pm25_monthly")
if pmm is not None:
    pmm.to_csv(OUT / "pm25_monthly.csv.gz", index=False, float_format="%.6g")
no2 = load("no2_monthly")
if no2 is not None:
    no2.to_csv(OUT / "no2_monthly.csv.gz", index=False, float_format="%.6g")
    g = no2.groupby(["unit_id", "year"])
    a = g.agg(no2=("no2", "mean"), no2_area=("no2_area", "mean"), n_months=("no2", "count"),
              min_pop_share=("pop_share", "min"), max_clip_share=("clip_share", "max")).reset_index()
    a.loc[a.n_months < 12, ["no2", "no2_area"]] = float("nan")
    a.to_csv(OUT / "no2_annual.csv", index=False, float_format="%.6g")
    print(f"no2_annual: {len(a)} rows, missing (fewer than 12 months) {int(a.no2.isna().sum())}, "
          f"max_clip_share above 0.10 in {int((a.no2.notna() & (a.max_clip_share > 0.10)).sum())} further rows")
