"""Exploratory check, not in the registration: the imputation estimator with a linear trend for every district.

python -I scripts/analysis/06_trends.py panel_dir

The NO2 pre-trend test of the main specification rejects (pretrend.csv). This check adds a district-specific linear
time trend to the untreated model of did.py, so each designated district is compared with the extrapolation of its own
pre-designation path,

    y_it = a_i + b_i t + economy-by-year + size-group-by-year + X_it'c + e_it,

fitted on untreated district-years only. The model is solved directly, coefficients = (Z0'Z0)^+ Z0'y0, and the standard
error is the BJS Theorem 3 estimator of did.py with v = -Z0 (Z0'Z0)^+ Z1'w. A treated district-year is imputed only when
its district has at least MIN_PRE untreated years and its economy-year and size-year levels appear among untreated rows.
With the trend columns removed the same code must reproduce did.impute, which is checked on every run.

Writes trends.csv in panel_dir: outcome, model (levels or district trends), estimand (h0_5, h0 to h5, all), est, se, p,
ci_lo, ci_hi, pct, n_obs, n_clusters, n_treated_clusters, n_not_imputed.
"""
import sys
import time
from importlib import import_module
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import did  # noqa: E402

mde = import_module("02_mde")
OUTCOMES, COVARS = mde.OUTCOMES, mde.COVARS
MIN_PRE = 5


def impute_direct(df, spec, estimands, trend):
    d, X = did._prepare(df, spec)
    D = d["_D"].to_numpy()
    n = len(d)
    fes = did._codes(d, spec.fe)
    blocks = [did._indicator(c, g) for c, g in fes]
    # treated rows whose fixed effect levels have no untreated row cannot be imputed
    ok = D.copy()
    for c, g in fes:
        seen = np.bincount(c[~D], minlength=g) > 0
        ok &= seen[c]
    if trend:
        unit = d[spec.unit]
        n0 = unit[~D].value_counts()
        ok &= unit.map(n0).fillna(0).to_numpy() >= MIN_PRE
        tbar = d.loc[~D].groupby(spec.unit)[spec.year].mean()
        tc = (d[spec.year] - unit.map(tbar)).to_numpy(float) / 10
        uc, ug = fes[0]
        blocks.append(sparse.csr_matrix((tc, (np.arange(n), uc)), shape=(n, ug)))
    if X.shape[1]:
        blocks.append(sparse.csr_matrix(X))
    Z = sparse.hstack(blocks, format="csr")
    y = d[spec.y].to_numpy(float)
    Z0, Z1 = Z[~D], Z[ok]
    P = np.linalg.pinv((Z0.T @ Z0).toarray(), rcond=1e-11, hermitian=True)
    coef = P @ (Z0.T @ y[~D])
    pred = Z @ coef
    t = d.loc[ok].copy()
    t["tau"] = y[ok] - pred[ok]
    resid0 = y[~D] - pred[~D]
    clusters = d[spec.cluster].to_numpy()
    rows = []
    for name, f in estimands.items():
        w = np.asarray(f(t), float)
        if w.sum() <= 0:
            continue
        w1 = w / w.sum()
        v0 = -(Z0 @ (P @ (Z1.T @ w1)))
        est = float(w1 @ t["tau"].to_numpy())
        e1 = did._treated_resid(t, w1, spec)
        se = did._cluster_se(np.concatenate([v0, w1]), np.concatenate([resid0, e1]),
                             np.concatenate([clusters[~D], clusters[ok]]))
        rows.append(dict(estimand=name, est=est, se=se, n_obs=int((w1 > 0).sum()),
                         n_clusters=int(pd.unique(clusters).size),
                         n_treated_clusters=int(pd.unique(clusters[ok][w1 > 0]).size)))
    return pd.DataFrame(rows), int((D & ~ok).sum())


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    panel_dir = Path(sys.argv[1])
    p = mde.load(panel_dir)
    p["cohort"] = p["first_treated"]
    est = did.horizon_estimands()
    out = []
    for y in OUTCOMES:
        spec = did.Spec(y=y, covars=COVARS)
        t0 = time.time()
        ref = did.impute(p, spec, {"h0_5": est["h0_5"]}).estimates.loc["h0_5"]
        for trend in (False, True):
            r, n_not = impute_direct(p, spec, est, trend)
            if not trend:
                h = r.set_index("estimand").loc["h0_5"]
                if abs(h["est"] - ref["est"]) > 1e-6 or abs(h["se"] - ref["se"]) > 1e-6:
                    raise RuntimeError(f"{y}: direct solve {h['est']:.6f} ({h['se']:.6f}) differs from did.impute "
                                       f"{ref['est']:.6f} ({ref['se']:.6f})")
            r.insert(0, "model", "district trends" if trend else "levels")
            r.insert(0, "outcome", y)
            r["n_not_imputed"] = n_not
            out.append(r)
            print(f"{y} {'trends' if trend else 'levels'}: h0_5 {r.loc[r.estimand == 'h0_5', 'est'].iloc[0]:.4f} "
                  f"({r.loc[r.estimand == 'h0_5', 'se'].iloc[0]:.4f}), {time.time() - t0:.0f} s", flush=True)
    res = pd.concat(out, ignore_index=True)
    res["p"] = [did.p_two_sided(e, s) for e, s in zip(res["est"], res["se"])]
    res["ci_lo"], res["ci_hi"] = res["est"] - 1.96 * res["se"], res["est"] + 1.96 * res["se"]
    res["pct"] = 100 * np.expm1(res["est"])
    cols = ["outcome", "model", "estimand", "est", "se", "p", "ci_lo", "ci_hi", "pct", "n_obs", "n_clusters",
            "n_treated_clusters", "n_not_imputed"]
    res[cols].to_csv(panel_dir / "trends.csv", index=False)
    print(res[cols].to_string())


if __name__ == "__main__":
    main()
