"""Main estimates for RQ1 to RQ3 and the focal economies (registration Q4, Q19 to Q23).

python -I scripts/analysis/03_estimate.py panel_dir [bootstrap_draws] [wild_draws] [workers]

Reads panel.parquet from 01_panel.py and writes, in panel_dir,

results_main.csv     headline (years 0 to 5), each year 0 to 5 and all treated years, for ln PM2.5 and ln NO2, with
                     Holm-adjusted p-values for the two headline effects and the TOST result (Q22)
pretrend.csv         BJS test of eight pre-designation indicators (Q19)
h1.csv               NO2 minus PM2.5 headline effect, cluster bootstrap (Q4)
rq3.csv, rq3_wald.csv  one sample per programme model, and the Wald test of equal effects on the bootstrap draws
focal.csv            Japan and Thailand from the pooled fit; wild cluster bootstrap p-values where the treated
                     district-years lie in fewer than 30 first-level units
rq2.csv              ln NTL and ln PM2.5 minus ln NTL, 2012 to 2024 (only if the panel has ntl)
"""
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import did  # noqa: E402
from importlib import import_module  # noqa: E402

mde = import_module("02_mde")

OUTCOMES = mde.OUTCOMES
COVARS = mde.COVARS
MODELS = {"impl": "implementation support", "cert": "certification", "ascn": "network membership"}
FOCAL = ("JPN", "THA")
HEAD = lambda t: t["_rel"].between(0, 5)


def pct(x):
    return 100 * (np.exp(x) - 1)


def model_of(first_model):
    """Districts whose first year has both certification and implementation support count as implementation support."""
    if pd.isna(first_model):
        return np.nan
    return "implementation support" if "implementation support" in first_model else first_model


def rq3_sample(p, model):
    """Treated: first designation under `model`. Districts first designated under another model are kept only until
    the year before that designation, and are untreated there."""
    m = p["first_model"].map(model_of)
    other = p["first_treated"].le(2024) & (m != model)
    s = p[~(other & (p["year"] >= p["first_treated"]))].copy()
    s.loc[other.loc[s.index], "cohort"] = np.nan
    return s


_P = None


def _init(p):
    global _P
    _P = p


def _draw(g):
    """Main and RQ3 headline effects on one cluster bootstrap draw."""
    q = did.resample(_P, g, did.Spec(y=OUTCOMES[0]))
    r = {f"main_{y}": did.point(q, did.Spec(y=y, covars=COVARS), HEAD) for y in OUTCOMES}
    for key, model in MODELS.items():
        s = rq3_sample(q, model)
        for y in OUTCOMES:
            r[f"{key}_{y}"] = did.point(s, did.Spec(y=y, covars=COVARS), HEAD)
    return r


def table(fit, outcome):
    e = fit.estimates.copy()
    e["p"] = [did.p_two_sided(a, b) for a, b in zip(e["est"], e["se"])]
    e["ci_lo"], e["ci_hi"] = e["est"] - 1.96 * e["se"], e["est"] + 1.96 * e["se"]
    e["pct"], e["pct_lo"], e["pct_hi"] = pct(e["est"]), pct(e["ci_lo"]), pct(e["ci_hi"])
    e["outcome"] = outcome
    e["n_not_imputed"] = fit.n_not_imputed
    return e.reset_index()


def rq3_table(p, panel_dir, B_wild):
    """RQ3 effects by programme model, written to rq3.csv. A model whose designated districts lie in fewer than 30
    first-level units also gets the wild cluster bootstrap p-value, as for the focal economies."""
    rows, theta = [], {}
    for key, model in MODELS.items():
        s = rq3_sample(p, model)
        for y in OUTCOMES:
            sp = did.Spec(y=y, covars=COVARS)
            fit = did.impute(s, sp, {"h0_5": HEAD})
            tab = table(fit, y).assign(model=model)
            tab["p_wild"] = (did.wild_cluster_p(fit, sp, "h0_5", B=B_wild)["p"]
                             if tab.loc[0, "n_treated_clusters"] < 30 else np.nan)
            rows.append(tab)
            theta[(key, y)] = tab.loc[0, "est"]
    pd.concat(rows, ignore_index=True).to_csv(panel_dir / "rq3.csv", index=False)
    return theta


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    panel_dir = Path(sys.argv[1])
    B = int(sys.argv[2]) if len(sys.argv) > 2 else 999
    B_wild = int(sys.argv[3]) if len(sys.argv) > 3 else 9_999
    workers = int(sys.argv[4]) if len(sys.argv) > 4 else 6
    p = mde.load(panel_dir)
    p["cohort"] = p["first_treated"]
    t0 = time.time()

    # RQ1, event study, focal economies
    est = did.horizon_estimands()
    for iso in FOCAL:
        est[f"{iso}_h0_5"] = (lambda iso: lambda t: (t["iso3"] == iso) & t["_rel"].between(0, 5))(iso)
        est[f"{iso}_all"] = (lambda iso: lambda t: t["iso3"] == iso)(iso)
    main_rows, pre_rows, focal_rows = [], [], []
    for y in OUTCOMES:
        sp = did.Spec(y=y, covars=COVARS)
        fit = did.impute(p, sp, est)
        tab = table(fit, y)
        main_rows.append(tab[~tab["estimand"].str[:3].isin(FOCAL)])
        f = tab[tab["estimand"].str[:3].isin(FOCAL)].copy()
        f["p_wild"] = np.nan
        for i, r in f.iterrows():
            if r["n_treated_clusters"] < 30 and r["n_obs"] > 0:
                f.loc[i, "p_wild"] = did.wild_cluster_p(fit, sp, r["estimand"], B=B_wild)["p"]
        focal_rows.append(f)
        pt = did.pretrend_test(p, sp)
        pre_rows.append(dict(outcome=y, F=pt["F"], df1=pt["df1"], df2=pt["df2"], p=pt["p"], n=pt["n"],
                             **{f"lead{k + 1}": c for k, c in enumerate(pt["coef"])},
                             **{f"lead{k + 1}_se": c for k, c in enumerate(pt["se"])}))
        print(f"{y}: fitted, {time.time() - t0:.0f} s", flush=True)
    res = pd.concat(main_rows, ignore_index=True)
    head = res["estimand"] == "h0_5"
    res.loc[head, "p_holm"] = did.holm(res.loc[head, "p"].to_numpy())
    for i in res.index[head]:
        t = did.tost(res.loc[i, "est"], res.loc[i, "se"])
        res.loc[i, "tost_p"], res.loc[i, "equivalent"] = t["p"], t["equivalent"]
        res.loc[i, "ci90_lo"], res.loc[i, "ci90_hi"] = t["ci90"]
    res.to_csv(panel_dir / "results_main.csv", index=False)
    pd.DataFrame(pre_rows).to_csv(panel_dir / "pretrend.csv", index=False)
    pd.concat(focal_rows, ignore_index=True).to_csv(panel_dir / "focal.csv", index=False)

    # RQ3 point estimates and standard errors
    theta = rq3_table(p, panel_dir, B_wild)
    print(f"RQ3 fitted, {time.time() - t0:.0f} s", flush=True)

    # cluster bootstrap for H1 and the RQ3 Wald test, on the same draws
    draws = did.cluster_draws(p["cluster_id"], B=B)
    for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[v] = "1"                            # one thread per worker process
    rows = []
    with ProcessPoolExecutor(workers, initializer=_init, initargs=(p,)) as ex:
        for b, r in enumerate(ex.map(_draw, draws, chunksize=4)):
            rows.append(r)
            if (b + 1) % 100 == 0:
                print(f"  bootstrap {b + 1}/{B}, {time.time() - t0:.0f} s", flush=True)
    bs = pd.DataFrame(rows)
    bs.to_csv(panel_dir / "bootstrap_draws.csv", index=False)

    main_est = res.set_index(["outcome", "estimand"])["est"]
    diff = main_est[("ln_no2", "h0_5")] - main_est[("ln_pm25", "h0_5")]
    d_bs = (bs["main_ln_no2"] - bs["main_ln_pm25"]).dropna()
    lo, hi = np.percentile(d_bs, [2.5, 97.5])
    pd.DataFrame([dict(diff=diff, ci_lo=lo, ci_hi=hi, se_boot=d_bs.std(), draws=len(d_bs),
                       excludes_zero=bool(lo > 0 or hi < 0))]).to_csv(panel_dir / "h1.csv", index=False)

    wald = []
    for y in OUTCOMES:
        cols = [f"{k}_{y}" for k in MODELS]
        dr = bs[cols].dropna()
        w = did.wald_equal([theta[(k, y)] for k in MODELS], dr.to_numpy())
        wald.append(dict(outcome=y, draws=len(dr), **w))
    pd.DataFrame(wald).to_csv(panel_dir / "rq3_wald.csv", index=False)

    # RQ2
    if "ntl" in p.columns:
        q = p[p["year"].between(2012, 2024)].copy()
        q["ln_ntl"] = np.log(q["ntl"].where(q["ntl"] > 0))
        q["ln_pm25_per_ntl"] = q["ln_pm25"] - q["ln_ntl"]
        out = [table(did.impute(q, did.Spec(y=y, covars=COVARS), did.horizon_estimands()), y)
               for y in ("ln_ntl", "ln_pm25_per_ntl")]
        pd.concat(out, ignore_index=True).to_csv(panel_dir / "rq2.csv", index=False)
    else:
        print("no ntl column: RQ2 not run")
    print(f"done in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
