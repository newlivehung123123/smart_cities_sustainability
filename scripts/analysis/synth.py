"""Synthetic control estimators for Singapore and Hong Kong (registration Q19, Q22, Q23).

Y is a units-by-periods array of log outcomes. Row 0 is the treated unit, rows 1.. are donors, and the first T0
periods are before designation.

scm       Synthetic control weights on the simplex, fitted on every pre-designation period (nnls with a sum-to-one row).
ascm      Ridge augmented synthetic control (Ben-Michael, Feller and Rothstein 2021). The synthetic control is corrected
          by a ridge regression of each post-designation period on the pre-designation periods among donors. The ridge
          penalty is chosen by rolling-origin cross-validation over the last pre-designation periods with the
          one-standard-error rule, as in the augsynth package.
sdid      Synthetic difference-in-differences (Arkhangelsky et al. 2021), unit and time weights by Frank-Wolfe with the
          regularisation and sparsification of the synthdid package.
residualize   Covariates enter by residualising each period's outcome on them across all units (augsynth default).

placebo_ranks gives every donor the designation in turn (the treated unit is dropped from the donor pool) and ranks the
ratio of post- to pre-designation root mean squared prediction error. The p-value counts the treated unit among the
ranks, so the smallest attainable value is 1/(donors + 1).
"""
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from scipy.optimize import nnls


# ---------------------------------------------------------------- synthetic control

def scm_weights(y1_pre, Y0_pre):
    """min ||y1 - Y0' w|| with w >= 0 and sum w = 1. Y0_pre is donors-by-periods."""
    scale = max(np.abs(Y0_pre).max(), np.abs(y1_pre).max(), 1.0)
    M = 1e3 * scale * np.sqrt(len(y1_pre))
    A = np.vstack([Y0_pre.T, np.full(Y0_pre.shape[0], M)])
    b = np.concatenate([y1_pre, [M]])
    w, _ = nnls(A, b, maxiter=50 * A.shape[1])
    s = w.sum()
    if abs(s - 1) > 1e-6:
        raise RuntimeError(f"synthetic control weights sum to {s}")
    return w / s


def scm(Y, T0):
    w = scm_weights(Y[0, :T0], Y[1:, :T0])
    path = w @ Y[1:]
    return dict(weights=w, path=path, gap=Y[0] - path)


# ---------------------------------------------------------------- ridge augmented synthetic control

def _ridge_fit(X, Yp, lam):
    """Coefficients of a ridge regression of the columns of Yp on X (both centered by donor means)."""
    Xc = X - X.mean(0)
    k = X.shape[1]
    return np.linalg.solve(Xc.T @ Xc + lam * np.eye(k), Xc.T @ (Yp - Yp.mean(0)))


def _ascm_path(Y, T0, lam, w=None):
    y1, Y0 = Y[0], Y[1:]
    if w is None:
        w = scm_weights(y1[:T0], Y0[:, :T0])
    eta = _ridge_fit(Y0[:, :T0], Y0[:, T0:], lam)
    imbalance = y1[:T0] - w @ Y0[:, :T0]
    path = w @ Y0
    path[T0:] += imbalance @ eta
    # pre-designation path of the augmented weights: w_aug = w + (X0c (X0c'X0c + lam I)^-1 imbalance)
    Xc = Y0[:, :T0] - Y0[:, :T0].mean(0)
    w_aug = w + Xc @ np.linalg.solve(Xc.T @ Xc + lam * np.eye(T0), imbalance)
    path[:T0] = w_aug @ Y0[:, :T0]
    return path, w, w_aug


def choose_lambda(Y, T0, grid=None, holdout=None):
    """Rolling-origin cross-validation: for each of the last `holdout` pre-designation periods s, fit on the periods
    before s and predict s. Returns the largest lambda whose error is within one standard error of the minimum."""
    Y0pre = Y[1:, :T0]
    if grid is None:
        sv = np.linalg.svd(Y0pre - Y0pre.mean(0), compute_uv=False)
        top = sv[0] ** 2
        grid = top * np.logspace(-8, 1, 37)
    if holdout is None:
        holdout = max(1, min(5, T0 // 3))
    errs = np.zeros((len(grid), holdout))
    for j, s in enumerate(range(T0 - holdout, T0)):
        Ys = Y[:, : s + 1]
        w = scm_weights(Ys[0, :s], Ys[1:, :s])
        for i, lam in enumerate(grid):
            p, _, _ = _ascm_path(Ys, s, lam, w)
            errs[i, j] = (Ys[0, s] - p[s]) ** 2
    m = errs.mean(1)
    se = errs.std(1, ddof=1) / np.sqrt(holdout) if holdout > 1 else np.zeros(len(grid))
    best = int(np.argmin(m))
    ok = np.where(m <= m[best] + se[best])[0]
    return float(grid[ok.max()]), dict(grid=grid, cv_mse=m)


def ascm(Y, T0, lam=None):
    if lam is None:
        lam, _ = choose_lambda(Y, T0)
    path, w, w_aug = _ascm_path(Y, T0, lam)
    return dict(weights=w, weights_aug=w_aug, lam=lam, path=path, gap=Y[0] - path)


# ---------------------------------------------------------------- synthetic difference-in-differences

def _fw_simplex(A, b, zeta, w0=None, max_iter=10_000, min_decrease=1e-10):
    """Frank-Wolfe for min ||A w - b||^2 / n + zeta^2 ||w||^2 over the simplex, with A and b centered (intercept).
    The synthdid package's sc.weight.fw, with min_decrease given on the squared scale."""
    n, k = A.shape
    w = np.full(k, 1.0 / k) if w0 is None else w0.copy()
    eta = n * zeta ** 2
    Aw = A @ w
    vals = []
    for _ in range(max_iter):
        half_grad = A.T @ (Aw - b) + eta * w
        i = int(np.argmin(half_grad))
        d_x = -w.copy()
        d_x[i] += 1.0
        if np.all(d_x == 0):
            break
        d_err = A[:, i] - Aw
        step = -(half_grad @ d_x) / (d_err @ d_err + eta * (d_x @ d_x))
        step = min(1.0, max(0.0, step))
        w = w + step * d_x
        Aw = Aw + step * d_err
        vals.append(zeta ** 2 * (w @ w) + ((Aw - b) ** 2).sum() / n)
        if len(vals) > 1 and vals[-2] - vals[-1] <= min_decrease ** 2:
            break
    return w


def _sparsify(w):
    w = np.where(w <= w.max() / 4, 0.0, w)
    return w / w.sum()


def sdid_weights(Y, T0):
    """Unit weights omega (donors) and time weights lambda (pre-designation periods)."""
    Y0 = Y[1:]
    N0, T = Y0.shape
    T1 = T - T0
    sigma = np.diff(Y0[:, :T0], axis=1).std(ddof=1)
    zeta_omega = (1 * T1) ** 0.25 * sigma
    zeta_lambda = 1e-6 * sigma
    min_dec = 1e-5 * sigma

    # time weights: regress each donor's post mean on its pre-designation periods
    A = Y0[:, :T0]
    b = Y0[:, T0:].mean(1)
    A, b = A - A.mean(0), b - b.mean()
    lam = _fw_simplex(A, b, zeta_lambda, max_iter=100, min_decrease=min_dec)
    lam = _fw_simplex(A, b, zeta_lambda, w0=_sparsify(lam), max_iter=10_000, min_decrease=min_dec)

    # unit weights: regress the treated pre-designation path on donors' paths
    A = Y0[:, :T0].T
    b = Y[0, :T0]
    A, b = A - A.mean(0), b - b.mean()
    om = _fw_simplex(A, b, zeta_omega, max_iter=100, min_decrease=min_dec)
    om = _fw_simplex(A, b, zeta_omega, w0=_sparsify(om), max_iter=10_000, min_decrease=min_dec)
    return om, lam


def sdid(Y, T0):
    om, lam = sdid_weights(Y, T0)
    y1, Y0 = Y[0], Y[1:]
    T = Y.shape[1]
    tau = (y1[T0:].mean() - lam @ y1[:T0]) - om @ (Y0[:, T0:].mean(1) - Y0[:, :T0] @ lam)
    # synthetic path with the intercept that SDID allows: the weighted donor path shifted to the treated unit's
    # time-weighted pre-designation level
    base = om @ Y0
    shift = lam @ y1[:T0] - lam @ base[:T0]
    path = base + shift
    gap = y1 - path
    return dict(tau=float(tau), weights=om, time_weights=lam, path=path, gap=gap,
                post_gaps=gap[T0:], T=T)


# ---------------------------------------------------------------- shared

def residualize(Y, X):
    """Residuals of each period's outcome on the covariates (with an intercept) across all units."""
    if X is None or X.shape[1] == 0:
        return Y
    Xd = np.column_stack([np.ones(len(X)), (X - X.mean(0)) / X.std(0)])
    coef = np.linalg.lstsq(Xd, Y, rcond=None)[0]
    return Y - Xd @ coef + coef[0]


def summarise(gap, T0):
    pre = np.sqrt(np.mean(gap[:T0] ** 2))
    post = np.sqrt(np.mean(gap[T0:] ** 2))
    return dict(effect=float(gap[T0:].mean()), rmspe_pre=float(pre), rmspe_post=float(post),
                ratio=float(post / pre) if pre > 0 else np.inf)


METHODS = {"scm": scm, "ascm": ascm, "sdid": sdid}


def estimate(Y, T0, method, X=None, **kw):
    Yr = residualize(Y, X)
    out = METHODS[method](Yr, T0, **kw)
    s = summarise(out["gap"], T0)
    if method == "sdid":
        s["effect"] = out["tau"]
    out.update(s)
    return out


def _placebo_chunk(args):
    donors, Xd, T0, method, fixed, js = args
    n0 = donors.shape[0]
    out = []
    for j in js:
        order = np.r_[j, np.delete(np.arange(n0), j)]
        r = estimate(donors[order], T0, method, None if Xd is None else Xd[order], **fixed)
        out.append((r["effect"], r["ratio"]))
    return out


def placebo_ranks(Y, T0, method, X=None, fixed=None, n_jobs=1):
    """Effect and RMSPE ratio for the treated unit and for each donor treated in turn.

    fixed carries settings to reuse in every placebo (for ascm, lam=...); by default every placebo chooses its own.
    n_jobs > 1 runs the placebos in that many processes. Returns the treated row, the placebo arrays, the rank p-value
    of the ratio, and the two-sided rank p-value of the effect."""
    fixed = fixed or {}
    real = estimate(Y, T0, method, X, **fixed)
    n0 = Y.shape[0] - 1
    donors = Y[1:]
    Xd = None if X is None else X[1:]
    chunks = [c for c in np.array_split(np.arange(n0), max(1, n_jobs) * 4) if len(c)]
    args = [(donors, Xd, T0, method, fixed, c) for c in chunks]
    if n_jobs > 1:
        with ProcessPoolExecutor(n_jobs) as ex:
            res = [r for part in ex.map(_placebo_chunk, args) for r in part]
    else:
        res = [r for a in args for r in _placebo_chunk(a)]
    eff, ratio = np.array(res).T
    p_ratio = (1 + np.sum(ratio >= real["ratio"])) / (n0 + 1)
    p_effect = (1 + np.sum(np.abs(eff) >= abs(real["effect"]))) / (n0 + 1)
    return dict(real=real, placebo_effect=eff, placebo_ratio=ratio, p_ratio=float(p_ratio),
                p_effect=float(p_effect))


def in_time_placebo(Y, T0, method, X=None, shift=5, **kw):
    """Designation moved `shift` periods earlier, using only periods before the true designation."""
    if T0 - shift < 3:
        raise ValueError("too few pre-designation periods for the in-time placebo")
    return placebo_ranks(Y[:, :T0], T0 - shift, method, X, **kw)
