"""Synthetic control estimates for Singapore and Hong Kong (registration Q19, Q22 to Q24).

python -I scripts/analysis/04_synth.py panel_dir data/final [jobs]

Results are written to panel_dir. Outcomes are read from data/final/outcomes, since the city-states are not in the pooled
panel, and covariates
from data/final/covariates (every CSV has unit_id, year and one column per covariate; built is GHS-BUILT-S, read in 2015).

Donors are the panel districts with no designation under any specification by 2024. Malaysian 2024 values are dropped as
in the pooled panel (Q13). A synthetic control needs every period, so a donor with a missing year (or month) of the
outcome or a missing predictor is dropped, and the count by economy is written to synth_donors.json.

Predictors are the outcome in every pre-designation period, which sets the weights, and ln 2015 population, ln 2015
built-up area and pre-designation means of ln night-time light (from 2012), 2 m temperature, precipitation and wind
speed, which enter by residualising each period's outcome on them (synth.residualize). Each method is run with every
donor designated in turn (rank p-value of the RMSPE ratio) and with designation moved five years earlier.

Checks
main               Singapore first treated 2015 and Hong Kong 2018, ln PM2.5 from 1998 and ln NO2 from 2005
hk_kowloon_east    Hong Kong dated by the 2015 Kowloon East pilot
no_twn             Taiwanese districts dropped from the donors
no_covid           2020 and 2021 dropped from the post-designation years
sgp_monthly        Singapore, monthly outcomes 2005 to 2024 without August to October, ln fire detections within 500 km
                   added as a predictor (designation moved 45 months earlier in the in-time placebo)
hk_within          Kwun Tong against the other 17 districts of Hong Kong, dated 2015, no covariates
hk_within_kai_tak  Kwun Tong and Kowloon City (mean of the two logs) against the other 16, with every pair of the 18
                   districts as a placebo (smallest attainable p-value 1/153)
The two Hong Kong district checks read outcomes/hk_districts_annual.csv (district, year, pm25, no2, max_clip_share)
and are skipped when the file is absent.

Writes synth_results.csv, synth_paths.csv, synth_weights.csv, synth_placebos.csv and synth_donors.json in panel_dir.
"""
import json
import sys
import time
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import synth  # noqa: E402

START = {"ln_pm25": 1998, "ln_no2": 2005}
CLIP_MAX = 0.10  # Q12
BURNING = (8, 9, 10)
PRE_MEANS = ("t2m", "tp", "wind10")
COVID = (2020, 2021)


def pct(x):
    return 100 * (np.exp(x) - 1)


def units(final):
    t = pd.read_csv(final / "treatment.csv", dtype={"unit_id": str})
    first = [c for c in t.columns if c.startswith("first_treated")]
    never = ~(t[first] <= 2024).any(axis=1)
    donors = t.loc[t["in_panel"] & never, ["unit_id", "iso3"]].set_index("unit_id")["iso3"]
    city = t[t["iso3"].isin(["SGP", "HKG"]) & ~t["in_panel"]].set_index("iso3")
    pop = pd.read_csv(final / "units.csv", dtype={"unit_id": str}, usecols=["unit_id", "pop2015"])
    return donors, city, pop.set_index("unit_id")["pop2015"]


def annual(final, outcome, ids, iso):
    var = outcome[3:]
    f, extra = ("pm25_annual.csv", []) if var == "pm25" else ("no2_annual.csv", ["max_clip_share"])
    d = pd.read_csv(final / "outcomes" / f, dtype={"unit_id": str}, usecols=["unit_id", "year", var] + extra)
    d = d[d["unit_id"].isin(ids) & d["year"].between(START[outcome], 2024)].copy()
    if extra:
        d.loc[d["max_clip_share"] > CLIP_MAX, var] = np.nan
    d.loc[d["unit_id"].map(iso).eq("MYS") & d["year"].eq(2024), var] = np.nan
    d.loc[d[var] <= 0, var] = np.nan
    return np.log(d.pivot(index="unit_id", columns="year", values=var))


def monthly(final, outcome, ids, iso):
    var = outcome[3:]
    extra = ["clip_share"] if var == "no2" else []
    d = pd.read_csv(final / "outcomes" / f"{var}_monthly.csv.gz", dtype={"unit_id": str},
                    usecols=["unit_id", "year", "month", var] + extra)
    d = d[d["unit_id"].isin(ids) & ~d["month"].isin(BURNING)].copy()
    if extra:
        d.loc[d["clip_share"] > CLIP_MAX, var] = np.nan
    d.loc[d["unit_id"].map(iso).eq("MYS") & d["year"].eq(2024), var] = np.nan
    d.loc[d[var] <= 0, var] = np.nan
    d["period"] = d["year"] * 100 + d["month"]
    return np.log(d.pivot(index="unit_id", columns="period", values=var))


def read_covariates(final):
    files = sorted((final / "covariates").glob("*.csv")) if (final / "covariates").exists() else []
    cov = None
    for f in files:
        c = pd.read_csv(f, dtype={"unit_id": str})
        cov = c if cov is None else cov.merge(c, on=["unit_id", "year"], how="outer")
    need = list(PRE_MEANS) + ["ntl", "built", "ln_fire_500km"]
    missing = need if cov is None else [c for c in need if c not in cov.columns]
    if missing:
        sys.exit(f"synthetic control predictors missing from data/final/covariates: {missing}")
    return cov


def predictors(cov, pop, ids, first, fire=False):
    """Unit-level predictors for the units in ids, pre-designation means taken over years before `first`."""
    c = cov[cov["unit_id"].isin(ids)]
    pre = c[c["year"] < first]
    X = pd.DataFrame(index=pd.Index(ids, name="unit_id"))
    X["ln_pop2015"] = np.log(pop.reindex(ids))
    X["ln_built2015"] = np.log(c[c["year"] == 2015].set_index("unit_id")["built"].where(lambda s: s > 0))
    for v in PRE_MEANS:
        X[v] = pre.groupby("unit_id")[v].mean()
    ntl = pre[(pre["year"] >= 2012) & (pre["ntl"] > 0)]
    X["ln_ntl_pre"] = np.log(ntl["ntl"]).groupby(ntl["unit_id"]).mean()
    if fire:
        X["ln_fire_500km"] = pre.groupby("unit_id")["ln_fire_500km"].mean()
    return X


def year_of(period):
    return period // 100 if period > 3000 else period


def run(rec, Yd, treated, first, X, jobs, per_year=1, drop=()):
    """All methods for one treated series. Yd has the treated row first, donors after; X is aligned or None."""
    ok = Yd.notna().all(axis=1)
    if X is not None:
        ok &= X.notna().all(axis=1)
    if not ok.iloc[0]:
        print(f"  {rec}: treated series or predictors incomplete, skipped", flush=True)
        return None
    Yd = Yd[ok]
    Yd = Yd.loc[:, [p for p in Yd.columns if year_of(p) not in drop]]
    periods = np.array(Yd.columns)
    T0 = int(sum(year_of(p) < first for p in periods))
    Y = Yd.to_numpy()
    Xa = None if X is None else X[ok].to_numpy()
    rows, paths, weights, placebos = [], [], [], []
    for m in synth.METHODS:
        pr = synth.placebo_ranks(Y, T0, m, Xa, n_jobs=jobs)
        it = synth.in_time_placebo(Y, T0, m, Xa, shift=5 * per_year, n_jobs=jobs)
        r = pr["real"]
        actual = r["path"] + r["gap"]
        rows.append(dict(**rec, method=m, first=first, n_pre=T0, n_post=len(periods) - T0, n_donors=len(Y) - 1,
                         effect=r["effect"], pct=pct(r["effect"]), rmspe_pre=r["rmspe_pre"], rmspe_post=r["rmspe_post"],
                         ratio=r["ratio"], rmspe_pre_over_sd=r["rmspe_pre"] / actual[:T0].std(ddof=1),
                         p_ratio=pr["p_ratio"], p_effect=pr["p_effect"], lam=r.get("lam", np.nan),
                         intime_effect=it["real"]["effect"], intime_p_ratio=it["p_ratio"]))
        paths.append(pd.DataFrame(dict(**rec, method=m, period=periods, actual=actual, synthetic=r["path"])))
        w = pd.Series(r["weights"], index=Yd.index[1:])
        weights.append(w[w > 1e-3].rename("weight").reset_index().assign(**rec, method=m))
        placebos.append(pd.DataFrame(dict(**rec, method=m, donor=Yd.index[1:], effect=pr["placebo_effect"],
                                          ratio=pr["placebo_ratio"])))
        print(f"  {rec} {m}: effect {r['effect']:+.4f}, p {pr['p_ratio']:.3f}", flush=True)
    return rows, paths, weights, placebos


def pair_run(rec, Yd, pair, first):
    """Mean of two treated districts against the rest, with every pair of districts as a placebo."""
    Yd = Yd.dropna()
    names = list(Yd.index)
    periods = np.array(Yd.columns)
    T0 = int(sum(p < first for p in periods))
    rows = []
    for m in synth.METHODS:
        res = {}
        for a, b in combinations(names, 2):
            rest = [n for n in names if n not in (a, b)]
            Y = np.vstack([Yd.loc[[a, b]].mean().to_numpy(), Yd.loc[rest].to_numpy()])
            res[(a, b)] = synth.estimate(Y, T0, m)
        key = tuple(sorted(pair, key=names.index))
        real = res[key]
        ratios = np.array([v["ratio"] for v in res.values()])
        effs = np.array([v["effect"] for v in res.values()])
        rows.append(dict(**rec, method=m, first=first, n_pre=T0, n_post=len(periods) - T0, n_donors=len(names) - 2,
                         effect=real["effect"], pct=pct(real["effect"]), rmspe_pre=real["rmspe_pre"],
                         rmspe_post=real["rmspe_post"], ratio=real["ratio"],
                         p_ratio=np.mean(ratios >= real["ratio"]), p_effect=np.mean(np.abs(effs) >= abs(real["effect"]))))
        print(f"  {rec} {m}: effect {real['effect']:+.4f}, p {rows[-1]['p_ratio']:.3f} over {len(res)} pairs", flush=True)
    return rows


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    panel_dir, final = Path(sys.argv[1]), Path(sys.argv[2])
    jobs = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    donors, city, pop = units(final)
    iso = pd.concat([donors, pd.Series(city.index, index=city["unit_id"])])
    cov = read_covariates(final)
    out = dict(rows=[], paths=[], weights=[], placebos=[])
    log = {}
    t0 = time.time()

    def add(res):
        if res:
            for k, v in zip(("rows", "paths", "weights", "placebos"), res):
                out[k].extend(v)

    def series(outcome, tid, pool, first, fire=False, frequency="annual"):
        ids = [tid] + list(pool)
        Y = (annual if frequency == "annual" else monthly)(final, outcome, ids, iso).reindex(ids)
        X = predictors(cov, pop, ids, first, fire)
        dropped = Y.iloc[1:].isna().any(axis=1) | X.iloc[1:].isna().any(axis=1)
        log_key = f"{frequency}_{outcome}_{tid}_{first}_{len(pool)}"
        log[log_key] = dict(donors=len(pool), dropped=int(dropped.sum()),
                            dropped_by_economy=iso.reindex(Y.index[1:][dropped.to_numpy()]).value_counts().to_dict())
        return Y, X

    for c in ("SGP", "HKG"):
        tid, first = city.loc[c, "unit_id"], int(city.loc[c, "first_treated"])
        for y in START:
            Y, X = series(y, tid, donors.index, first)
            add(run(dict(check="main", unit=c, outcome=y), Y, tid, first, X, jobs))
            add(run(dict(check="no_covid", unit=c, outcome=y), Y, tid, first, X, jobs, drop=COVID))
            pool = donors.index[donors != "TWN"]
            Y2, X2 = series(y, tid, pool, first)
            add(run(dict(check="no_twn", unit=c, outcome=y), Y2, tid, first, X2, jobs))
            if c == "HKG":
                ke = int(city.loc[c, "first_treated_hk_kowloon_east"])
                Y3, X3 = series(y, tid, donors.index, ke)
                add(run(dict(check="hk_kowloon_east", unit=c, outcome=y), Y3, tid, ke, X3, jobs))
            print(f"{c} {y} done, {time.time() - t0:.0f} s", flush=True)

    tid, first = city.loc["SGP", "unit_id"], int(city.loc["SGP", "first_treated"])
    for y in START:
        Y, X = series(y, tid, donors.index, first, fire=True, frequency="monthly")
        add(run(dict(check="sgp_monthly", unit="SGP", outcome=y), Y, tid, first, X, jobs, per_year=12 - len(BURNING)))
    print(f"Singapore monthly done, {time.time() - t0:.0f} s", flush=True)

    hk = final / "outcomes" / "hk_districts_annual.csv"
    if hk.exists():
        d = pd.read_csv(hk)
        d.loc[d["max_clip_share"] > CLIP_MAX, "no2"] = np.nan
        ke = int(city.loc["HKG", "first_treated_hk_kowloon_east"])
        for y in START:
            v = y[3:]
            w = d[d["year"] >= START[y]].pivot(index="district", columns="year", values=v)
            w = np.log(w.where(w > 0))
            order = ["Kwun Tong"] + [n for n in w.index if n != "Kwun Tong"]
            add(run(dict(check="hk_within", unit="Kwun Tong", outcome=y), w.loc[order], "Kwun Tong", ke, None, jobs))
            out["rows"].extend(pair_run(dict(check="hk_within_kai_tak", unit="Kwun Tong + Kowloon City", outcome=y),
                                        w, ("Kwun Tong", "Kowloon City"), ke))
    else:
        print("outcomes/hk_districts_annual.csv not found: the within-Hong Kong checks are not run")

    pd.DataFrame(out["rows"]).to_csv(panel_dir / "synth_results.csv", index=False)
    for k in ("paths", "weights", "placebos"):
        pd.concat(out[k], ignore_index=True).to_csv(panel_dir / f"synth_{k}.csv", index=False)
    (panel_dir / "synth_donors.json").write_text(json.dumps(log, indent=2))
    print(f"done in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
