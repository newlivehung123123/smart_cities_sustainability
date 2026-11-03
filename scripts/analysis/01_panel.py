"""Build the analysis panel: treatment table joined to the annual outcomes (registration Q12 to Q14).

python -I scripts/analysis/01_panel.py data/final out_dir

Writes out_dir/panel.parquet, one line per panel district and year 2005 to 2024, and out_dir/panel_log.json with the
counts the registration asks to report.

Covariates are read from every CSV in data/final/covariates/ (columns unit_id, year and one column per covariate). The
estimation scripts stop if a covariate of the main specification (COVARS in 02_mde.py) is missing from the panel.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

YEARS = range(2005, 2025)
CLIP_MAX = 0.10  # Q12


def build(final, out):
    tr = pd.read_csv(final / "treatment.csv", dtype={"unit_id": str})
    tr = tr[tr["in_panel"]].copy()
    first_cols = [c for c in tr.columns if c.startswith("first_treated")]
    keep = ["unit_id", "economy", "iso3", "cluster_name", "pop2015", "size_group", "first_programme", "first_model",
            "first_is_part", "id_mou_only_unit", "prefecture_named_year"] + first_cols
    units = pd.read_csv(final / "units.csv", dtype={"unit_id": str}, usecols=["unit_id", "cluster_id"])
    tr = tr[keep].merge(units, on="unit_id", how="left", validate="one_to_one")

    grid = pd.MultiIndex.from_product([tr["unit_id"], YEARS], names=["unit_id", "year"]).to_frame(index=False)
    p = grid.merge(tr, on="unit_id", how="left", validate="many_to_one")

    pm = pd.read_csv(final / "outcomes" / "pm25_annual.csv", dtype={"unit_id": str})
    no2 = pd.read_csv(final / "outcomes" / "no2_annual.csv", dtype={"unit_id": str})
    p = p.merge(pm[["unit_id", "year", "pm25", "pm25_area"]], on=["unit_id", "year"], how="left", validate="one_to_one")
    p = p.merge(no2[["unit_id", "year", "no2", "no2_area", "max_clip_share"]], on=["unit_id", "year"], how="left",
                validate="one_to_one")

    log = {}
    # Malaysian district-years of 2024 are dropped (Q13)
    drop = (p["iso3"] == "MYS") & (p["year"] == 2024)
    log["dropped_mys_2024"] = int(drop.sum())
    p = p[~drop].copy()
    log["district_years"] = len(p)

    for v in ["pm25", "pm25_area", "no2", "no2_area"]:
        bad = p[v] <= 0
        log[f"{v}_at_or_below_zero"] = int(bad.sum())
        p.loc[bad, v] = np.nan
    # main specification: NO2 missing when the clipped share is above 0.10 in any month (Q12); no2_all keeps every year
    p["no2_all"] = p["no2"]
    clip = p["max_clip_share"] > CLIP_MAX
    log["no2_clipping_rule"] = int((clip & p["no2"].notna()).sum())
    p.loc[clip, "no2"] = np.nan
    for v in ["pm25", "pm25_area", "no2", "no2_area", "no2_all"]:
        p[f"ln_{v}"] = np.log(p[v])
        log[f"missing_{v}"] = int(p[v].isna().sum())

    p["cohort"] = p["first_treated"]
    p["econ_year"] = p["iso3"] + "_" + p["year"].astype(str)
    p["size_group"] = p["size_group"].astype(int)
    p["size_year"] = p["size_group"].astype(str) + "_" + p["year"].astype(str)
    cov_dir = final / "covariates"
    for f in sorted(cov_dir.glob("*.csv")) if cov_dir.exists() else []:
        c = pd.read_csv(f, dtype={"unit_id": str})
        p = p.merge(c, on=["unit_id", "year"], how="left", validate="many_to_one")
        log[f"covariates_{f.stem}"] = [x for x in c.columns if x not in ("unit_id", "year")]
    log["districts"] = int(p["unit_id"].nunique())
    log["clusters"] = int(p["cluster_id"].nunique())
    log["treated_by_2024"] = int(tr["first_treated"].le(2024).sum())
    p.to_parquet(out / "panel.parquet", index=False)
    (out / "panel_log.json").write_text(json.dumps(log, indent=2))
    print(json.dumps(log, indent=2))


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    final, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    build(final, out)


if __name__ == "__main__":
    main()
