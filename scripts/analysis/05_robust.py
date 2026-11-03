"""Robustness checks of the headline effects (registration Q16, Q19, Q23, Q24, and the deviations reported in the paper).

python -I scripts/analysis/05_robust.py panel_dir data/final part [draws] [workers]

part is one of estimators, rival, coding, inference, honest, extras. Each part writes robust_{part}.csv in panel_dir with
the columns check, group, outcome, est, se, p, ci_lo, ci_hi, n_obs, n_clusters, note. Unless a row says otherwise, est is
the headline effect (mean effect over years 0 to 5 after designation on the log outcome) from the imputation estimator
with the main fixed effects and covariates, and se is clustered by first-level unit. draws (default 499) sets the
bootstrap draws; randomisation inference uses 1,000 permutations and the wild bootstrap 9,999 draws. workers (default 6)
sets the processes for the bootstrap and permutation loops.

estimators  Callaway and Sant'Anna (2021) doubly robust, de Chaisemartin and D'Haultfoeuille, stacked, static two-way fixed
            effects and its Goodman-Bacon decomposition (bacon_{outcome}.csv), entropy balancing (Hainmueller 2012),
            2015 population weights
rival       2020 and 2021 dropped, outcomes without the burning-season months, spillovers to neighbouring districts,
            one year of anticipation, each economy dropped in turn, capital cities dropped, urban centres as the unit
coding      alternative designation codings, alternative programmes coded as treated or dropped, balanced panel,
            area-weighted outcomes and NO2 without the clipping rule
inference   Conley standard errors, randomisation inference within economies, wild cluster bootstrap by economy
honest      Sun and Abraham (2021) event study (sa_event.csv) and the Rambachan and Roth (2023) relative-magnitude
            confidence sets for the headline effect (honest.csv)
extras      income group in the designation year (World Bank OGHIST), programme-model checks, size group, part or whole
            designation, years 6 and 7, NO2 by calendar month, night-time light 2005 to 2024
"""
import os
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor
from importlib import import_module
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import alt  # noqa: E402
import did  # noqa: E402
import honest  # noqa: E402

mde = import_module("02_mde")
est3 = import_module("03_estimate")

OUTCOMES, COVARS, HEAD = mde.OUTCOMES, mde.COVARS, est3.HEAD
COLS = ["check", "group", "outcome", "est", "se", "p", "ci_lo", "ci_hi", "n_obs", "n_clusters", "note"]
LAST = 2024
BURN = {**{c: (2, 3, 4) for c in ("KHM", "LAO", "MMR", "THA", "VNM")}, **{c: (8, 9, 10) for c in ("IDN", "MYS", "BRN")}}
CAPITALS = ("Tokyo", "Seoul", "Taipei", "Bangkok", "Dki Jakarta", "Ha Noi", "Phnom Penh", "Vientiane Capital",
            "Kuala Lumpur", "Brunei-Muara", "Ulaanbaatar", "Dili", "NCR, City of Manila, First District",
            "NCR, Second District", "NCR, Third District", "NCR, Fourth District")
ALT_PROGRAMMES = ("jp_joint", "jp_digital_garden", "kr_campus", "kr_theme_complex", "my_rating_2023",
                  "ph_digital_cities")
MODEL_COLS = {"implementation support": "impl", "certification": "cert", "network membership": "ascn"}
CLIP_MAX = 0.10


# ---------------------------------------------------------------- helpers

def row(check, outcome, est, se=np.nan, group="", ci=None, p=None, n_obs=np.nan, n_clusters=np.nan, note=""):
    if ci is None:
        ci = (est - 1.96 * se, est + 1.96 * se) if np.isfinite(se) else (np.nan, np.nan)
    if p is None:
        p = did.p_two_sided(est, se) if np.isfinite(se) and se > 0 else np.nan
    return dict(check=check, group=group, outcome=outcome, est=est, se=se, p=p, ci_lo=ci[0], ci_hi=ci[1],
                n_obs=n_obs, n_clusters=n_clusters, note=note)


def imp(p, y, check, estimands=None, note="", **kw):
    """did.impute rows, one per estimand (the headline, with group "", by default)."""
    estimands = estimands or {"": HEAD}
    fit = did.impute(p, did.Spec(y=y, covars=COVARS, **kw), estimands)
    out = [row(check, y, r["est"], r["se"], group=g, n_obs=r["n_obs"], n_clusters=r["n_clusters"], note=note)
           for g, r in fit.estimates.iterrows()]
    return out, fit


def boot_row(check, y, est, draws, note="", n_obs=np.nan, n_clusters=np.nan):
    d = np.asarray(draws, float)
    d = d[np.isfinite(d)]
    se = float(d.std(ddof=1))
    lo, hi = np.percentile(d, [2.5, 97.5])
    return row(check, y, est, se, ci=(lo, hi), n_obs=n_obs, n_clusters=n_clusters,
               note=f"cluster bootstrap, {len(d)} draws, percentile interval" + (f"; {note}" if note else ""))


def districts(p):
    return p.drop_duplicates("unit_id").set_index("unit_id")


def designated(p):
    """District-level mask of designation by the last panel year."""
    return districts(p)["cohort"].le(LAST)


_G = {}


def _init(state):
    _G.update(state)


def pmap(fn, args, workers, state):
    """fn over args in worker processes, each holding state in _G."""
    if workers <= 1:
        _init(state)
        return [fn(a) for a in args]
    for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[v] = "1"
    with ProcessPoolExecutor(workers, initializer=_init, initargs=(state,)) as ex:
        return list(ex.map(fn, args, chunksize=max(1, len(args) // (workers * 8))))


def load(panel_dir, final):
    p = mde.load(panel_dir)
    p["cohort"] = p["first_treated"]
    p["ln_pop"] = np.log(p["pop2015"])
    u = pd.read_csv(final / "units.csv", dtype={"unit_id": str}, usecols=["unit_id", "uc_main", "urban_city_rule"])
    return p.merge(u, on="unit_id", how="left", validate="many_to_one")


# ---------------------------------------------------------------- estimators

def _cs_draw(seed):
    wd = _G["wd"]
    w = wd.take(alt.cluster_index(wd, np.random.default_rng(seed)))
    return alt.aggregate(alt.cs_dr(w, COVARS)), alt.aggregate(alt.dcdh(w))


EB_TOL = 1e-3


def eb_sample(p, y):
    """Designated districts with weight 1 and comparison districts (not designated by 2024, in economies with
    designated districts) with entropy-balancing weights on ln 2015 population, the mean log outcome in 2005 to 2010,
    2011 to 2013 and 2014 to 2016, and the economy shares, scaled to mean 1. Comparison districts with a missing
    moment are dropped."""
    first = districts(p)
    tr = first["cohort"].le(LAST)
    econ = sorted(first.loc[tr, "iso3"].unique())
    ctrl = ~tr & first["iso3"].isin(econ)
    ly = p.pivot(index="unit_id", columns="year", values=y)
    M = pd.DataFrame({"ln_pop": first["ln_pop"],
                      "y05_10": ly.loc[:, 2005:2010].mean(1), "y11_13": ly.loc[:, 2011:2013].mean(1),
                      "y14_16": ly.loc[:, 2014:2016].mean(1)})
    for c in econ[1:]:
        M[f"econ_{c}"] = (first["iso3"] == c).astype(float)
    ok = M.notna().all(1)
    target = M[tr & ok].mean().to_numpy()
    C = M[ctrl & ok]
    w, gap = alt.entropy_weights(C.to_numpy(), target)
    wts = pd.Series(1.0, index=first.index[tr])
    wts = pd.concat([wts, pd.Series(w * len(w), index=C.index)])
    s = p[p["unit_id"].isin(wts.index)].copy()
    s["w_eb"] = s["unit_id"].map(wts)
    ess = float(w.sum() ** 2 / (w ** 2).sum())
    return s, dict(gap=gap, controls=len(w), ess=ess)


def _eb_draw(args):
    """NaN when the resample cannot be balanced, which happens when an economy keeps designated districts but loses
    every comparison district, so the economy share has no feasible weights and the solver diverges."""
    draw, y = args
    q = did.resample(_G["p"], draw, did.Spec(y=y))
    with np.errstate(over="ignore", invalid="ignore"):
        s, info = eb_sample(q, y)
    if not np.isfinite(info["gap"]) or info["gap"] > EB_TOL or not np.isfinite(s["w_eb"]).all():
        return np.nan
    try:
        return alt.wpoint(s, did.Spec(y=y, covars=COVARS), "w_eb", HEAD)
    except np.linalg.LinAlgError:
        return np.nan


def part_estimators(p, panel_dir, B, workers):
    rows = []
    for y in OUTCOMES:
        t0 = time.time()
        sp = did.Spec(y=y, covars=COVARS)
        r, fit = imp(p, y, "main")
        rows += r

        wd = alt.Wide(p, y, covars=COVARS)
        cs_cells, dc_cells = alt.cs_dr(wd, COVARS), alt.dcdh(wd)
        draws = pmap(_cs_draw, list(range(20261200, 20261200 + B)), workers, dict(wd=wd))
        cs_d, dc_d = zip(*draws)
        rows.append(boot_row("Callaway and Sant'Anna, doubly robust", y, alt.aggregate(cs_cells), cs_d,
                             note=f"{len(cs_cells)} cohort-year cells, not-yet-designated comparisons in the economy",
                             n_obs=int(cs_cells.loc[cs_cells['e'].between(0, 5), 'n'].sum())))
        rows.append(boot_row("de Chaisemartin and D'Haultfoeuille", y, alt.aggregate(dc_cells), dc_d,
                             note=f"{len(dc_cells)} cohort-economy-year cells",
                             n_obs=int(dc_cells.loc[dc_cells['e'].between(0, 5), 'n'].sum())))

        st = alt.stacked(p, sp)
        rows.append(row("stacked", y, st["est"], st["se"], n_obs=st["n_obs"], n_clusters=st["clusters"],
                        note=f"{st['stacks']} stacks, years g-5 to g+5"))
        tw = alt.twfe(p, sp)
        rows.append(row("static two-way fixed effects", y, tw["est"], tw["se"], n_obs=tw["n_obs"],
                        n_clusters=tw["clusters"], note="all treated years"))
        b = alt.bacon(alt.Wide(p, y))
        b["parts"].to_csv(panel_dir / f"bacon_{y}.csv", index=False)
        forb = b["parts"]["kind"].str.startswith("later vs earlier")
        rows.append(row("Goodman-Bacon two-way estimate", y, b["beta"], n_obs=b["districts"],
                        note=(f"balanced districts {b['districts']}; weights sum {b['weight_sum']:.4f}; recomposed "
                              f"{b['recomposed']:.5f}; weight on comparisons with already-designated districts "
                              f"{b['parts'].loc[forb, 'weight'].sum():.3f}")))

        s, info = eb_sample(p, y)
        e = alt.wimpute(s, sp, "w_eb", {"": HEAD})
        bs = pmap(_eb_draw, [(d, y) for d in did.cluster_draws(p["cluster_id"], B=B, seed=20261104)], workers,
                  dict(p=p))
        bs = np.asarray(bs, float)
        bs = bs[np.isfinite(bs)]
        lo, hi = np.percentile(bs, [2.5, 97.5])
        print(f"entropy balancing {y}: {B - len(bs)} of {B} draws could not be balanced", flush=True)
        rows.append(row("entropy balancing", y, e.loc["", "est"], float(bs.std(ddof=1)), ci=(lo, hi),
                        n_obs=e.loc["", "n_obs"], n_clusters=e.loc["", "n_clusters"],
                        note=(f"bootstrap {len(bs)} of {B} draws re-estimating the weights ({B - len(bs)} draws "
                              f"dropped with a balance gap above {EB_TOL} sd); se given the weights "
                              f"{e.loc['', 'se']:.4f}; {info['controls']} comparison districts, effective number "
                              f"{info['ess']:.0f}, largest balance gap {info['gap']:.1e} sd")))
        pw = alt.wimpute(p, sp, "pop2015", {"": HEAD}, est_w="pop2015")
        rows.append(row("2015 population weights", y, pw.loc["", "est"], pw.loc["", "se"], n_obs=pw.loc["", "n_obs"],
                        n_clusters=pw.loc["", "n_clusters"], note="weighted fit and weighted mean of effects"))
        print(f"estimators {y}: {time.time() - t0:.0f} s", flush=True)
    return rows


# ---------------------------------------------------------------- rival explanations

def monthly_outcomes(p, final, drop_burn):
    """Annual means of the monthly products, without the burning-season months where drop_burn. A district-year needs
    every included month. NO2 follows the clipping rule over the included months."""
    iso = districts(p)["iso3"]
    out = []
    for v, f, extra in (("pm25", "pm25_monthly.csv.gz", []), ("no2", "no2_monthly.csv.gz", ["clip_share"])):
        m = pd.read_csv(final / "outcomes" / f, dtype={"unit_id": str}, usecols=["unit_id", "year", "month", v] + extra)
        m = m[m["unit_id"].isin(iso.index)]
        if drop_burn:
            months = m["unit_id"].map(iso).map(lambda c: BURN.get(c, ()))
            m = m[[mo not in ms for mo, ms in zip(m["month"], months)]]
        g = m.groupby(["unit_id", "year"])
        a = g[v].mean().to_frame(f"m_{v}")
        need = 12 - a.index.get_level_values("unit_id").map(iso).map(lambda c: len(BURN.get(c, ())) if drop_burn
                                                                      else 0).to_numpy()
        a.loc[g[v].count().to_numpy() < need, f"m_{v}"] = np.nan
        if v == "no2":
            a.loc[g["clip_share"].max() > CLIP_MAX, f"m_{v}"] = np.nan
        a[f"ln_m_{v}"] = np.log(a[f"m_{v}"].where(a[f"m_{v}"] > 0))
        out.append(a)
    q = p.merge(pd.concat(out, axis=1).reset_index(), on=["unit_id", "year"], how="left")
    q.loc[(q["iso3"] == "MYS") & (q["year"] == 2024), ["ln_m_pm25", "ln_m_no2"]] = np.nan
    return q


def neighbour_table(panel_dir, final, ids):
    f = panel_dir / "neighbours.csv"
    if f.exists():
        return pd.read_csv(f, dtype=str)
    import geopandas as gpd
    u = gpd.read_parquet(final.parent / "interim" / "units" / "units.parquet", columns=["unit_id", "iso3", "geometry"])
    u = u[u["unit_id"].isin(ids)].reset_index(drop=True)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        b = u.assign(geometry=u.geometry.buffer(0.002))
    j = gpd.sjoin(b, u, predicate="intersects")
    j = j[(j["unit_id_left"] != j["unit_id_right"]) & (j["iso3_left"] == j["iso3_right"])]
    nb = j[["unit_id_left", "unit_id_right"]].rename(columns={"unit_id_left": "unit_id", "unit_id_right": "nb"})
    nb.to_csv(f, index=False)
    return nb


def uc_panel(p):
    """Urban centres (GHSL, uc_main) as the unit: population-weighted means of the members' outcome levels and
    covariates over the members with values, cohort the earliest member cohort, economy and first-level unit of the
    largest member, size groups recomputed on the summed 2015 population."""
    q = p.copy()
    q["uc"] = q["uc_main"].astype(str)
    key = ["uc", "year"]
    vals = {}
    for v in ("pm25", "no2") + COVARS:
        ok = q[v].notna()
        num = (q.loc[ok, v] * q.loc[ok, "pop2015"]).groupby([q.loc[ok, "uc"], q.loc[ok, "year"]]).sum()
        den = q.loc[ok, "pop2015"].groupby([q.loc[ok, "uc"], q.loc[ok, "year"]]).sum()
        vals[v] = num / den
    out = pd.DataFrame(vals)
    out.index.names = key
    out = out.reset_index()
    first = districts(q).reset_index()
    big = first.sort_values("pop2015", ascending=False).drop_duplicates("uc").set_index("uc")
    agg = first.groupby("uc").agg(cohort=("first_treated", "min"), pop2015=("pop2015", "sum"),
                                  members=("unit_id", "size"))
    agg["iso3"], agg["cluster_id"] = big["iso3"], big["cluster_id"]
    agg["size_group"] = pd.qcut(agg["pop2015"], 4, labels=False) + 1
    out = out.merge(agg.reset_index(), on="uc", how="left")
    out = out.rename(columns={"uc": "unit_id"})
    out = out[out["year"].isin(p["year"].unique())]
    out["econ_year"] = out["iso3"] + "_" + out["year"].astype(str)
    out["size_year"] = out["size_group"].astype(str) + "_" + out["year"].astype(str)
    for v in ("pm25", "no2"):
        out[f"ln_{v}"] = np.log(out[v].where(out[v] > 0))
    return out, int(agg.shape[0]), int(agg["cohort"].le(LAST).sum())


def part_rival(p, panel_dir, final):
    rows = []
    first = districts(p)
    des = first["cohort"].le(LAST)
    for y in OUTCOMES:
        rows += imp(p, y, "main")[0]
        rows += imp(p[~p["year"].isin([2020, 2021])], y, "2020 and 2021 dropped")[0]
        rows += imp(p.assign(cohort=p["cohort"].where(p["cohort"] > LAST + 1, p["cohort"] - 1)), y,
                    "one year of anticipation", note="designation year moved one year earlier")[0]
        for c in sorted(p["iso3"].unique()):
            rows += imp(p[p["iso3"] != c], y, "economy dropped", estimands={c: HEAD})[0]
        cap = p["cluster_name"].isin(CAPITALS)
        rows += imp(p[~cap], y, "capital cities dropped",
                    note=f"{p.loc[cap, 'unit_id'].nunique()} districts in capital first-level units dropped; "
                         "Nay Pyi Taw and Putrajaya have no district in the panel")[0]

    for drop_burn, check in ((False, "monthly product, all months"), (True, "burning-season months dropped")):
        q = monthly_outcomes(p, final, drop_burn)
        for v in ("pm25", "no2"):
            rows += imp(q, f"ln_m_{v}", check,
                        note="February to April dropped in KHM, LAO, MMR, THA, VNM; August to October in IDN, MYS, "
                             "BRN" if drop_burn else "mean of the 12 monthly values")[0]

    nb = neighbour_table(panel_dir, final, first.index)
    nb["nb_cohort"] = nb["nb"].map(first["cohort"].where(des))
    uc = first["uc_main"]
    uc_cohort = first["cohort"].where(des).groupby(uc).min()
    exp_cohort = pd.concat([nb.groupby("unit_id")["nb_cohort"].min(),
                            first["uc_main"].map(uc_cohort).rename("nb_cohort")], axis=1).min(1)
    exp_cohort = exp_cohort.reindex(first.index)
    exposed = ~des & exp_cohort.notna()
    for y in OUTCOMES:
        rows += imp(p[~p["unit_id"].isin(exposed[exposed].index)], y, "neighbours of designated districts dropped",
                    note=f"{int(exposed.sum())} undesignated districts that border or share an urban centre with a "
                         "district designated by 2024")[0]
        s = p[p["unit_id"].isin(des[~des].index)].copy()
        s["cohort"] = s["unit_id"].map(exp_cohort)
        rows += imp(s, y, "effect on undesignated neighbours",
                    note="undesignated districts only, treated from the first designation of a bordering district or "
                         "urban-centre partner")[0]

    u, n_uc, n_uc_tr = uc_panel(p)
    for y in OUTCOMES:
        rows += imp(u, y, "urban centre as the unit", note=f"{n_uc} urban centres, {n_uc_tr} designated by 2024")[0]
    return rows


# ---------------------------------------------------------------- coding

def part_coding(p):
    rows = []
    first = districts(p)
    des = first["cohort"].le(LAST)
    for y in OUTCOMES:
        rows += imp(p, y, "main")[0]
        rows += imp(p.assign(cohort=p["first_treated_no_part"]), y, "part-district designations not counted")[0]
        rows += imp(p.assign(cohort=p["first_treated_id_2022"]), y, "Indonesia dated by the 2022 cohort list")[0]
        mou = p["id_mou_only_unit"].fillna(False).astype(bool)
        rows += imp(p[~mou].assign(cohort=p.loc[~mou, "first_treated_id_no_mou_only"]), y,
                    "Indonesian memorandum-only districts dropped",
                    note=f"{p.loc[mou, 'unit_id'].nunique()} districts dropped")[0]
        vnm = p["iso3"].eq("VNM") & ~p["unit_id"].map(des)
        rows += imp(p[~vnm], y, "undesignated Vietnamese districts dropped")[0]
        pref = p["prefecture_named_year"].notna() & ~p["unit_id"].map(des)
        rows += imp(p[~pref], y, "undesignated districts in named prefectures dropped",
                    note=f"{p.loc[pref, 'unit_id'].nunique()} districts dropped")[0]
        city = p["urban_city_rule"].eq(True)
        rows += imp(p[city], y, "urban districts only", note=f"{p.loc[city, 'unit_id'].nunique()} districts")[0]
        for prog in ALT_PROGRAMMES:
            col = p[f"first_treated_{prog}"]
            rows += imp(p.assign(cohort=np.fmin(p["first_treated"], col)), y, "alternative programme coded as treated",
                        estimands={prog: HEAD},
                        note=f"{int((col.le(LAST) & ~p['unit_id'].map(des)).groupby(p['unit_id']).any().sum())} "
                             "districts added")[0]
            drop = col.le(LAST) & ~p["unit_id"].map(des)
            rows += imp(p[~drop], y, "alternative programme districts dropped", estimands={prog: HEAD},
                        note=f"{p.loc[drop, 'unit_id'].nunique()} districts dropped")[0]
        full = p[y].notna().groupby(p["unit_id"]).transform("all")
        rows += imp(p[full], y, "balanced panel",
                    note=f"{p.loc[full, 'unit_id'].nunique()} districts with the outcome in every panel year")[0]
    for y, base in (("ln_pm25_area", "ln_pm25"), ("ln_no2_area", "ln_no2"), ("ln_no2_all", "ln_no2")):
        rows += imp(p, y, {"ln_pm25_area": "area-weighted outcome", "ln_no2_area": "area-weighted outcome",
                           "ln_no2_all": "NO2 without the clipping rule"}[y], note=f"compare {base}")[0]
    return rows


# ---------------------------------------------------------------- inference

def _ri_draw(seed):
    p, first = _G["p"], _G["first"]
    rng = np.random.default_rng(seed)
    perm = pd.Series(np.nan, index=first.index)
    for _, idx in first.groupby("iso3").groups.items():
        perm[idx] = rng.permutation(first.loc[idx, "cohort"].to_numpy())
    q = p.assign(cohort=p["unit_id"].map(perm))
    return [did.point(q, did.Spec(y=y, covars=COVARS), HEAD) for y in OUTCOMES]


def part_inference(p, final, workers, n_perm=1000, B_wild=9_999):
    import geopandas as gpd
    rows = []
    first = districts(p)
    u = gpd.read_parquet(final.parent / "interim" / "units" / "units.parquet", columns=["unit_id", "geometry"])
    u = u[u["unit_id"].isin(first.index)].set_index("unit_id")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pt = u.geometry.representative_point()
    coords = pd.DataFrame({"lat": pt.y, "lon": pt.x})
    obs = {}
    for y in OUTCOMES:
        sp = did.Spec(y=y, covars=COVARS)
        r, fit = imp(p, y, "main", estimands={"h0_5": HEAD})
        r[0]["group"] = ""
        rows += r
        est = fit.estimates.loc["h0_5", "est"]
        obs[y] = est
        cs = alt.conley_se(fit, sp, "h0_5", coords, (100, 250))
        for h in (100, 250):
            rows.append(row(f"Conley standard error, {h} km", y, est, cs[h], n_obs=r[0]["n_obs"],
                            note=f"uniform kernel on district distance; cluster formula check {cs['cluster_check']:.5f}"))
        spi = did.Spec(y=y, covars=COVARS, cluster="iso3")
        fi = did.impute(p, spi, {"h0_5": HEAD})
        w = did.wild_cluster_p(fi, spi, "h0_5", B=B_wild)
        rows.append(row("economy clusters, wild bootstrap", y, est, fi.estimates.loc["h0_5", "se"], p=w["p"],
                        n_clusters=w["clusters"], note=f"Webb weights, {B_wild} draws, restricted, studentised; "
                                                       "se is the analytic economy-clustered value"))
    draws = pmap(_ri_draw, list(range(20261300, 20261300 + n_perm)), workers, dict(p=p, first=first))
    D = pd.DataFrame(draws, columns=list(OUTCOMES))
    for y in OUTCOMES:
        d = D[y].dropna().to_numpy()
        pval = (1 + (np.abs(d) >= abs(obs[y])).sum()) / (1 + len(d))
        rows.append(row("randomisation inference within economies", y, obs[y], float(d.std(ddof=1)), p=pval,
                        ci=(np.nan, np.nan), note=f"{len(d)} permutations of the designation year across districts "
                                                  "of the same economy; se is the sd of the permutation estimates"))
    return rows, D


# ---------------------------------------------------------------- honest

def part_honest(p, panel_dir, mbars=(0.0, 0.5, 1.0, 1.5, 2.0)):
    rows, ev_all, hon = [], [], []
    for y in OUTCOMES:
        t0 = time.time()
        sa = alt.sun_abraham(p, did.Spec(y=y, covars=COVARS))
        ev = sa["event"].assign(outcome=y)
        ev_all.append(ev)
        est, se = alt.sa_aggregate(sa)
        rows.append(row("Sun and Abraham", y, est, se, n_clusters=sa["clusters"],
                        note="never-designated comparison, year -1 reference"))
        sel = (ev["e"].between(-8, -2) | ev["e"].between(0, 5)).to_numpy()
        idx = np.flatnonzero(sel)
        e = ev["e"].to_numpy()[idx]
        assert list(e) == list(range(-8, -1)) + list(range(0, 6)), e
        beta, Sigma = ev["est"].to_numpy()[idx], sa["V"][np.ix_(idx, idx)]
        n_pre = 7
        n = ev["n"].to_numpy()[idx][n_pre:]
        l = n / n.sum()
        for m in mbars:
            cs = honest.confidence_set(beta, Sigma, l, n_pre, m)
            hon.append(dict(outcome=y, mbar=m, theta=float(l @ beta[n_pre:]), lo=cs["lo"], hi=cs["hi"],
                            one_interval=cs["one_interval"]))
        bd = honest.breakdown(beta, Sigma, l, n_pre)
        hon.append(dict(outcome=y, mbar=np.nan, theta=float(l @ beta[n_pre:]), lo=np.nan, hi=np.nan,
                        one_interval=np.nan, breakdown=bd))
        rows.append(row("Rambachan and Roth breakdown", y, float(l @ beta[n_pre:]), ci=(np.nan, np.nan), p=np.nan,
                        note=f"largest relative magnitude Mbar with zero outside the set: {bd:.3f}"))
        print(f"honest {y}: {time.time() - t0:.0f} s", flush=True)
    pd.concat(ev_all, ignore_index=True).to_csv(panel_dir / "sa_event.csv", index=False)
    pd.DataFrame(hon).to_csv(panel_dir / "honest.csv", index=False)
    return rows


# ---------------------------------------------------------------- extras

def income_groups(final):
    """Income group of each economy by World Bank data year, from OGHIST (sheet Country Analytical History)."""
    x = pd.read_excel(final.parent / "raw" / "worldbank" / "OGHIST.xlsx", sheet_name="Country Analytical History",
                      header=None)
    years = pd.to_numeric(x.iloc[5], errors="coerce")
    cols = [j for j in range(x.shape[1]) if np.isfinite(years[j])]
    body = x.iloc[6:]
    body = body[body[0].astype(str).str.fullmatch(r"[A-Z]{3}")]
    g = body.set_index(0)[cols]
    g.columns = years[cols].astype(int).to_numpy()
    return g.stack().rename("group").reset_index().rename(columns={0: "iso3", "level_1": "data_year"})


def by_model(p, cols):
    """Model of each designated district from the by-model designation years: the model whose year equals the first
    designation year, ties in the order of cols."""
    first = districts(p)
    m = pd.Series(np.nan, index=first.index, dtype=object)
    for model, c in reversed(list(cols.items())):
        m[first[c].eq(first["first_treated"]) & first["first_treated"].le(LAST)] = model
    return m


def rq3_by(p, model_of_unit, model, censor=False, cols=None):
    """Treated: first designation under model. Districts first designated under another model are kept only until the
    year before that designation. With censor, district-years of model districts from a later designation under
    another model are dropped too."""
    m = p["unit_id"].map(model_of_unit)
    other = p["first_treated"].le(LAST) & (m != model)
    s = p[~(other & (p["year"] >= p["first_treated"]))].copy()
    s.loc[other.loc[s.index], "cohort"] = np.nan
    if censor:
        later = pd.concat([s[c].where(s[c] > s["first_treated"]) for k, c in cols.items() if k != model], axis=1).min(1)
        s = s[~((s["unit_id"].map(model_of_unit) == model) & (s["year"] >= later))]
    return s


def part_extras(p, final):
    rows = []
    inc = income_groups(final).set_index(["iso3", "data_year"])["group"]
    p = p.copy()
    p["income"] = [inc.get((i, int(c) - 1), np.nan) if c <= LAST else np.nan for i, c in zip(p["iso3"], p["cohort"])]
    est = {}
    for gname in ("H", "UM", "LM", "L"):
        est[f"income {gname}"] = (lambda g: lambda t: HEAD(t) & (t["income"] == g))(gname)
    for k in range(1, 5):
        est[f"size group {k}"] = (lambda k: lambda t: HEAD(t) & (t["size_group"] == k))(k)
    est["part of district"] = lambda t: HEAD(t) & (t["first_is_part"] == True)  # noqa: E712
    est["whole district"] = lambda t: HEAD(t) & (t["first_is_part"] == False)  # noqa: E712
    est.update({k: v for k, v in did.horizon_estimands(0, 7, all_=False).items() if k in ("h0_7", "h6", "h7")})
    for y in OUTCOMES:
        r, fit = imp(p, y, "heterogeneity", estimands=est)
        rows += r

    cols = {k: f"first_treated_{v}" for k, v in MODEL_COLS.items()}
    cols_sc = {"implementation support": "first_treated_impl_sc", "certification": "first_treated_cert_sc",
               "network membership": "first_treated_ascn"}
    main_m = districts(p)["first_model"].map(est3.model_of)
    bm, bm_sc = by_model(p, cols), by_model(p, cols_sc)
    counts = {k: (int((main_m == k).sum()), int((bm == k).sum()), int((bm_sc == k).sum())) for k in MODEL_COLS}
    dual = districts(p)["first_model"].eq("certification; implementation support")
    for model in MODEL_COLS:
        c = counts[model]
        for y in OUTCOMES:
            rows += imp(rq3_by(p, bm, model), y, "RQ3 from by-model years", estimands={model: HEAD},
                        note=f"districts {c[1]} (main coding {c[0]})")[0]
            rows += imp(rq3_by(p[~p["unit_id"].map(dual)], main_m, model), y, "RQ3 without dual-model districts",
                        estimands={model: HEAD}, note=f"{int(dual.sum())} districts dropped")[0]
            rows += imp(rq3_by(p, main_m, model, censor=True, cols=cols), y,
                        "RQ3 censored at a later designation under another model", estimands={model: HEAD})[0]
            rows += imp(rq3_by(p, bm_sc, model), y, "RQ3 with the Super City programme", estimands={model: HEAD},
                        note=f"districts {c[2]}")[0]

    m = pd.read_csv(final / "outcomes" / "no2_monthly.csv.gz", dtype={"unit_id": str},
                    usecols=["unit_id", "year", "month", "no2", "clip_share"])
    m = m[m["unit_id"].isin(p["unit_id"].unique())]
    m.loc[(m["clip_share"] > CLIP_MAX) | (m["no2"] <= 0), "no2"] = np.nan
    w = m.pivot_table(index=["unit_id", "year"], columns="month", values="no2", aggfunc="first")
    w.columns = [f"ln_no2_m{c:02d}" for c in w.columns]
    q = p.merge(np.log(w).reset_index(), on=["unit_id", "year"], how="left")
    q.loc[(q["iso3"] == "MYS") & (q["year"] == 2024), list(w.columns)] = np.nan
    for c in w.columns:
        rows += imp(q, c, "NO2 by calendar month", estimands={c[-3:]: HEAD})[0]

    if "ntl" in p.columns:
        q = p.copy()
        q["ln_ntl"] = np.log(q["ntl"].where(q["ntl"] > 0))
        q["ln_pm25_per_ntl"] = q["ln_pm25"] - q["ln_ntl"]
        for y in ("ln_ntl", "ln_pm25_per_ntl"):
            rows += imp(q, y, "RQ2 over 2005 to 2024",
                        note="DMSP to 2013, VIIRS converted to the DMSP scale from 2014 (Li et al. 2020)")[0]
    return rows, counts


# ---------------------------------------------------------------- main

def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    panel_dir, final, part = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    B = int(sys.argv[4]) if len(sys.argv) > 4 else 499
    workers = int(sys.argv[5]) if len(sys.argv) > 5 else 6
    p = load(panel_dir, final)
    t0 = time.time()
    if part == "estimators":
        rows = part_estimators(p, panel_dir, B, workers)
    elif part == "rival":
        rows = part_rival(p, panel_dir, final)
    elif part == "coding":
        rows = part_coding(p)
    elif part == "inference":
        rows, D = part_inference(p, final, workers)
        D.to_csv(panel_dir / "ri_draws.csv", index=False)
    elif part == "honest":
        rows = part_honest(p, panel_dir)
    elif part == "extras":
        rows, counts = part_extras(p, final)
        print("districts by model (main coding, by-model years, Super City):", counts)
    else:
        sys.exit(f"unknown part {part}")
    out = pd.DataFrame(rows)[COLS]
    out.to_csv(panel_dir / f"robust_{part}.csv", index=False)
    print(out.to_string(max_colwidth=60), f"\n{part} done in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
