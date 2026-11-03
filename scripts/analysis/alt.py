"""Alternative estimators and inference for the robustness checks (registration Q16, Q19, Q23, Q24).

- wpoint, wimpute: the imputation estimator of did.py with weights, for population weights (Q16) and entropy balancing (Q24).
- conley_se: spatial standard errors for an estimand of did.impute, uniform kernel on district centroid distance.
- cs_dr: Callaway and Sant'Anna (2021), doubly robust (Sant'Anna and Zhao 2020), not-yet-treated comparisons, base
  year g - 1, baseline covariates, comparisons within the economy.
- dcdh: de Chaisemartin and D'Haultfoeuille, DID_M (2020, effect in the first treated year) and DID_l for years 0 to 5
  (the 2024 extension), comparisons within the economy.
- stacked: stacked difference-in-differences (Cengiz et al. 2019), one stack per cohort, years g - 5 to g + 5, clean
  comparisons not treated within the window.
- twfe: static two-way fixed effects with the fixed effects of the main specification.
- bacon: Goodman-Bacon (2021) decomposition of the district and year two-way fixed effects estimate on a balanced panel.
- sun_abraham: Sun and Abraham (2021) interaction-weighted event study with the main fixed effects and covariates,
  year -1 as reference, never-designated districts as the comparison, and its clustered covariance.
- entropy_weights: entropy balancing (Hainmueller 2012) of comparison districts on pre-designation outcomes, 2015
  population and economy.

Cohort conventions follow did.py: cohort is the first treated year, NaN when never treated. A cohort after the last
panel year is treated as never treated within the panel.
"""
import numpy as np
import pandas as pd
from scipy import optimize, sparse, stats

import did

LAST = 2024


# ---------------------------------------------------------------- weighted imputation

def _wdemean(M, fes, w, tol=did.TOL, maxit=did.MAXIT):
    M = np.array(M, dtype=float, copy=True)
    if M.ndim == 1:
        M = M[:, None]
    mats = [(did._indicator(c, g), np.bincount(c, weights=w, minlength=g)) for c, g in fes]
    mats = [(S, np.where(sw > 0, sw, 1.0)) for S, sw in mats]
    for _ in range(maxit):
        step = 0.0
        for S, sw in mats:
            m = (S.T @ (w[:, None] * M)) / sw[:, None]
            M -= S @ m
            step = max(step, np.abs(m).max())
        if step < tol:
            return M
    raise RuntimeError("weighted alternating projections did not converge")


def _wfe_values(r, fes, w, tol=did.TOL, maxit=did.MAXIT):
    mats = [(did._indicator(c, g), np.bincount(c, weights=w, minlength=g), c) for c, g in fes]
    vals = [np.zeros(g) for _, g in fes]
    for _ in range(maxit):
        step = 0.0
        for k, (S, sw, c) in enumerate(mats):
            other = sum(vals[j][mats[j][2]] for j in range(len(mats)) if j != k)
            new = (S.T @ (w * (r - other))) / np.where(sw > 0, sw, 1.0)
            step = max(step, np.abs(new - vals[k]).max())
            vals[k] = new
        if step < tol:
            break
    else:
        raise RuntimeError("weighted fixed effect values did not converge")
    for k, (_, sw, _) in enumerate(mats):
        vals[k][sw == 0] = np.nan
    return vals


def wpoint(df, spec, fit_w, estimand, est_w=None):
    """Imputation estimate with the untreated model fitted by weighted least squares (weights in column fit_w) and
    the estimand weights multiplied by column est_w (None for equal weights)."""
    d, X = did._prepare(df, spec)
    D = d["_D"].to_numpy()
    fes = did._codes(d, spec.fe)
    y = d[spec.y].to_numpy(float)
    w0 = d[fit_w].to_numpy(float)[~D]
    fes0 = [(c[~D], g) for c, g in fes]
    if X.shape[1]:
        Md = _wdemean(np.column_stack([y[~D], X[~D]]), fes0, w0)
        sw = np.sqrt(w0)
        beta = np.linalg.lstsq(Md[:, 1:] * sw[:, None], Md[:, 0] * sw, rcond=None)[0]
    else:
        beta = np.zeros(0)
    vals = _wfe_values(y[~D] - X[~D] @ beta, fes0, w0)
    pred = X @ beta + sum(v[c] for v, (c, _) in zip(vals, fes))
    ok = D & np.isfinite(pred)
    t = d.loc[ok].copy()
    t["tau"] = y[ok] - pred[ok]
    m = np.asarray(estimand(t), float)
    if est_w is not None:
        m = m * t[est_w].to_numpy(float)
    return float(m @ t["tau"].to_numpy() / m.sum()) if m.sum() > 0 else np.nan


def wimpute(df, spec, fit_w, estimands, est_w=None):
    """wpoint for several estimands, with the standard error of BJS Theorem 3 for weighted least squares, conditional on
    the weights: v = w for treated rows and v = -w0 * Z0 (Z0'W0 Z0)^+ Z1'w for untreated rows. The estimate from v is
    checked against the alternating projections estimate."""
    d, X = did._prepare(df, spec)
    D = d["_D"].to_numpy()
    fes = did._codes(d, spec.fe)
    y = d[spec.y].to_numpy(float)
    w0 = d[fit_w].to_numpy(float)[~D]
    fes0 = [(c[~D], g) for c, g in fes]
    if X.shape[1]:
        Md = _wdemean(np.column_stack([y[~D], X[~D]]), fes0, w0)
        sw = np.sqrt(w0)
        beta = np.linalg.lstsq(Md[:, 1:] * sw[:, None], Md[:, 0] * sw, rcond=None)[0]
    else:
        beta = np.zeros(0)
    vals = _wfe_values(y[~D] - X[~D] @ beta, fes0, w0)
    pred = X @ beta + sum(v[c] for v, (c, _) in zip(vals, fes))
    ok = D & np.isfinite(pred)
    t = d.loc[ok].copy()
    t["tau"] = y[ok] - pred[ok]
    Z = did._design(fes, X)
    Z0, Z1 = Z[~D], Z[ok]
    P = np.linalg.pinv((Z0.T @ Z0.multiply(w0[:, None])).toarray(), rcond=1e-11, hermitian=True)
    resid0 = y[~D] - pred[~D]
    clusters = d[spec.cluster].to_numpy()
    rows = []
    for name, f in estimands.items():
        m = np.asarray(f(t), float)
        if est_w is not None:
            m = m * t[est_w].to_numpy(float)
        if m.sum() <= 0:
            rows.append(dict(estimand=name, est=np.nan, se=np.nan, n_obs=0, n_clusters=0))
            continue
        w1 = m / m.sum()
        v0 = -w0 * (Z0 @ (P @ (Z1.T @ w1)))
        est = float(w1 @ t["tau"].to_numpy())
        est_v = float(w1 @ y[ok] + v0 @ y[~D])
        if abs(est_v - est) > 1e-6 * max(1.0, abs(est)):
            raise RuntimeError(f"{name}: direct solve {est_v} and alternating projections {est} differ")
        e1 = did._treated_resid(t, w1, spec)
        se = did._cluster_se(np.concatenate([v0, w1]), np.concatenate([resid0, e1]),
                             np.concatenate([clusters[~D], clusters[ok]]))
        rows.append(dict(estimand=name, est=est, se=se, n_obs=int((w1 > 0).sum()),
                         n_clusters=int(pd.unique(clusters[ok][w1 > 0]).size)))
    return pd.DataFrame(rows).set_index("estimand")


# ---------------------------------------------------------------- Conley standard errors

def contributions(fit, spec, estimand):
    """Per-row terms v_it e_it of the variance of an estimand of did.impute, with the district of each row."""
    x = fit.extra
    d, D, ok, Z, P = x["d"], x["D"], x["ok"], x["Z"], x["P"]
    j = list(fit.estimates.index).index(estimand)
    w1, v0 = x["W"][:, j], x["V0"][:, j]
    y = d[spec.y].to_numpy(float)
    Z0 = Z[~D]
    resid0 = y[~D] - Z0 @ (P @ (Z0.T @ y[~D]))
    e1 = did._treated_resid(fit.tau, w1, spec)
    s = np.concatenate([v0 * resid0, w1 * e1])
    units = np.concatenate([d[spec.unit].to_numpy()[~D], d[spec.unit].to_numpy()[ok]])
    clusters = np.concatenate([d[spec.cluster].to_numpy()[~D], d[spec.cluster].to_numpy()[ok]])
    return s, units, clusters


def haversine_km(lat, lon):
    la, lo = np.radians(lat)[:, None], np.radians(lon)[:, None]
    a = np.sin((la - la.T) / 2) ** 2 + np.cos(la) * np.cos(la.T) * np.sin((lo - lo.T) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def conley_se(fit, spec, estimand, coords, cutoffs_km):
    """coords: DataFrame indexed by district with lat and lon. Every pair of districts within the cut-off is allowed to
    be correlated in every year pair (uniform kernel); a district is always correlated with itself."""
    s, units, clusters = contributions(fit, spec, estimand)
    S = pd.Series(s).groupby(units).sum()
    c = coords.loc[S.index]
    dist = haversine_km(c["lat"].to_numpy(), c["lon"].to_numpy())
    v = S.to_numpy()
    out = {}
    for h in cutoffs_km:
        K = (dist <= h).astype(float)
        out[h] = float(np.sqrt(max(v @ K @ v, 0.0)))
    cl = pd.Series(s).groupby(clusters).sum().to_numpy()
    out["cluster_check"] = float(np.sqrt((cl ** 2).sum()))
    return out


# ---------------------------------------------------------------- wide arrays for the cohort comparisons

class Wide:
    """District-by-year arrays of one outcome and the baseline covariates."""

    def __init__(self, p, y, covars=(), static=("iso3", "size_group", "cluster_id", "ln_pop")):
        years = np.arange(p["year"].min(), p["year"].max() + 1)
        units = np.sort(p["unit_id"].unique())
        self.years, self.units = years, units
        idx = pd.MultiIndex.from_product([units, years], names=["unit_id", "year"])
        q = p.set_index(["unit_id", "year"]).reindex(idx)
        n, T = len(units), len(years)
        self.Y = q[y].to_numpy(float).reshape(n, T)
        self.C = {c: q[c].to_numpy(float).reshape(n, T) for c in covars}
        first = p.drop_duplicates("unit_id").set_index("unit_id").loc[units]
        g = first["cohort"].to_numpy(float)
        g[np.isnan(g) | (g > LAST)] = np.inf
        self.G = g
        self.S = {c: first[c].to_numpy() for c in static if c in first}

    def take(self, idx):
        new = object.__new__(Wide)
        new.years, new.units = self.years, self.units[idx]
        new.Y = self.Y[idx]
        new.C = {k: v[idx] for k, v in self.C.items()}
        new.G = self.G[idx]
        new.S = {k: v[idx] for k, v in self.S.items()}
        return new

    def col(self, year):
        return int(year - self.years[0])


def _dummies(codes):
    u, inv = np.unique(codes, return_inverse=True)
    if len(u) < 2:
        return np.zeros((len(codes), 0))
    return np.eye(len(u))[inv][:, 1:]


def _logit_ridge(X, D, lam=1.0, maxit=100):
    """Logit with an L2 penalty on every coefficient except the intercept (first column of X)."""
    b = np.zeros(X.shape[1])
    pen = np.full(X.shape[1], lam)
    pen[0] = 0.0
    for _ in range(maxit):
        p = 1 / (1 + np.exp(-np.clip(X @ b, -30, 30)))
        g = X.T @ (D - p) - pen * b
        H = (X * (p * (1 - p))[:, None]).T @ X + np.diag(pen)
        step = np.linalg.solve(H, g)
        b += step
        if np.abs(step).max() < 1e-8:
            break
    return 1 / (1 + np.exp(-np.clip(X @ b, -30, 30)))


def _std(X):
    sd = X.std(0)
    sd[sd == 0] = 1
    return (X - X.mean(0)) / sd


def dr_att(dY, D, X, trim=0.995):
    """Doubly robust ATT for panel data (Sant'Anna and Zhao 2020): propensity score by logit and the outcome change
    of comparison units by least squares, both on X (which starts with an intercept)."""
    ps = _logit_ridge(X, D.astype(float))
    keep = D | (ps < trim)
    b = np.linalg.lstsq(X[~D & keep], dY[~D & keep], rcond=None)[0]
    r = dY - X @ b
    wc = np.where(~D & keep, ps / (1 - ps), 0.0)
    return float(r[D].mean() - (wc @ r) / wc.sum())


def _cell_design(wd, rows, base, covars):
    cols = [np.ones(len(rows))]
    blocks = [np.column_stack(cols)]
    if covars:
        Xc = np.column_stack([wd.C[c][rows, wd.col(base)] for c in covars])
        blocks.append(_std(Xc))
    if "ln_pop" in wd.S:
        blocks.append(_std(wd.S["ln_pop"][rows].astype(float)[:, None]))
    blocks.append(_dummies(wd.S["iso3"][rows]))
    blocks.append(_dummies(wd.S["size_group"][rows]))
    return np.column_stack(blocks)


def cs_dr(wd, covars, horizons=range(0, 6), min_treated=1):
    """ATT(g, t) for t = g + e, e in horizons, with comparison districts not yet treated at t in the economies where
    cohort g has districts. Rows with a missing covariate in the base year are dropped. Returns one line per (g, e)."""
    out = []
    covar_ok = np.ones_like(wd.Y, dtype=bool)
    for c in covars:
        covar_ok &= np.isfinite(wd.C[c])
    for g in np.unique(wd.G[np.isfinite(wd.G)]):
        base = int(g) - 1
        for e in horizons:
            t = int(g) + e
            if t > wd.years[-1]:
                break
            ok = np.isfinite(wd.Y[:, wd.col(t)]) & np.isfinite(wd.Y[:, wd.col(base)]) & covar_ok[:, wd.col(base)]
            tr = (wd.G == g) & ok
            econ = np.unique(wd.S["iso3"][tr])
            ct = (wd.G > t) & ok & np.isin(wd.S["iso3"], econ)
            # an economy needs at least one comparison district
            econ_ok = np.intersect1d(econ, np.unique(wd.S["iso3"][ct]))
            tr &= np.isin(wd.S["iso3"], econ_ok)
            ct &= np.isin(wd.S["iso3"], econ_ok)
            if tr.sum() < min_treated or ct.sum() < 2:
                continue
            rows = np.flatnonzero(tr | ct)
            dY = wd.Y[rows, wd.col(t)] - wd.Y[rows, wd.col(base)]
            X = _cell_design(wd, rows, base, covars)
            att = dr_att(dY, tr[rows], X)
            out.append(dict(g=int(g), e=e, t=t, att=att, n=int(tr.sum()), n_ctrl=int(ct.sum())))
    return pd.DataFrame(out)


def dcdh(wd, horizons=range(0, 6)):
    """DID_l of de Chaisemartin and D'Haultfoeuille for an absorbing binary treatment: for cohort g in economy c,
    the change in Y from g - 1 to g + l of the cohort minus that of districts of c not yet treated at g + l.
    Returns one line per (g, economy, l)."""
    out = []
    for g in np.unique(wd.G[np.isfinite(wd.G)]):
        base = int(g) - 1
        for e in horizons:
            t = int(g) + e
            if t > wd.years[-1]:
                break
            ok = np.isfinite(wd.Y[:, wd.col(t)]) & np.isfinite(wd.Y[:, wd.col(base)])
            dY = wd.Y[:, wd.col(t)] - wd.Y[:, wd.col(base)]
            for c in np.unique(wd.S["iso3"][(wd.G == g) & ok]):
                inc = wd.S["iso3"] == c
                tr, ct = (wd.G == g) & ok & inc, (wd.G > t) & ok & inc
                if tr.sum() and ct.sum():
                    out.append(dict(g=int(g), iso3=c, e=e, att=float(dY[tr].mean() - dY[ct].mean()),
                                    n=int(tr.sum()), n_ctrl=int(ct.sum())))
    return pd.DataFrame(out)


def aggregate(cells, horizons=range(0, 6)):
    """Mean over cells weighted by the number of treated districts (each treated district-year counts once)."""
    c = cells[cells["e"].isin(list(horizons))]
    return float(np.average(c["att"], weights=c["n"])) if len(c) else np.nan


def cluster_index(wd, rng):
    """Row indices of a cluster bootstrap draw on the wide arrays."""
    cl = wd.S["cluster_id"]
    uniq, inv = np.unique(cl, return_inverse=True)
    members = [np.flatnonzero(inv == k) for k in range(len(uniq))]
    draw = rng.integers(0, len(uniq), size=len(uniq))
    return np.concatenate([members[k] for k in draw])


# ---------------------------------------------------------------- regression helpers

def ols_cluster(y, R, clusters):
    """OLS of y on the columns of R (already demeaned) with the CR1 covariance by cluster (G / (G - 1))."""
    coef = np.linalg.lstsq(R, y, rcond=None)[0]
    u = y - R @ coef
    codes, uniq = pd.factorize(clusters)
    G = len(uniq)
    bread = np.linalg.pinv(R.T @ R)
    S = sparse.csr_matrix((np.ones(len(codes)), (codes, np.arange(len(codes)))), shape=(G, len(codes)))
    sc = S @ (R * u[:, None])
    V = bread @ (sc.T @ sc) @ bread * G / (G - 1)
    return coef, V, G


def twfe(p, spec):
    """Static two-way fixed effects estimate of D with the fixed effects and covariates of spec, every district-year."""
    d, X = did._prepare(p, spec)
    fes = did._codes(d, spec.fe)
    M = np.column_stack([d[spec.y].to_numpy(float), d["_D"].to_numpy(float), X])
    Md, _ = did.demean(M, fes)
    coef, V, G = ols_cluster(Md[:, 0], Md[:, 1:], d[spec.cluster].to_numpy())
    return dict(est=float(coef[0]), se=float(np.sqrt(V[0, 0])), n_obs=len(d), clusters=G)


def stacked(p, spec, window=5):
    """Stacked difference-in-differences. One stack per cohort g with the districts of the cohort and districts not
    treated by g + window, years g - window to g + window; fixed effects of spec interacted with the stack, covariates,
    and one treated-after indicator. Standard errors clustered by first-level unit."""
    g_all = p["cohort"].where(p["cohort"] <= LAST)
    parts = []
    for g in sorted(g_all.dropna().unique()):
        yrs = (p["year"] >= g - window) & (p["year"] <= g + window)
        tr = g_all == g
        ct = g_all.isna() | (g_all > g + window)
        s = p[yrs & (tr | ct)].copy()
        s["_stack"] = int(g)
        s["_treat_post"] = ((s["cohort"] == g) & (s["year"] >= g)).astype(float)
        parts.append(s)
    s = pd.concat(parts, ignore_index=True)
    s = s[s[spec.y].notna()]
    for f in spec.fe:
        s[f + "_stk"] = s[f].astype(str) + "|" + s["_stack"].astype(str)
    fes = did._codes(s, [f + "_stk" for f in spec.fe])
    X = s[list(spec.covars)].to_numpy(float) if spec.covars else np.zeros((len(s), 0))
    M = np.column_stack([s[spec.y].to_numpy(float), s["_treat_post"].to_numpy(), X])
    Md, _ = did.demean(M, fes)
    coef, V, G = ols_cluster(Md[:, 0], Md[:, 1:], s[spec.cluster].to_numpy())
    return dict(est=float(coef[0]), se=float(np.sqrt(V[0, 0])), n_obs=len(s), clusters=G, stacks=len(parts))


# ---------------------------------------------------------------- Goodman-Bacon decomposition

def _twoway(Y, D):
    """Two-way (district and year) fixed effects estimate on a balanced block, and the mean squared demeaned D."""
    def dm(A):
        return A - A.mean(1, keepdims=True) - A.mean(0, keepdims=True) + A.mean()
    Dt = dm(D)
    v = (Dt ** 2).mean()
    return (float((Dt * dm(Y)).sum() / (Dt ** 2).sum()) if v > 0 else np.nan), float(v)


def bacon(wd):
    """Goodman-Bacon decomposition on the districts observed in every year. Returns the two-way fixed effects estimate,
    the 2x2 estimates with their weights, and the sum of the weights as a check."""
    full = np.isfinite(wd.Y).all(1)
    Y, G = wd.Y[full], wd.G[full]
    years = wd.years
    D = (years[None, :] >= G[:, None]).astype(float)
    beta, VD = _twoway(Y, D)
    N = Y.size
    timing = np.unique(G[np.isfinite(G)])
    rows = []

    def add(kind, k, l, units, cols, Dsub):
        b, v = _twoway(Y[np.ix_(units, cols)], Dsub)
        share = len(units) * len(cols) / N
        rows.append(dict(kind=kind, k=k, l=l, est=b, weight=share ** 2 * v / VD))

    never = np.flatnonzero(~np.isfinite(G))
    allc = np.arange(len(years))
    for k in timing:
        uk = np.flatnonzero(G == k)
        if len(never):
            units = np.concatenate([uk, never])
            add("treated vs never treated", k, np.inf, units, allc, D[np.ix_(units, allc)])
        for l in timing[timing > k]:
            ul = np.flatnonzero(G == l)
            units = np.concatenate([uk, ul])
            early = np.flatnonzero(years < l)
            add("earlier vs later (later not yet treated)", k, l, units, early, D[np.ix_(units, early)])
            late = np.flatnonzero(years >= k)
            add("later vs earlier (earlier already treated)", l, k, units, late, D[np.ix_(units, late)])
    out = pd.DataFrame(rows)
    return dict(beta=beta, parts=out, weight_sum=float(out["weight"].sum()),
                recomposed=float((out["weight"] * out["est"]).sum()), districts=int(full.sum()))


# ---------------------------------------------------------------- Sun and Abraham

def sun_abraham(p, spec, ref=-1):
    """Interaction-weighted event study. Every cohort-by-relative-year indicator except ref is in one regression with
    the fixed effects and covariates of spec; districts never designated within the panel are the comparison group.
    Returns the relative-year estimates (weights = treated district-years with the outcome), their covariance, and
    the cohort-by-relative-year cells."""
    d, X = did._prepare(p, spec)
    g = d[spec.cohort].where(d[spec.cohort] <= LAST)
    rel = (d[spec.year] - g)
    cells = sorted({(int(a), int(b)) for a, b in zip(g[g.notna()], rel[g.notna()]) if b != ref})
    col = {c: k for k, c in enumerate(cells)}
    r_idx = np.flatnonzero(g.notna().to_numpy() & (rel.to_numpy() != ref))
    c_idx = np.array([col[(int(g.iloc[i]), int(rel.iloc[i]))] for i in r_idx])
    I = sparse.csr_matrix((np.ones(len(r_idx)), (r_idx, c_idx)), shape=(len(d), len(cells))).toarray()
    fes = did._codes(d, spec.fe)
    Md, _ = did.demean(np.column_stack([d[spec.y].to_numpy(float), I, X]), fes)
    coef, V, G = ols_cluster(Md[:, 0], Md[:, 1:], d[spec.cluster].to_numpy())
    k = len(cells)
    b, Vb = coef[:k], V[:k, :k]
    n = I.sum(0)
    cell_df = pd.DataFrame(cells, columns=["g", "e"]).assign(est=b, se=np.sqrt(np.diag(Vb)), n=n)
    rels = sorted(cell_df["e"].unique())
    L = np.zeros((len(rels), k))
    for i, e in enumerate(rels):
        m = (cell_df["e"] == e).to_numpy()
        L[i, m] = n[m] / n[m].sum()
    theta = L @ b
    Vt = L @ Vb @ L.T
    es = pd.DataFrame(dict(e=rels, est=theta, se=np.sqrt(np.diag(Vt)), n=[n[cell_df["e"].to_numpy() == e].sum()
                                                                           for e in rels]))
    return dict(event=es, V=Vt, L=L, cells=cell_df, Vcells=Vb, clusters=G)


def sa_aggregate(sa, horizons=range(0, 6)):
    c = sa["cells"]
    m = c["e"].isin(list(horizons)).to_numpy()
    w = np.where(m, c["n"].to_numpy(), 0.0)
    w = w / w.sum()
    est = float(w @ c["est"].to_numpy())
    se = float(np.sqrt(w @ sa["Vcells"] @ w))
    return est, se


# ---------------------------------------------------------------- entropy balancing

def entropy_weights(C, target, maxit=1000):
    """Weights on the rows of C (comparison units) with weighted means equal to target and the smallest
    Kullback-Leibler distance from equal weights (Hainmueller 2012). Returns weights summing to one."""
    mu, sd = C.mean(0), C.std(0)
    sd[sd == 0] = 1
    Cs, ts = (C - mu) / sd, (target - mu) / sd

    def f(lam):
        z = Cs @ lam
        m = z.max()
        e = np.exp(z - m)
        return m + np.log(e.sum()) - lam @ ts, (Cs.T @ e) / e.sum() - ts

    res = optimize.minimize(f, np.zeros(C.shape[1]), jac=True, method="BFGS",
                            options=dict(maxiter=maxit, gtol=1e-10))
    z = Cs @ res.x
    w = np.exp(z - z.max())
    w /= w.sum()
    gap = float(np.abs(w @ Cs - ts).max())
    return w, gap
