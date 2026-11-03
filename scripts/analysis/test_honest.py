"""Checks of honest.py on simulated event studies.

python -I scripts/analysis/test_honest.py

1. With Mbar = 0 the post-designation bias is zero, so the confidence set should be close to the usual interval
   l'beta_post +/- 1.96 se (the hybrid test is slightly wider by construction).
2. Size. With a linear differential trend, which lies in Delta^RM(1), the true theta of zero should be rejected in about
   5 percent of draws or fewer at Mbar = 1.
3. With a large effect and flat pre-designation coefficients the breakdown Mbar is positive and finite.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import honest  # noqa: E402

N_PRE, N_POST = 7, 6
rng = np.random.default_rng(1)
k = N_PRE + N_POST
Sigma = 0.02 ** 2 * 0.5 ** np.abs(np.subtract.outer(np.arange(k), np.arange(k)))
l = np.array([0.25, 0.2, 0.18, 0.15, 0.12, 0.1])
l = l / l.sum()

# 1
beta = np.concatenate([rng.normal(0, 0.005, N_PRE), np.full(N_POST, -0.03)])
cs = honest.confidence_set(beta, Sigma, l, N_PRE, 0.0)
se = np.sqrt(l @ Sigma[N_PRE:, N_PRE:] @ l)
usual = (l @ beta[N_PRE:] - 1.96 * se, l @ beta[N_PRE:] + 1.96 * se)
print("1. Mbar 0:", np.round([cs["lo"], cs["hi"]], 4), "usual:", np.round(usual, 4))
assert cs["lo"] < usual[0] + 0.1 * se and cs["hi"] > usual[1] - 0.1 * se
assert (cs["hi"] - cs["lo"]) < 1.35 * (usual[1] - usual[0])

# 2
e = np.concatenate([np.arange(-8, -1), np.arange(0, 6)])
delta = 0.01 * (e + 1)
comps = honest.components(Sigma, l, N_PRE, 1.0)
draws = rng.multivariate_normal(delta, Sigma, size=400)
rej = np.mean([not honest.in_set(comps, b, 0.0) for b in draws])
print(f"2. rejection rate of the true theta under a linear trend at Mbar 1: {rej:.3f}")
assert rej <= 0.07

# 3
beta = np.concatenate([rng.normal(0, 0.003, N_PRE), np.full(N_POST, -0.08)])
bd = honest.breakdown(beta, Sigma, l, N_PRE)
print(f"3. breakdown Mbar: {bd:.3f}")
assert 0 < bd < np.inf
for m in (0.5, 1.0):
    c = honest.confidence_set(beta, Sigma, l, N_PRE, m)
    print(f"   Mbar {m}: [{c['lo']:.4f}, {c['hi']:.4f}] one interval {c['one_interval']}")
print("all checks passed")
