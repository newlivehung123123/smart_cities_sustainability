"""Checks of did.py on simulated panels only. No file in data/ is read.

python -I scripts/analysis/test_did.py [reps]

Each check prints one line and stops the run with an AssertionError if it fails. reps (default 200) sets the number of
simulated panels for the coverage, size and bootstrap checks.
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import did  # noqa: E402

REPS = int(sys.argv[1]) if len(sys.argv) > 1 else 200


def simulate(rng, n_econ=6, per_econ=100, per_cluster=8, years=range(2005, 2025), share_treated=0.3,
             tau=None, lead=0.0, rho=0.5, sd_cluster=0.05, sd_unit=0.05, covar=True):
    """Panel shaped like the study panel: districts nested in clusters nested in economies, size quartiles,
    staggered first treated years 2017 to 2024, AR(1) district shocks and cluster-year shocks.

    tau(rel) gives the effect at rel years after designation (default 0). lead adds an effect in the two years before.
    """
    years = np.array(list(years))
    T = len(years)
    rows = []
    size_trend = np.cumsum(rng.normal(0, 0.02, (4, T)), axis=1)  # common to all economies, as in the model
    for e in range(n_econ):
        n = per_econ
        cl = np.arange(n) // per_cluster
        size = rng.integers(0, 4, n)
        treated = rng.random(n) < share_treated
        coh = np.where(treated, rng.integers(2017, 2025, n), np.nan)
        econ_trend = np.cumsum(rng.normal(0, 0.03, T))
        a = rng.normal(3.0, 0.4, n)
        cshock = rng.normal(0, sd_cluster, (cl.max() + 1, T))
        u = np.zeros((n, T))
        u[:, 0] = rng.normal(0, sd_unit, n)
        for t in range(1, T):
            u[:, t] = rho * u[:, t - 1] + rng.normal(0, sd_unit * np.sqrt(1 - rho ** 2), n)
        for i in range(n):
            x = rng.normal(0, 1, T) + (0.5 if treated[i] else 0.0)
            for t, yr in enumerate(years):
                rel = yr - coh[i]
                eff = 0.0
                if treated[i] and rel >= 0 and tau is not None:
                    eff = tau(rel)
                if treated[i] and -2 <= rel <= -1:
                    eff += lead
                y = a[i] + econ_trend[t] + size_trend[size[i], t] + (0.1 * x[t] if covar else 0.0) + eff \
                    + cshock[cl[i], t] + u[i, t]
                rows.append((f"e{e}_{i}", e, f"e{e}_c{cl[i]}", size[i], yr, coh[i], y, x[t], eff))
    d = pd.DataFrame(rows, columns=["unit_id", "econ", "cluster_id", "size", "year", "cohort", "y", "x", "eff"])
    d["econ_year"] = d["econ"].astype(str) + "_" + d["year"].astype(str)
    d["size_year"] = d["size"].astype(str) + "_" + d["year"].astype(str)
    return d


def spec(covar=True):
    return did.Spec(y="y", covars=("x",) if covar else ())


def check(name, ok, detail):
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}", flush=True)
    assert ok, name


def t_demean_matches_projection(rng):
    d = simulate(rng, n_econ=3, per_econ=40)
    fes = did._codes(d, ("unit_id", "econ_year", "size_year"))
    y = d["y"].to_numpy()
    ap, sweeps = did.demean(y, fes)
    Z = sparse.hstack([did._indicator(c, g) for c, g in fes]).toarray()
    direct = y - Z @ np.linalg.lstsq(Z, y, rcond=None)[0]
    err = np.abs(ap[:, 0] - direct).max()
    check("alternating projections equal the direct projection", err < 1e-8, f"max diff {err:.1e}, {sweeps} sweeps")


def t_recovery(rng):
    tau = lambda r: -0.05 - 0.01 * min(r, 5)
    d = simulate(rng, n_econ=8, per_econ=200, tau=tau)
    f = did.impute(d, spec(), did.horizon_estimands())
    est = f.estimates
    t = f.tau
    truth = {"h0_5": t.loc[t["_rel"].between(0, 5), "eff"].mean(), "all": t["eff"].mean()}
    truth.update({f"h{h}": tau(h) for h in range(6)})
    z = {k: (est.loc[k, "est"] - v) / est.loc[k, "se"] for k, v in truth.items()}
    worst = max(z, key=lambda k: abs(z[k]))
    check("effects by horizon recovered", max(abs(v) for v in z.values()) < 3.5,
          f"h0_5 {est.loc['h0_5', 'est']:.4f} (true {truth['h0_5']:.4f}, se {est.loc['h0_5', 'se']:.4f}); "
          f"largest |z| {abs(z[worst]):.2f} at {worst}")
    check("every treated district-year imputed", f.n_not_imputed == 0, f"{len(t)} imputed")


def t_coverage(rng):
    hit, hit_all, ses, ests = 0, 0, [], []
    t0 = time.time()
    for _ in range(REPS):
        d = simulate(rng, n_econ=5, per_econ=60, per_cluster=6, tau=lambda r: -0.03)
        f = did.impute(d, spec(), {"h0_5": lambda t: t["_rel"].between(0, 5), "all": lambda t: np.ones(len(t))})
        e = f.estimates
        hit += abs(e.loc["h0_5", "est"] + 0.03) <= 1.96 * e.loc["h0_5", "se"]
        hit_all += abs(e.loc["all", "est"] + 0.03) <= 1.96 * e.loc["all", "se"]
        ses.append(e.loc["h0_5", "se"])
        ests.append(e.loc["h0_5", "est"])
    cov, cov_all = hit / REPS, hit_all / REPS
    lo = 0.95 - 3 * np.sqrt(0.95 * 0.05 / REPS)
    check("95 percent intervals cover a constant effect", cov >= lo and cov_all >= lo,
          f"coverage {cov:.3f} (headline), {cov_all:.3f} (all years); mean se {np.mean(ses):.4f}, "
          f"sd of estimates {np.std(ests):.4f}, bias {np.mean(ests) + 0.03:+.4f}; {time.time() - t0:.0f} s")


def t_heterogeneous_conservative(rng):
    """Effects that differ across districts within a cohort-year: the variance should not be too small."""
    hit = 0
    n = max(REPS // 2, 50)
    for _ in range(n):
        d = simulate(rng, n_econ=5, per_econ=60, per_cluster=6, tau=lambda r: -0.03)
        het = rng.normal(0, 0.05, d["unit_id"].nunique())
        codes = pd.factorize(d["unit_id"])[0]
        D = d["cohort"].notna() & (d["year"] >= d["cohort"])
        d.loc[D, "y"] += het[codes[D.to_numpy()]]
        d.loc[D, "eff"] += het[codes[D.to_numpy()]]
        f = did.impute(d, spec(), {"h0_5": lambda t: t["_rel"].between(0, 5)})
        truth = f.tau.loc[f.tau["_rel"].between(0, 5), "eff"].mean()
        e = f.estimates.loc["h0_5"]
        hit += abs(e["est"] - truth) <= 1.96 * e["se"]
    check("intervals cover the sample effect when effects differ by district", hit / n >= 0.95 - 3 * np.sqrt(0.0475 / n),
          f"coverage {hit / n:.3f} over {n} panels")


def t_not_imputable(rng):
    d = simulate(rng, n_econ=3, per_econ=60, tau=lambda r: -0.05)
    # every district of economy 0 in size group 0 is treated from 2019, so its size-group-by-year cells after 2018 are
    # still fitted from the other economies; make one economy-year fully treated instead
    e0 = d["econ"] == 0
    d.loc[e0, "cohort"] = np.where(d.loc[e0, "cohort"].notna(), d.loc[e0, "cohort"], 2024)
    f = did.impute(d, spec(), {"all": lambda t: np.ones(len(t))})
    expected = int((e0 & (d["year"] == 2024)).sum())
    check("treated district-years without an untreated district in the same economy and year are dropped",
          f.n_not_imputed == expected, f"{f.n_not_imputed} dropped, {expected} expected")
    d2 = simulate(rng, n_econ=3, per_econ=60, tau=lambda r: -0.05)
    first = d2["unit_id"] == d2.loc[d2["cohort"].notna(), "unit_id"].iloc[0]
    d2.loc[first, "cohort"] = 2005
    f2 = did.impute(d2, spec(), {"all": lambda t: np.ones(len(t))})
    check("a district treated in every year cannot be imputed", f2.n_not_imputed == int(first.sum()),
          f"{f2.n_not_imputed} dropped, {int(first.sum())} expected")


def t_pretrend(rng):
    """At the study's cluster count (about 300). With 50 clusters the clustered F test of eight leads rejects about 11
    to 17 percent of the time; at 300 clusters, about 6 percent (400 panels)."""
    big = dict(n_econ=6, per_econ=200, per_cluster=4)
    rej = 0
    for _ in range(REPS):
        d = simulate(rng, tau=lambda r: -0.03, **big)
        rej += did.pretrend_test(d, spec())["p"] < 0.05
    size = rej / REPS
    check("pre-trend test size near 5 percent with 300 clusters", size <= 0.05 + 3 * np.sqrt(0.0475 / REPS),
          f"rejects {size:.3f}")
    power = np.mean([did.pretrend_test(simulate(rng, lead=-0.02, **big), spec())["p"] < 0.05 for _ in range(50)])
    check("pre-trend test detects a 2 percent anticipation effect", power >= 0.8, f"rejects {power:.2f} of 50")


def t_holm_tost():
    from statsmodels.stats.multitest import multipletests
    p = np.array([0.01, 0.04, 0.03, 0.2])
    ok = np.allclose(did.holm(p), multipletests(p, method="holm")[1])
    check("Holm adjustment matches statsmodels", ok, f"{did.holm(p).round(3)}")
    a = did.tost(0.0, 0.01)
    b = did.tost(0.0, 0.05)
    c = did.tost(-0.06, 0.01)
    check("TOST", a["equivalent"] and not b["equivalent"] and not c["equivalent"],
          f"p {a['p']:.4f}, {b['p']:.3f}, {c['p']:.3f}")


def t_wild(rng):
    """Few clusters: wild bootstrap p-values under the null should reject about 5 percent of the time."""
    n = max(REPS // 2, 50)
    rej, rej_norm = 0, 0
    t0 = time.time()
    for _ in range(n):
        d = simulate(rng, n_econ=2, per_econ=60, per_cluster=6, tau=lambda r: 0.0, sd_cluster=0.08)
        f = did.impute(d, spec(), {"h0_5": lambda t: t["_rel"].between(0, 5)})
        w = did.wild_cluster_p(f, spec(), "h0_5", B=399, seed=int(rng.integers(1 << 31)))
        rej += w["p"] < 0.05
        rej_norm += did.p_two_sided(f.estimates.loc["h0_5", "est"], f.estimates.loc["h0_5", "se"]) < 0.05
    check("wild cluster bootstrap size with 20 clusters", rej / n <= 0.05 + 3 * np.sqrt(0.0475 / n),
          f"bootstrap rejects {rej / n:.3f}, normal rejects {rej_norm / n:.3f} over {n} panels; {time.time() - t0:.0f} s")


def t_cluster_bootstrap(rng):
    d = simulate(rng, n_econ=4, per_econ=60, per_cluster=6, tau=lambda r: -0.03)
    sp = spec()
    est = lambda t: t["_rel"].between(0, 5)
    f = did.impute(d, sp, {"h0_5": est})
    draws = [did.point(did.resample(d, g, sp), sp, est) for g in did.cluster_draws(d["cluster_id"], B=199)]
    sd = np.nanstd(draws)
    se = f.estimates.loc["h0_5", "se"]
    check("cluster bootstrap spread close to the analytic standard error", 0.6 < sd / se < 1.6,
          f"bootstrap sd {sd:.4f}, analytic se {se:.4f}")
    theta = np.array([-0.03, -0.031, -0.029])
    cov = np.diag([1e-4] * 3)
    draws3 = rng.multivariate_normal(theta, cov, size=999)
    w = did.wald_equal(theta, draws3)
    w2 = did.wald_equal(np.array([-0.03, -0.06, 0.0]), draws3)
    check("Wald test of equal effects", w["p"] > 0.5 and w2["p"] < 0.001, f"p {w['p']:.2f} and {w2['p']:.1e}")


def main():
    rng = np.random.default_rng(1)
    t0 = time.time()
    t_demean_matches_projection(rng)
    t_holm_tost()
    t_recovery(rng)
    t_not_imputable(rng)
    t_cluster_bootstrap(rng)
    t_coverage(rng)
    t_heterogeneous_conservative(rng)
    t_pretrend(rng)
    t_wild(rng)
    print(f"all checks passed in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
