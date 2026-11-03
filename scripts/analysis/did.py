"""Imputation estimator and its tests for the pooled panel (registration Q4, Q19 to Q23).

Borusyak, Jaravel and Spiess (2024). The untreated model

    y_it = sum of fixed effects (district, economy-by-year, size-group-by-year) + X_it'b + e_it

is fitted on untreated district-years only. Covariates are partialled out by alternating projections and the fixed
effects are then recovered by alternating projections on y - Xb (tolerance 1e-10, Q23). The fitted model predicts the
untreated outcome of every treated district-year whose fixed effect levels all appear among untreated district-years
(otherwise the district-year cannot be imputed and is dropped and counted). tau_it is observed minus predicted.

An estimand is a weighted mean of tau_it over treated district-years. Its standard error is the conservative estimator of
BJS Theorem 3: the estimate is sum v_it y_it, where v_it = w_it for treated rows and v = -Z0 (Z0'Z0)^+ Z1'w for
untreated rows, and the variance is the sum over clusters of (sum v_it e_it)^2. e_it is the untreated residual, or for a
treated row tau_it minus the v^2-weighted mean of tau within its cohort and year. v is computed by a direct solve, and
the estimate from v is checked against the alternating projections estimate on every call.

Also here: the BJS pre-trend test (Q19), Holm adjustment and TOST (Q4, Q22), the cluster bootstrap of first-level units
(Q4), the Wald test of equal effects across programme models from the bootstrap draws (Q4), and the wild cluster
bootstrap with Webb weights, restricted under the null, studentised (Q22).

Input frames have one row per district-year with the columns named in `Spec`. A district never treated has cohort NaN.
"""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import sparse, stats

TOL = 1e-10
MAXIT = 200_000
LN_EQ = (np.log(0.95), np.log(1.05))  # smallest effect of interest (Q20)


@dataclass
class Spec:
    y: str
    unit: str = "unit_id"
    year: str = "year"
    cohort: str = "cohort"          # first treated year, NaN if never treated
    cluster: str = "cluster_id"
    fe: tuple = ("unit_id", "econ_year", "size_year")
    covars: tuple = ()
    var_groups: tuple = ("cohort", "year")  # groups for the treated-row residual of Theorem 3


@dataclass
class Fit:
    estimates: pd.DataFrame          # one row per estimand: est, se, n_obs, n_clusters, n_treated_clusters
    tau: pd.DataFrame                # one row per imputed treated district-year
    n_not_imputed: int
    n_untreated: int
    beta: np.ndarray
    extra: dict = field(default_factory=dict)


# ---------------------------------------------------------------- fixed effects

def _codes(df, cols):
    out = []
    for c in cols:
        codes, uniq = pd.factorize(df[c], sort=True)
        out.append((codes, len(uniq)))
    return out


def _indicator(codes, n_groups):
    n = len(codes)
    return sparse.csr_matrix((np.ones(n), (np.arange(n), codes)), shape=(n, n_groups))


def demean(M, fes, tol=TOL, maxit=MAXIT):
    """Partial the fixed effects out of the columns of M by alternating projections."""
    M = np.array(M, dtype=float, copy=True)
    if M.ndim == 1:
        M = M[:, None]
    mats = [(_indicator(c, g), np.maximum(np.bincount(c, minlength=g), 1)) for c, g in fes]
    for it in range(maxit):
        step = 0.0
        for S, cnt in mats:
            m = (S.T @ M) / cnt[:, None]
            M -= S @ m
            step = max(step, np.abs(m).max())
        if step < tol:
            return M, it + 1
    raise RuntimeError(f"alternating projections did not reach {tol} in {maxit} sweeps")


def fe_values(r, fes, tol=TOL, maxit=MAXIT):
    """Fixed effect values for the residual r (block Gauss-Seidel on the levels). Unused levels are NaN."""
    mats = [(_indicator(c, g), np.bincount(c, minlength=g), c) for c, g in fes]
    vals = [np.zeros(g) for _, g in fes]
    for it in range(maxit):
        step = 0.0
        for k, (S, cnt, c) in enumerate(mats):
            other = sum(vals[j][mats[j][2]] for j in range(len(mats)) if j != k)
            new = (S.T @ (r - other)) / np.maximum(cnt, 1)
            step = max(step, np.abs(new - vals[k]).max())
            vals[k] = new
        if step < tol:
            break
    else:
        raise RuntimeError(f"fixed effect values did not reach {tol} in {maxit} sweeps")
    for k, (_, cnt, _) in enumerate(mats):
        vals[k][cnt == 0] = np.nan
    return vals


def fit_untreated(y0, X0, fes0):
    """Covariate coefficients and fixed effect values of the untreated model."""
    if X0.shape[1]:
        Md, _ = demean(np.column_stack([y0, X0]), fes0)
        beta = np.linalg.lstsq(Md[:, 1:], Md[:, 0], rcond=None)[0]
    else:
        beta = np.zeros(0)
    vals = fe_values(y0 - X0 @ beta, fes0)
    return beta, vals


# ---------------------------------------------------------------- the estimator

def _prepare(df, spec):
    d = df[df[spec.y].notna()].copy()
    d["_D"] = (d[spec.cohort].notna() & (d[spec.year] >= d[spec.cohort])).to_numpy()
    d["_rel"] = d[spec.year] - d[spec.cohort]
    X = d[list(spec.covars)].to_numpy(float) if spec.covars else np.zeros((len(d), 0))
    if X.shape[1]:
        if np.isnan(X).any():
            raise ValueError("covariates have missing values")
        X = (X - X.mean(0)) / X.std(0)  # scale only; predictions do not change
    return d.reset_index(drop=True), X


def _design(fes, X):
    blocks = [_indicator(c, g) for c, g in fes]
    if X.shape[1]:
        blocks.append(sparse.csr_matrix(X))
    return sparse.hstack(blocks, format="csr")


def impute(df, spec, estimands, check=True):
    """Fit the untreated model and return estimates for each estimand.

    estimands maps a name to a function of the treated frame (columns of df plus _rel, tau) that returns a boolean mask or
    nonnegative weights; weights are rescaled to sum to one over the imputed rows.
    """
    d, X = _prepare(df, spec)
    D = d["_D"].to_numpy()
    fes = _codes(d, spec.fe)
    fes0 = [(c[~D], g) for c, g in fes]
    y = d[spec.y].to_numpy(float)
    beta, vals = fit_untreated(y[~D], X[~D], fes0)

    pred = X @ beta + sum(v[c] for v, (c, _) in zip(vals, fes))
    ok = D & np.isfinite(pred)
    t = d.loc[ok].copy()
    t["tau"] = y[ok] - pred[ok]
    n_not = int((D & ~np.isfinite(pred)).sum())

    # weights of every estimand on the imputed treated rows
    W = []
    for name, f in estimands.items():
        w = np.asarray(f(t), dtype=float)
        if w.sum() <= 0:
            W.append(np.full(len(t), np.nan))
        else:
            W.append(w / w.sum())
    W = np.column_stack(W) if W else np.zeros((len(t), 0))

    # v for untreated rows: -Z0 (Z0'Z0)^+ Z1'W
    Z = _design(fes, X)
    Z0, Z1 = Z[~D], Z[ok]
    A = (Z0.T @ Z0).toarray()
    P = np.linalg.pinv(A, rcond=1e-11, hermitian=True)
    good = ~np.isnan(W).any(0)
    V0 = np.full((Z0.shape[0], W.shape[1]), np.nan)
    V0[:, good] = -(Z0 @ (P @ (Z1.T @ W[:, good])))

    resid0 = y[~D] - pred[~D]
    clusters = d[spec.cluster].to_numpy()
    rows = []
    for j, name in enumerate(estimands):
        if not good[j]:
            rows.append(dict(estimand=name, est=np.nan, se=np.nan, n_obs=0, n_clusters=0, n_treated_clusters=0))
            continue
        w1, v0 = W[:, j], V0[:, j]
        est = float(w1 @ t["tau"].to_numpy())
        if check:
            est_v = float(w1 @ y[ok] + v0 @ y[~D])
            if abs(est_v - est) > 1e-6 * max(1.0, abs(est)):
                raise RuntimeError(f"{name}: direct solve {est_v} and alternating projections {est} differ")
        e1 = _treated_resid(t, w1, spec)
        se = _cluster_se(np.concatenate([v0, w1]), np.concatenate([resid0, e1]),
                         np.concatenate([clusters[~D], clusters[ok]]))
        used = np.concatenate([np.abs(v0) > 1e-14, w1 > 0])
        rows.append(dict(estimand=name, est=est, se=se, n_obs=int((w1 > 0).sum()),
                         n_clusters=int(pd.unique(np.concatenate([clusters[~D], clusters[ok]])[used]).size),
                         n_treated_clusters=int(pd.unique(clusters[ok][w1 > 0]).size)))
    out = Fit(pd.DataFrame(rows).set_index("estimand"), t, n_not, int((~D).sum()), beta)
    out.extra = dict(P=P, Z=Z, D=D, ok=ok, W=W, V0=V0, d=d, X=X, fes=fes)
    return out


def _treated_resid(t, w1, spec):
    g = t.groupby(list(spec.var_groups)).ngroup().to_numpy()
    w2 = w1 ** 2
    num = np.bincount(g, weights=w2 * t["tau"].to_numpy())
    den = np.bincount(g, weights=w2)
    bar = np.divide(num, den, out=np.zeros_like(num), where=den > 0)
    return t["tau"].to_numpy() - bar[g]


def _cluster_se(v, e, clusters):
    codes, _ = pd.factorize(clusters)
    s = np.bincount(codes, weights=v * e)
    return float(np.sqrt((s ** 2).sum()))


def horizon_estimands(lo=0, hi=5, each=True, all_=True):
    """Headline (mean over years lo to hi after designation), each horizon, and every treated year (Q19)."""
    e = {f"h{lo}_{hi}": lambda t: t["_rel"].between(lo, hi)}
    if each:
        for h in range(lo, hi + 1):
            e[f"h{h}"] = (lambda h: lambda t: t["_rel"] == h)(h)
    if all_:
        e["all"] = lambda t: np.ones(len(t))
    return e


# ---------------------------------------------------------------- pre-trend test

def pretrend_test(df, spec, leads=8):
    """BJS test: on untreated rows, add indicators for 1 to `leads` years before designation and test them jointly.

    Cluster-robust covariance with the G/(G-1) correction; F statistic on (leads, G-1) degrees of freedom.
    """
    d, X = _prepare(df, spec)
    d0 = d.loc[~d["_D"]].reset_index(drop=True)
    X0 = X[~d["_D"].to_numpy()]
    L = np.column_stack([(d0["_rel"] == -k).to_numpy(float) for k in range(1, leads + 1)])
    fes0 = _codes(d0, spec.fe)
    Md, _ = demean(np.column_stack([d0[spec.y].to_numpy(float), L, X0]), fes0)
    yd, R = Md[:, 0], Md[:, 1:]
    coef = np.linalg.lstsq(R, yd, rcond=None)[0]
    u = yd - R @ coef
    codes, uniq = pd.factorize(d0[spec.cluster])
    G = len(uniq)
    bread = np.linalg.pinv(R.T @ R)
    S = sparse.csr_matrix((np.ones(len(codes)), (codes, np.arange(len(codes)))), shape=(G, len(codes)))
    sc = S @ (R * u[:, None])
    V = bread @ (sc.T @ sc) @ bread * G / (G - 1)
    b, Vb = coef[:leads], V[:leads, :leads]
    W = float(b @ np.linalg.solve(Vb, b))
    F = W / leads
    return dict(coef=b, se=np.sqrt(np.diag(Vb)), F=F, df1=leads, df2=G - 1,
                p=float(stats.f.sf(F, leads, G - 1)), n=len(d0), clusters=G,
                n_lead_obs=(L.sum(0)).astype(int))


# ---------------------------------------------------------------- inference helpers

def holm(p):
    """Holm-adjusted p-values, in the input order."""
    p = np.asarray(p, float)
    order = np.argsort(p)
    m = len(p)
    adj = np.empty(m)
    run = 0.0
    for i, k in enumerate(order):
        run = max(run, min(1.0, (m - i) * p[k]))
        adj[k] = run
    return adj


def tost(est, se, bounds=LN_EQ):
    """Two one-sided tests against the equivalence bounds. Equivalent when p < 0.05 (90 percent CI inside bounds)."""
    lo, hi = bounds
    p_lo = stats.norm.sf((est - lo) / se)
    p_hi = stats.norm.cdf((est - hi) / se)
    return dict(p=float(max(p_lo, p_hi)), ci90=(est - 1.645 * se, est + 1.645 * se),
                equivalent=bool(max(p_lo, p_hi) < 0.05))


def p_two_sided(est, se):
    return float(2 * stats.norm.sf(abs(est / se)))


# ---------------------------------------------------------------- cluster bootstrap (Q4)

def cluster_draws(clusters, B=999, seed=20261102):
    rng = np.random.default_rng(seed)
    uniq = np.asarray(pd.unique(clusters))
    return [rng.choice(uniq, size=len(uniq), replace=True) for _ in range(B)]


def resample(df, draw, spec):
    """Stack the drawn clusters; each copy of a cluster gets its own district and cluster labels."""
    parts = []
    by = dict(tuple(df.groupby(spec.cluster, sort=False)))
    for k, c in enumerate(draw):
        p = by[c].copy()
        p[spec.unit] = p[spec.unit].astype(str) + f"#{k}"
        p[spec.cluster] = f"{c}#{k}"
        parts.append(p)
    return pd.concat(parts, ignore_index=True)


def point(df, spec, estimand):
    """Point estimate only (no variance), for bootstrap draws."""
    d, X = _prepare(df, spec)
    D = d["_D"].to_numpy()
    fes = _codes(d, spec.fe)
    y = d[spec.y].to_numpy(float)
    beta, vals = fit_untreated(y[~D], X[~D], [(c[~D], g) for c, g in fes])
    pred = X @ beta + sum(v[c] for v, (c, _) in zip(vals, fes))
    ok = D & np.isfinite(pred)
    t = d.loc[ok].copy()
    t["tau"] = y[ok] - pred[ok]
    w = np.asarray(estimand(t), float)
    return float(w @ t["tau"].to_numpy() / w.sum()) if w.sum() > 0 else np.nan


def wald_equal(theta, draws):
    """Wald test that the entries of theta are equal, with the covariance of the bootstrap draws (rows = draws)."""
    theta = np.asarray(theta, float)
    k = len(theta)
    R = np.eye(k)[:-1] - np.eye(k, k=1)[:-1]
    S = np.cov(np.asarray(draws, float), rowvar=False)
    r = R @ theta
    W = float(r @ np.linalg.solve(R @ S @ R.T, r))
    return dict(W=W, df=k - 1, p=float(stats.chi2.sf(W, k - 1)))


# ---------------------------------------------------------------- wild cluster bootstrap (Q22)

WEBB = np.array([-np.sqrt(1.5), -1.0, -np.sqrt(0.5), np.sqrt(0.5), 1.0, np.sqrt(1.5)])


def wild_cluster_p(fit, spec, estimand, B=9_999, seed=20261102, batch=250):
    """Restricted (tau = 0) wild cluster bootstrap-t with Webb weights for one estimand of a fitted model."""
    x = fit.extra
    d, Z, D, ok, P = x["d"], x["Z"], x["D"], x["ok"], x["P"]
    j = list(fit.estimates.index).index(estimand)
    w1, v0 = x["W"][:, j], x["V0"][:, j]
    y = d[spec.y].to_numpy(float)
    keep = ~D | ok                      # rows the estimator uses
    # restricted model: no treatment effect, fitted on every used row
    fes_k = [(c[keep], g) for c, g in x["fes"]]
    beta_r, vals_r = fit_untreated(y[keep], x["X"][keep], fes_k)
    fitted = x["X"][keep] @ beta_r + sum(v[c] for v, (c, _) in zip(vals_r, fes_k))
    resid = y[keep] - fitted
    cl, G = pd.factorize(d[spec.cluster].to_numpy()[keep])
    G = len(G)
    is0 = (~D)[keep]
    Z0, Z1 = Z[~D], Z[ok]
    v = np.empty(keep.sum())
    v[is0], v[~is0] = v0, w1
    t_tr = fit.tau
    g = t_tr.groupby(list(spec.var_groups)).ngroup().to_numpy()
    w2 = w1 ** 2
    den = np.bincount(g, weights=w2)
    Cmat = sparse.csr_matrix((np.ones(len(cl)), (cl, np.arange(len(cl)))), shape=(G, len(cl)))
    Gmat = sparse.csr_matrix((w2, (g, np.arange(len(g)))), shape=(len(den), len(g)))

    est = float(fit.estimates.loc[estimand, "est"])
    se = float(fit.estimates.loc[estimand, "se"])
    t_obs = est / se
    rng = np.random.default_rng(seed)
    exceed, done = 0, 0
    while done < B:
        b = min(batch, B - done)
        eta = WEBB[rng.integers(0, 6, size=(G, b))]
        Ys = fitted[:, None] + resid[:, None] * eta[cl]
        Y0, Y1 = Ys[is0], Ys[~is0]
        gam = P @ (Z0.T @ Y0)
        e0 = Y0 - Z0 @ gam
        tau = Y1 - Z1 @ gam
        est_s = w1 @ tau
        bar = (Gmat @ tau) / np.where(den > 0, den, 1)[:, None]
        e1 = tau - bar[g]
        E = np.empty_like(Ys)
        E[is0], E[~is0] = e0, e1
        se_s = np.sqrt(((Cmat @ (v[:, None] * E)) ** 2).sum(0))
        exceed += int((np.abs(est_s / se_s) >= abs(t_obs)).sum())
        done += b
    return dict(p=exceed / B, B=B, clusters=G, t=t_obs)
