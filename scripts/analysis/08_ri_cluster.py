"""Exploratory check, not in the registration: randomisation inference that permutes designation in province blocks.

python -I scripts/analysis/08_ri_cluster.py panel_dir [n_perm] [workers]

The registered permutation test (05_robust.py, part inference) reassigns designation years across districts of the same
economy one district at a time. Designation is not assigned that way. Districts of one province (cluster_id) are
designated together, so regional pollution shocks hit many designated districts at once, and a district-level
permutation averages those shocks out. The permutation spread is then too small and the test over-rejects.

This check keeps the province blocks. Within each economy the provinces are permuted, and the districts of province A
take the designation years of the districts of the matched province B, shuffled and repeated or cut to the size of A.
The share and timing of designation within a province travel together, as in the data.

Writes ri_cluster.csv in panel_dir (outcome, est, perm_sd, p, n_perm, note) and ri_cluster_draws.csv.
"""
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from importlib import import_module
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import did  # noqa: E402

mde = import_module("02_mde")
est3 = import_module("03_estimate")
OUTCOMES, COVARS, HEAD = mde.OUTCOMES, mde.COVARS, est3.HEAD
_G = {}


def _init(p):
    _G["p"] = p
    _G["first"] = p.drop_duplicates("unit_id").set_index("unit_id")


def _draw(seed):
    p, first = _G["p"], _G["first"]
    rng = np.random.default_rng(seed)
    perm = pd.Series(np.nan, index=first.index)
    for _, f in first.groupby("iso3"):
        blocks = {c: g.index.to_numpy() for c, g in f.groupby("cluster_id")}
        cohorts = {c: f.loc[ids, "cohort"].to_numpy() for c, ids in blocks.items()}
        names = list(blocks)
        for a, b in zip(names, rng.permutation(names)):
            perm[blocks[a]] = np.resize(rng.permutation(cohorts[b]), len(blocks[a]))
    q = p.assign(cohort=p["unit_id"].map(perm))
    return [did.point(q, did.Spec(y=y, covars=COVARS), HEAD) for y in OUTCOMES]


def main():
    if len(sys.argv) not in (2, 3, 4):
        sys.exit(__doc__)
    panel_dir = Path(sys.argv[1])
    n_perm = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    p = mde.load(panel_dir)
    p["cohort"] = p["first_treated"]
    obs = {y: did.point(p, did.Spec(y=y, covars=COVARS), HEAD) for y in OUTCOMES}
    for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[v] = "1"
    seeds = list(range(20261400, 20261400 + n_perm))
    with ProcessPoolExecutor(workers, initializer=_init, initargs=(p,)) as ex:
        draws = list(ex.map(_draw, seeds, chunksize=max(1, n_perm // (workers * 8))))
    D = pd.DataFrame(draws, columns=list(OUTCOMES))
    D.to_csv(panel_dir / "ri_cluster_draws.csv", index=False)
    rows = []
    for y in OUTCOMES:
        d = D[y].dropna().to_numpy()
        rows.append(dict(outcome=y, est=obs[y], perm_sd=float(d.std(ddof=1)),
                         p=(1 + (np.abs(d) >= abs(obs[y])).sum()) / (1 + len(d)), n_perm=len(d),
                         note="provinces permuted within economies, district years drawn from the matched province"))
    out = pd.DataFrame(rows)
    out.to_csv(panel_dir / "ri_cluster.csv", index=False)
    print(out.to_string())


if __name__ == "__main__":
    main()
