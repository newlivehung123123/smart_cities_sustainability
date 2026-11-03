"""Exploratory check, not in the registration: is the RQ2 fall in night-time light an artefact of the DN 63 ceiling?

python -I scripts/analysis/07_ntl_ceiling.py panel_dir

The harmonised night-time light series of Li et al. (2020) is on the DMSP scale, top-coded at a digital number (DN) of
63, and many designated districts are close to the ceiling. A district near 63 cannot brighten, so designated districts
would fall behind dimmer undesignated districts without any change in activity. This script reports

1. the share of districts with a 2016 mean DN of at least 55, by designation status (2016 precedes every first
   treated year of the panel),
2. the pre-trend test of did.py for ln NTL on 2012 to 2024 (five leads, the most that 2012 to 2016 allows),
3. the RQ2 estimates of 03_estimate.py on districts with a 2016 mean DN below 40 and below 30.

Writes ntl_ceiling.csv in panel_dir: check, outcome, est, se, p, ci_lo, ci_hi, pct, n_obs, n_treated_clusters, note.
"""
import sys
from importlib import import_module
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import did  # noqa: E402

mde = import_module("02_mde")
COVARS = mde.COVARS
BASE = 2016


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    panel_dir = Path(sys.argv[1])
    p = mde.load(panel_dir)
    p["cohort"] = p["first_treated"]
    q = p[p["year"].between(2012, 2024)].copy()
    q["ln_ntl"] = np.log(q["ntl"].where(q["ntl"] > 0))
    q["ln_pm25_per_ntl"] = q["ln_pm25"] - q["ln_ntl"]
    base = p.loc[p["year"] == BASE].set_index("unit_id")["ntl"]
    q["ntl_base"] = q["unit_id"].map(base)
    ever = p.groupby("unit_id")["first_treated"].first().le(2024)

    rows = []
    for status, ids in (("designated by 2024", ever[ever].index), ("not designated by 2024", ever[~ever].index)):
        b = base.reindex(ids)
        rows.append(dict(check=f"share with {BASE} mean DN >= 55", outcome=status, est=float((b >= 55).mean()),
                         n_obs=int(b.notna().sum()), note=f"median {BASE} DN {b.median():.1f}"))

    pt = did.pretrend_test(q, did.Spec(y="ln_ntl", covars=COVARS), leads=5)
    rows.append(dict(check="pre-trend test, 2012 to 2024", outcome="ln_ntl", est=pt["F"], p=pt["p"],
                     n_obs=pt["n"], note="F statistic with 5 leads; leads " +
                     ", ".join(f"{c:.3f}" for c in pt["coef"])))

    est = {"h0_5": did.horizon_estimands()["h0_5"]}
    for cut in (None, 40, 30):
        s = q if cut is None else q[q["ntl_base"] < cut]
        for y in ("ln_ntl", "ln_pm25_per_ntl"):
            r = did.impute(s, did.Spec(y=y, covars=COVARS), est).estimates.loc["h0_5"]
            rows.append(dict(check="all districts" if cut is None else f"{BASE} mean DN below {cut}", outcome=y,
                             est=r["est"], se=r["se"], p=did.p_two_sided(r["est"], r["se"]), n_obs=r["n_obs"],
                             n_treated_clusters=r["n_treated_clusters"],
                             note=f"{s['unit_id'].nunique()} districts"))
            print(rows[-1], flush=True)
    out = pd.DataFrame(rows)
    out["ci_lo"], out["ci_hi"] = out["est"] - 1.96 * out["se"], out["est"] + 1.96 * out["se"]
    out["pct"] = np.where(out["se"].notna(), 100 * np.expm1(out["est"]), np.nan)
    cols = ["check", "outcome", "est", "se", "p", "ci_lo", "ci_hi", "pct", "n_obs", "n_treated_clusters", "note"]
    out[cols].to_csv(panel_dir / "ntl_ceiling.csv", index=False)
    print(out[cols].to_string())


if __name__ == "__main__":
    main()
