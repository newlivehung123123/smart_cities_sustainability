"""Checks of synth.py on simulated factor-model panels only. No file in data/ is read.

python -I scripts/analysis/test_synth.py [reps]
"""
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import synth  # noqa: E402

REPS = int(sys.argv[1]) if len(sys.argv) > 1 else 100


def factor_panel(rng, n0=300, T0=17, T1=7, r=3, effect=0.0, sd=0.03, outside=False):
    """y_it = a_i + b_t + l_i'f_t + e_it, treated unit (row 0) with loadings inside the donors' range, or beyond the
    largest donor loading on every factor when outside is true (a city-state no donor mix can match)."""
    T = T0 + T1
    f = np.cumsum(rng.normal(0, 0.05, (T, r)), axis=0)
    L = rng.normal(0, 1, (n0 + 1, r))
    L[0] = L[1:].max(0) + 0.5 if outside else L[1:6].mean(0)
    a = rng.normal(3, 0.3, n0 + 1)
    x = rng.normal(0, 1, (n0 + 1, 1))  # a covariate with no effect unless a check adds one
    b = np.cumsum(rng.normal(0, 0.02, T))
    Y = a[:, None] + b[None, :] + L @ f.T + rng.normal(0, sd, (n0 + 1, T))
    Y[0, T0:] += effect
    return Y, T0, x


def check(name, ok, detail):
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}", flush=True)
    assert ok, name


def t_weights(rng):
    Y, T0, _ = factor_panel(rng)
    w = synth.scm_weights(Y[0, :T0], Y[1:, :T0])
    check("synthetic control weights on the simplex", w.min() >= 0 and abs(w.sum() - 1) < 1e-9,
          f"min {w.min():.1e}, sum {w.sum():.12f}, {np.sum(w > 1e-6)} donors used")
    # a treated unit that equals one donor exactly
    Y2 = Y.copy()
    Y2[0] = Y2[7]
    w2 = synth.scm_weights(Y2[0, :T0], Y2[1:, :T0])
    check("an exact copy of a donor gets that donor", w2[6] > 0.99, f"weight {w2[6]:.4f}")


def t_recovery(rng):
    out = {m: [] for m in synth.METHODS}
    for _ in range(REPS):
        Y, T0, _ = factor_panel(rng, effect=-0.10)
        for m in synth.METHODS:
            out[m].append(synth.estimate(Y, T0, m)["effect"])
    for m, v in out.items():
        v = np.array(v)
        check(f"{m} recovers a -0.10 effect", abs(v.mean() + 0.10) < 0.02,
              f"mean {v.mean():+.4f}, sd {v.std():.4f} over {REPS} panels")


def t_outside(rng):
    """Treated unit outside the donors' range: the ridge correction should cut the bias of the synthetic control."""
    b = {m: [] for m in synth.METHODS}
    for _ in range(max(REPS // 2, 20)):
        Y, T0, _ = factor_panel(rng, effect=0.0, outside=True)
        for m in synth.METHODS:
            b[m].append(synth.estimate(Y, T0, m)["effect"])
    mae = {m: np.mean(np.abs(v)) for m, v in b.items()}
    check("ridge augmentation reduces bias outside the donors' range", mae["ascm"] < mae["scm"],
          ", ".join(f"{m} mean |error| {v:.4f}" for m, v in mae.items()))


def t_covariate(rng):
    """A covariate with no effect before designation and a growing one after: matching on the pre-period cannot see
    it, so the raw estimate is biased and residualising on it removes the bias."""
    b_raw, b_res = [], []
    for _ in range(max(REPS // 2, 30)):
        Y, T0, x = factor_panel(rng, effect=0.0)
        x[0] = 2.0                               # treated unit far from donors on x
        ramp = np.clip((np.arange(Y.shape[1]) - T0 + 1) / (Y.shape[1] - T0), 0, 1)
        Y = Y + 0.3 * x * ramp[None, :]
        b_raw.append(synth.estimate(Y, T0, "sdid")["effect"])
        b_res.append(synth.estimate(Y, T0, "sdid", X=x)["effect"])
    raw, res = np.mean(b_raw), np.mean(b_res)
    check("residualising on covariates", abs(raw) > 0.1 and abs(res) < abs(raw) / 10,
          f"mean effect without {raw:+.4f}, with {res:+.4f} (true 0)")


def t_placebo(rng):
    n0 = 99
    Y, T0, _ = factor_panel(rng, n0=n0, effect=-0.25)
    t0 = time.time()
    res = {m: synth.placebo_ranks(Y, T0, m) for m in synth.METHODS}
    for m, r in res.items():
        check(f"{m} placebo rank finds a large effect", r["p_ratio"] <= 0.02,
              f"p {r['p_ratio']:.3f} (smallest possible {1 / (n0 + 1):.3f})")
    print(f"      three placebo runs on {n0} donors took {time.time() - t0:.1f} s", flush=True)
    par = synth.placebo_ranks(Y, T0, "ascm", n_jobs=4)
    check("placebos in four processes equal the serial run",
          np.allclose(par["placebo_effect"], res["ascm"]["placebo_effect"]) and par["p_ratio"] == res["ascm"]["p_ratio"],
          f"largest difference {np.abs(par['placebo_effect'] - res['ascm']['placebo_effect']).max():.1e}")
    # under no effect the rank p-value should be roughly uniform
    ps = []
    for _ in range(max(REPS // 5, 20)):
        Y, T0, _ = factor_panel(rng, n0=49, effect=0.0)
        ps.append(synth.placebo_ranks(Y, T0, "sdid")["p_ratio"])
    ps = np.array(ps)
    check("sdid placebo p-values under no effect", 0.3 < ps.mean() < 0.7 and np.mean(ps <= 0.05) <= 0.2,
          f"mean p {ps.mean():.2f}, share at or below 0.05 {np.mean(ps <= 0.05):.2f} over {len(ps)} panels")


def t_in_time(rng):
    Y, T0, _ = factor_panel(rng, n0=99, effect=-0.25)
    r = synth.in_time_placebo(Y, T0, "sdid")
    check("in-time placebo finds no effect before designation", abs(r["real"]["effect"]) < 0.06,
          f"effect {r['real']['effect']:+.4f}, p {r['p_ratio']:.2f}")


def t_lambda(rng):
    Y, T0, _ = factor_panel(rng)
    lam, cv = synth.choose_lambda(Y, T0)
    check("ridge penalty chosen inside its grid", cv["grid"].min() <= lam <= cv["grid"].max(), f"lambda {lam:.3g}")


def main():
    rng = np.random.default_rng(2)
    t0 = time.time()
    t_weights(rng)
    t_lambda(rng)
    t_recovery(rng)
    t_outside(rng)
    t_covariate(rng)
    t_in_time(rng)
    t_placebo(rng)
    print(f"all checks passed in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
