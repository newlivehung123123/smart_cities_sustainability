"""Minimum detectable effect from placebo designations (registration Q21).

python -I scripts/analysis/02_mde.py panel_dir rule [n_placebo] [seed]

panel_dir holds panel.parquet from 01_panel.py. The sample is the panel districts with no
designation under any specification. Each placebo assigns designation within each economy and runs the main estimator
(the headline mean of tau over years 0 to 5).

rule count   Q21 as registered: as many placebo districts as are treated in the economy. Stops if an economy has fewer
             never-designated districts than treated ones, or as many, since no comparison district would be left.
rule share   The economy's share of treated panel districts, applied to its never-designated districts (rounded).

Placebo first treated years are drawn without replacement from the economy's observed first treated years to 2024.
Writes mde_placebos.csv (one line per placebo and outcome) and mde.csv (SD of the placebo estimates and 2.80 x SD).
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import did  # noqa: E402

OUTCOMES = ("ln_pm25", "ln_no2")
COVARS = ("t2m", "tp", "wind10", "ln_fire_100km", "ln_fire_300km")  # Q12
FIRST = None  # filled from the panel: every first_treated column


def load(panel_dir):
    panel_dir = Path(panel_dir)
    p = pd.read_parquet(panel_dir / "panel.parquet")
    missing = [c for c in COVARS if c not in p.columns]
    if missing:
        sys.exit(f"covariates of the main specification missing from the panel: {missing}")
    return p


def placebo_counts(units, rule):
    """Placebo districts per economy."""
    out = {}
    for iso, g in units.groupby("iso3"):
        n_tr = int(g["first_treated"].le(2024).sum())
        n_never = int(g["never"].sum())
        if n_tr == 0:
            continue
        if rule == "count":
            if n_tr >= n_never:
                raise ValueError(f"{iso}: {n_tr} treated and {n_never} never-designated districts; the count rule "
                                 "leaves no comparison district")
            out[iso] = n_tr
        else:
            out[iso] = int(round(n_tr / len(g) * n_never))
    return out


def main():
    if len(sys.argv) < 3 or sys.argv[2] not in ("count", "share"):
        sys.exit(__doc__)
    panel_dir, rule = Path(sys.argv[1]), sys.argv[2]
    n_pl = int(sys.argv[3]) if len(sys.argv) > 3 else 500
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 20261102
    p = load(panel_dir)
    first = [c for c in p.columns if c.startswith("first_treated")]
    units = p.drop_duplicates("unit_id")[["unit_id", "iso3", "first_treated"] + [c for c in first if c != "first_treated"]]
    units = units.assign(never=units[first].isna().all(1))
    counts = placebo_counts(units, rule)
    cohorts = {iso: units.loc[(units.iso3 == iso) & units.first_treated.le(2024), "first_treated"].to_numpy()
               for iso in counts}
    never_ids = {iso: units.loc[(units.iso3 == iso) & units.never, "unit_id"].to_numpy() for iso in counts}
    sample = p[p["unit_id"].isin(units.loc[units.never, "unit_id"])].copy()
    print(f"rule {rule}: {sum(counts.values())} placebo districts among {units.never.sum()} never-designated; "
          + ", ".join(f"{k} {v}" for k, v in counts.items()), flush=True)

    rng = np.random.default_rng(seed)
    est = lambda t: t["_rel"].between(0, 5)
    rows = []
    t0 = time.time()
    for k in range(n_pl):
        assign = {}
        for iso, n in counts.items():
            ids = rng.choice(never_ids[iso], size=n, replace=False)
            yrs = rng.choice(cohorts[iso], size=n, replace=False)
            assign.update(dict(zip(ids, yrs)))
        sample["cohort"] = sample["unit_id"].map(assign)
        for y in OUTCOMES:
            sp = did.Spec(y=y, covars=COVARS)
            rows.append(dict(placebo=k, outcome=y, est=did.point(sample, sp, est)))
        if (k + 1) % 50 == 0:
            print(f"  {k + 1}/{n_pl} placebos, {time.time() - t0:.0f} s", flush=True)
    r = pd.DataFrame(rows)
    r.to_csv(panel_dir / f"mde_placebos_{rule}.csv", index=False)
    s = r.groupby("outcome")["est"].agg(["mean", "std", "count"])
    s["mde"] = 2.80 * s["std"]
    s["mde_pct"] = 100 * (1 - np.exp(-s["mde"]))
    s["detects_5pct"] = s["mde"] <= -np.log(0.95)
    s.to_csv(panel_dir / f"mde_{rule}.csv")
    (panel_dir / f"mde_{rule}.json").write_text(json.dumps(dict(rule=rule, seed=seed, counts=counts), indent=2))
    print(s.round(4).to_string())


if __name__ == "__main__":
    main()
