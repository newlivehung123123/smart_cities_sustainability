"""Sensitivity of the headline effect to violations of parallel trends (Rambachan and Roth 2023), registration Q19.

Event-study coefficients beta = (pre, post), with the year before designation as the reference (set to zero). beta =
delta + tau, where delta is the bias from differential trends and tau_pre = 0. The target is theta = l'tau_post.

Relative magnitudes. Delta^RM(Mbar) holds every delta whose largest change between consecutive years after designation is
at most Mbar times the largest change between consecutive years before designation. Delta^RM(Mbar) is the union over the
pre-designation change s and its sign of the polyhedra {delta : |post change t| <= Mbar * sign * (pre change s) for all
t}, so the confidence set is the union of one confidence set per polyhedron (Rambachan and Roth 2023, section 4).

Each polyhedron is tested with the conditional-least-favourable hybrid of Andrews, Roth and Pakes (2023) with kappa =
alpha / 10, the test Rambachan and Roth recommend for Delta^RM. The linear programme of the test statistic is solved
exactly by enumerating the vertices of its dual feasible set, which also gives the truncation points of the conditional
test in closed form.
"""
import itertools

import numpy as np
from scipy import stats

ALPHA = 0.05
N_SIM = 5000


def rm_components(n_pre, n_post, mbar):
    """Constraint matrices A (A delta <= 0) of the polyhedra whose union is Delta^RM(mbar). delta lists the pre years
    from the earliest to two years before designation, then the post years from the designation year."""
    full = n_pre + 1 + n_post

    def change(i):
        r = np.zeros(full)
        r[i + 1], r[i] = 1.0, -1.0
        return np.delete(r, n_pre)

    pre = [change(i) for i in range(n_pre)]
    post = [change(i) for i in range(n_pre, n_pre + n_post)]
    if mbar == 0:
        return [np.vstack([np.vstack([c, -c]) for c in post])]
    comps = []
    for s, sign in itertools.product(range(n_pre), (1.0, -1.0)):
        rows = []
        for c in post:
            rows += [c - mbar * sign * pre[s], -c - mbar * sign * pre[s]]
        comps.append(np.vstack(rows))
    return comps


def _vertices(E, b, tol=1e-9):
    """Vertices of {g >= 0 : E g = b}."""
    # keep a set of independent rows, the normalisation row first
    keep = []
    for i in range(E.shape[0]):
        if np.linalg.matrix_rank(E[keep + [i]], tol=1e-10) > len(keep):
            keep.append(i)
    E, b = E[keep], b[keep]
    r, m = E.shape
    subsets = np.array(list(itertools.combinations(range(m), r)))
    EB = E[:, subsets].transpose(1, 0, 2)                     # (n_subsets, r, r)
    good = np.abs(np.linalg.det(EB)) > 1e-12
    sol = np.linalg.solve(EB[good], np.broadcast_to(b, (good.sum(), r))[..., None])[..., 0]
    feas = (sol >= -tol).all(1)
    V = np.zeros((feas.sum(), m))
    rows = np.arange(feas.sum())[:, None]
    V[rows, subsets[good][feas]] = np.clip(sol[feas], 0, None)
    V = V[np.abs(V @ E.T - b).max(1) < 1e-7]
    return np.unique(np.round(V, 12), axis=0)


class Component:
    """One polyhedron A delta <= 0 with the parts of the test that do not depend on the hypothesised theta."""

    def __init__(self, A, Sigma, l, n_pre, alpha=ALPHA, n_sim=N_SIM, seed=20261103):
        self.alpha, self.kappa = alpha, alpha / 10
        n_post = len(l)
        Gam = np.eye(n_post)
        Gam[0] = l                                     # first row l, then unit vectors (l[0] > 0)
        Gi = np.linalg.inv(Gam)
        Ap = A[:, n_pre:]
        self.A, self.a, Xt = A, Ap @ Gi[:, 0], Ap @ Gi[:, 1:]
        self.SY = A @ Sigma @ A.T
        self.sd = np.sqrt(np.diag(self.SY))
        E = np.vstack([self.sd, Xt.T])
        b = np.zeros(E.shape[0])
        b[0] = 1.0
        self.V = _vertices(E, b)
        if len(self.V):
            rng = np.random.default_rng(seed)
            xi = rng.multivariate_normal(np.zeros(len(self.sd)), self.SY, size=n_sim, method="eigh")
            self.c_lf = float(np.quantile((xi @ self.V.T).max(1), 1 - self.kappa))

    def rejects(self, beta, theta):
        """True when the hybrid test rejects theta at level alpha."""
        if not len(self.V):
            return False                               # dual infeasible: the statistic is minus infinity
        Y = self.A @ beta - self.a * theta
        vals = self.V @ Y
        k = int(np.argmax(vals))
        eta, g = vals[k], self.V[k]
        if eta > self.c_lf:
            return True
        s2 = float(g @ self.SY @ g)
        if s2 <= 1e-12 * float(self.sd @ self.sd):
            return False                               # the maximising vertex has no variance (paired rows +c and -c
                                                       # when Mbar = 0), so eta = 0, the smallest value it can take
        c = self.SY @ g / s2
        z = Y - c * eta
        av, bv = self.V @ z, self.V @ c
        lo = av[bv < 1 - 1e-12] / (1 - bv[bv < 1 - 1e-12])
        up = av[bv > 1 + 1e-12] / (1 - bv[bv > 1 + 1e-12])
        vlo = lo.max() if len(lo) else -np.inf
        vup = min(up.min() if len(up) else np.inf, self.c_lf)
        sd = np.sqrt(s2)
        if vup <= vlo:
            return False
        level = (self.alpha - self.kappa) / (1 - self.kappa)
        F = stats.truncnorm.cdf(eta / sd, vlo / sd, vup / sd)
        return bool(F > 1 - level)


def components(beta_cov, l, n_pre, mbar, **kw):
    Sigma = beta_cov
    return [Component(A, Sigma, l, n_pre, **kw) for A in rm_components(n_pre, len(l), mbar)]


def in_set(comps, beta, theta):
    return any(not c.rejects(beta, theta) for c in comps)


def confidence_set(beta, Sigma, l, n_pre, mbar, n_grid=241, refine=14, **kw):
    """Lower and upper ends of the confidence set for theta (the hull of the union over polyhedra), and whether the
    accepted values form one interval on the grid."""
    comps = components(Sigma, l, n_pre, mbar, **kw)
    post = beta[n_pre:]
    centre = float(l @ post)
    se = float(np.sqrt(l @ Sigma[n_pre:, n_pre:] @ l))
    pre_full = np.concatenate([beta[:n_pre], [0.0]])
    maxdiff = float(np.abs(np.diff(pre_full)).max())
    width = 6 * se + 2 * mbar * maxdiff * float(l @ np.arange(1, len(l) + 1))
    for _ in range(6):
        grid = np.linspace(centre - width, centre + width, n_grid)
        acc = np.array([in_set(comps, beta, th) for th in grid])
        if not acc.any():
            return dict(lo=np.nan, hi=np.nan, empty=True, one_interval=True)
        if acc[0] or acc[-1]:
            width *= 2
            continue
        break
    i, j = np.flatnonzero(acc)[[0, -1]]

    def edge(a, r):                                    # a accepted, r rejected
        for _ in range(refine):
            m = (a + r) / 2
            if in_set(comps, beta, m):
                a = m
            else:
                r = m
        return a

    lo, hi = edge(grid[i], grid[i - 1]), edge(grid[j], grid[j + 1])
    one = bool(acc[i:j + 1].all())
    return dict(lo=lo, hi=hi, empty=False, one_interval=one)


def breakdown(beta, Sigma, l, n_pre, theta0=0.0, m_max=20.0, steps=16, **kw):
    """Largest Mbar at which theta0 stays outside the confidence set. NaN when theta0 is inside at Mbar = 0."""
    if in_set(components(Sigma, l, n_pre, 0.0, **kw), beta, theta0):
        return np.nan
    hi = 0.25
    while not in_set(components(Sigma, l, n_pre, hi, **kw), beta, theta0):
        hi *= 2
        if hi > m_max:
            return np.inf
    lo = hi / 2 if hi > 0.25 else 0.0
    for _ in range(steps):
        m = (lo + hi) / 2
        if in_set(components(Sigma, l, n_pre, m, **kw), beta, theta0):
            hi = m
        else:
            lo = m
    return lo
